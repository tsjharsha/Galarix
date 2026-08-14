# =====================================================
# 3.4 -- CONDITIONAL EXECUTOR
# =====================================================
# Executes IF/THEN dependency rules and derived field
# formulas row by row after base generation.
#
# Three rule types from Stage 2:
#   1. Conditionals: IF field == value THEN target in [min, max]
#   2. Derived:      target = formula(field_a, field_b, ...)
#   3. Equals:       IF condition THEN target equals source_field
# =====================================================

import numpy as np
import math
from typing import Any, Dict, List, Optional


def execute_conditionals(
    columns: Dict[str, np.ndarray],
    dependencies: Dict[str, Any],
    entity: str = "",
    rng: Optional[np.random.Generator] = None,
) -> Dict[str, np.ndarray]:
    """
    Apply dependency rules to the generated columns.

    Args:
        columns:      Dict of variable_name -> numpy array
        dependencies: Stage 2 dependency spec:
                      {"conditionals": [...], "derived": [...], "correlations": [...]}
        entity:       Entity name for variable name prefix resolution

    Returns:
        Updated columns dict with dependencies applied.
    """
    conditionals = dependencies.get("conditionals", [])
    derived = dependencies.get("derived", [])
    if rng is None:
        rng = np.random.default_rng(0)

    # ── Execute conditionals ──
    for rule in conditionals:
        _apply_conditional(columns, rule, rule.get("source_entity", entity), rng)

    # ── Execute derived fields ──
    for formula_spec in derived:
        _apply_derived(columns, formula_spec, formula_spec.get("source_entity", entity))

    return columns


def _apply_conditional(
    columns: Dict[str, np.ndarray],
    rule: Dict[str, Any],
    entity: str,
    rng: np.random.Generator,
) -> None:
    """
    Apply a single conditional rule: IF condition THEN modification.

    Rule format from schema_registry:
        {"if": {"merchant_category": "Travel"}, "then": {"amount": {"min": 100, "max": 5000}}}
        {"if": {"status": "Completed"}, "then": {"installments_paid": {"equals": "num_installments"}}}
    """
    if_clause = rule.get("if", {})
    then_clause = rule.get("then", {})

    if not if_clause or not then_clause:
        return

    n_rows = _get_row_count(columns)
    if n_rows == 0:
        return

    # ── Build the condition mask ──
    mask = np.ones(n_rows, dtype=bool)

    for field_name, expected_value in if_clause.items():
        col_name = _resolve_column_name(field_name, columns, entity)
        if col_name is None:
            # Condition references a non-existent column -- skip rule
            return

        col_data = columns[col_name]

        if isinstance(expected_value, dict):
            mask &= _evaluate_condition(col_data, expected_value, columns, entity)
        else:
            # Simple equality: field == value
            if col_data.dtype == object:
                mask &= np.array([str(x) == str(expected_value) for x in col_data])
            else:
                mask &= (col_data == expected_value)

    if not np.any(mask):
        return

    # ── Apply the THEN clause to masked rows ──
    for target_field, modification in then_clause.items():
        target_col = _resolve_column_name(target_field, columns, entity)
        if target_col is None:
            continue

        if isinstance(modification, dict):
            if "equals" in modification:
                # Equals rule: target = value of another column
                source_field = modification["equals"]
                source_col = _resolve_column_name(source_field, columns, entity)
                if source_col is not None:
                    columns[target_col][mask] = columns[source_col][mask]

            elif "value" in modification:
                # Direct value assignment
                columns[target_col][mask] = modification["value"]

            elif "min" in modification or "max" in modification:
                # Range clamping with jitter to prevent artificial spikes
                if "min" in modification:
                    try:
                        col_as_float = columns[target_col].astype(float)
                        min_value = _resolve_dynamic_value(modification["min"], columns, entity)
                        clamped_mask = mask & (col_as_float < min_value)
                        if np.any(clamped_mask):
                            # Shift upwards dynamically rather than a hard flatline clamp
                            jitter = _jitter_for_bound(min_value, clamped_mask, rng)
                            col_as_float[clamped_mask] = min_value[clamped_mask] + jitter
                        columns[target_col] = col_as_float
                    except (ValueError, TypeError):
                        pass

                if "max" in modification:
                    try:
                        col_as_float = columns[target_col].astype(float)
                        max_value = _resolve_dynamic_value(modification["max"], columns, entity)
                        clamped_mask = mask & (col_as_float > max_value)
                        if np.any(clamped_mask):
                            jitter = _jitter_for_bound(max_value, clamped_mask, rng)
                            col_as_float[clamped_mask] = np.where(
                                max_value[clamped_mask] > 0,
                                max_value[clamped_mask] - jitter,
                                max_value[clamped_mask],
                            )
                        columns[target_col] = col_as_float
                    except (ValueError, TypeError):
                        pass

            elif "modifier" in modification:
                # Mathematical modifier
                mod_type = modification["modifier"]
                mod_value = modification.get("value", 1.0)
                try:
                    col_as_float = columns[target_col].astype(float)
                    if mod_type == "multiply":
                        col_as_float[mask] *= mod_value
                    elif mod_type == "add":
                        col_as_float[mask] += mod_value
                    columns[target_col] = col_as_float
                except (ValueError, TypeError):
                    pass
        else:
            # Direct value assignment (non-dict)
            columns[target_col][mask] = modification


def _apply_derived(
    columns: Dict[str, np.ndarray],
    formula_spec: Dict[str, Any],
    entity: str,
) -> None:
    """
    Apply a derived field formula.

    Format: {"target": "emi", "formula": "principal * rate / 1200"}

    HARDENED: Now includes a generic NaN/Inf guard for ALL derived
    formulas, not just EMI. Any division-by-zero or overflow in ANY
    formula is caught and replaced with 0.0.
    """
    target = formula_spec.get("target", "")
    formula = formula_spec.get("formula", "")
    source_entity = formula_spec.get("source_entity", entity)

    if not target or not formula:
        return

    target_col = _resolve_column_name(target, columns, source_entity)
    if target_col is None:
        # Fallback: try with the generic entity
        target_col = _resolve_column_name(target, columns, entity)
        if target_col is None:
            return

    n_rows = _get_row_count(columns)

    # Build a namespace with all columns available for formula evaluation
    # Use source_entity for proper alias scoping
    namespace = _build_formula_namespace(columns, source_entity)

    # Auto-Heal: Replace bitwise XOR with exponentiation to fix math bugs
    formula = formula.replace("^", "**")

    try:
        with np.errstate(divide="ignore", invalid="ignore", over="ignore"):
            result = eval(formula, {"__builtins__": {}}, namespace)
        result = _repair_formula_result(result, target_col, formula, namespace, n_rows)

        # ── GENERIC NaN/Inf GUARD ──
        # Catches ALL division-by-zero, overflow, and invalid math results
        # across every derived formula (ltv_ratio, net_payout, installment_amount, etc.)
        if isinstance(result, np.ndarray):
            try:
                result_float = result.astype(float)
                non_finite = ~np.isfinite(result_float)
                if np.any(non_finite):
                    result_float[non_finite] = 0.0
                result = result_float
            except (ValueError, TypeError):
                pass

        if isinstance(result, np.ndarray) and len(result) == n_rows:
            columns[target_col] = result
        elif np.isscalar(result):
            columns[target_col] = np.full(n_rows, result)
    except Exception:
        repaired = _known_financial_formula(target_col, formula, namespace, n_rows)
        if repaired is not None:
            columns[target_col] = repaired
        elif target_col in columns and columns[target_col].dtype == object:
            columns[target_col] = np.zeros(n_rows)


def _resolve_column_name(
    field_name: str,
    columns: Dict[str, np.ndarray],
    entity: str,
) -> str:
    """
    Resolve a field name from a dependency rule to an actual column name.
    Rules use short names (e.g., "amount") but columns are prefixed
    (e.g., "credit_card_activity_amount").
    """
    # Exact match first
    if field_name in columns:
        return field_name

    # Try with entity prefix
    prefixed = f"{entity}_{field_name}"
    if prefixed in columns:
        return prefixed

    # Try partial match (column ends with the field name)
    for col_name in columns:
        if col_name.endswith(f"_{field_name}"):
            return col_name

    return None


def _repair_formula_result(
    result: Any,
    target_col: str,
    formula: str,
    namespace: Dict[str, Any],
    n_rows: int,
) -> Any:
    """Replace non-finite formula cells with known financial edge-case values."""
    if not isinstance(result, np.ndarray):
        return result

    try:
        result_float = result.astype(float)
    except (ValueError, TypeError):
        return result

    non_finite = ~np.isfinite(result_float)
    if not np.any(non_finite):
        return result

    repaired = _known_financial_formula(target_col, formula, namespace, n_rows)
    if repaired is None:
        return result

    result_float[non_finite] = repaired[non_finite]
    return result_float


def _known_financial_formula(
    target_col: str,
    formula: str,
    namespace: Dict[str, Any],
    n_rows: int,
) -> Optional[np.ndarray]:
    """Handle financial formulas whose edge cases need explicit domain logic."""
    target_lower = target_col.lower()
    formula_lower = formula.lower()
    if ("emi" not in target_lower and "monthly_payment" not in target_lower) or "interest_rate/1200" not in formula_lower:
        return None

    principal = _namespace_value(namespace, "principal_amount", "loan_amount")
    rate = _namespace_value(namespace, "interest_rate")
    term = _namespace_value(namespace, "loan_term_months")

    if principal is None or rate is None:
        return None
    if term is None:
        term = np.full(n_rows, 360.0)

    try:
        principal = np.asarray(principal, dtype=float)
        rate = np.asarray(rate, dtype=float)
        term = np.asarray(term, dtype=float)
        monthly_rate = rate / 1200.0
        with np.errstate(divide="ignore", invalid="ignore", over="ignore"):
            payment = (
                principal
                * monthly_rate
                * np.power(1 + monthly_rate, term)
                / (np.power(1 + monthly_rate, term) - 1)
            )
        zero_rate = np.isclose(monthly_rate, 0.0)
        payment = np.where(zero_rate, principal / np.maximum(term, 1.0), payment)
        return payment
    except (ValueError, TypeError, FloatingPointError):
        return None


def _namespace_value(namespace: Dict[str, Any], *names: str) -> Optional[Any]:
    for name in names:
        if name in namespace:
            return namespace[name]
    return None


def _build_formula_namespace(
    columns: Dict[str, np.ndarray],
    source_entity: str,
) -> Dict[str, Any]:
    """
    Build a formula namespace that understands both fully qualified names and
    schema-local aliases. For example, loans_principal_amount becomes
    principal_amount inside formulas declared by the loans schema.

    HARDENED: Entity-local aliases now have PRIORITY over generic aliases.
    This prevents ambiguous cross-entity collisions in multi-entity schemas
    where e.g. both 'loans_interest_rate' and 'mortgage_records_interest_rate'
    would both create an 'interest_rate' alias.
    """
    namespace: Dict[str, Any] = {"math": math, "np": np}
    generic_aliases: Dict[str, Any] = {}
    entity_local_aliases: Dict[str, Any] = {}

    for col_name, col_data in columns.items():
        try:
            value = col_data.astype(float)
        except (ValueError, TypeError):
            value = col_data

        # Full qualified name always available
        namespace[col_name] = value

        # Entity-local aliases get PRIORITY
        if source_entity and col_name.startswith(f"{source_entity}_"):
            local_name = col_name[len(source_entity) + 1:]
            entity_local_aliases[local_name] = value

        # Generic suffix aliases (lower priority)
        parts = col_name.split("_")
        for i in range(1, len(parts)):
            alias = "_".join(parts[i:])
            generic_aliases.setdefault(alias, value)

    # Apply generic aliases first (lower priority)
    for alias, value in generic_aliases.items():
        namespace.setdefault(alias, value)

    # Then overwrite with entity-local aliases (HIGHER priority)
    for alias, value in entity_local_aliases.items():
        namespace[alias] = value

    return namespace


def _evaluate_condition(
    col_data: np.ndarray,
    spec: Dict[str, Any],
    columns: Dict[str, np.ndarray],
    entity: str,
) -> np.ndarray:
    """Evaluate condition dictionaries such as {"min": 0.8}."""
    if "operator" in spec:
        value = _resolve_dynamic_value(spec.get("value", 0), columns, entity)
        return _evaluate_operator(col_data, spec.get("operator", "=="), value)

    try:
        col_float = col_data.astype(float)
        mask = np.ones(len(col_float), dtype=bool)
        if "min" in spec:
            mask &= col_float >= _resolve_dynamic_value(spec["min"], columns, entity)
        if "max" in spec:
            mask &= col_float <= _resolve_dynamic_value(spec["max"], columns, entity)
        if "equals" in spec:
            mask &= col_float == _resolve_dynamic_value(spec["equals"], columns, entity)
        return mask
    except (ValueError, TypeError):
        if "equals" in spec:
            return np.array([str(x) == str(spec["equals"]) for x in col_data])
        return np.zeros(len(col_data), dtype=bool)


def _resolve_dynamic_value(
    value: Any,
    columns: Dict[str, np.ndarray],
    entity: str,
) -> np.ndarray:
    """Return an array for literals or referenced columns."""
    n_rows = _get_row_count(columns)
    if isinstance(value, str):
        source_col = _resolve_column_name(value, columns, entity)
        if source_col is not None:
            try:
                return columns[source_col].astype(float)
            except (ValueError, TypeError):
                return columns[source_col]
        try:
            return np.full(n_rows, float(value))
        except ValueError:
            return np.full(n_rows, value, dtype=object)

    return np.full(n_rows, value)


def _jitter_for_bound(
    bound_values: np.ndarray,
    mask: np.ndarray,
    rng: np.random.Generator,
) -> np.ndarray:
    """Generate deterministic smart jitter that collapses to zero at zero bounds."""
    selected = np.asarray(bound_values[mask], dtype=float)
    scale = np.maximum(np.abs(selected), 1.0)
    jitter = scale * rng.uniform(0.01, 0.15, size=len(selected))
    return np.where(selected == 0, 0.0, jitter)


def _evaluate_operator(
    col_data: np.ndarray,
    operator: str,
    value: Any,
) -> np.ndarray:
    """Evaluate a comparison operator on a column."""
    try:
        col_float = col_data.astype(float)
        if operator == "<":
            return col_float < value
        elif operator == "<=":
            return col_float <= value
        elif operator == ">":
            return col_float > value
        elif operator == ">=":
            return col_float >= value
        elif operator == "==":
            return col_float == value
        elif operator == "!=":
            return col_float != value
    except (ValueError, TypeError):
        pass

    # Fallback: string comparison
    return np.array([str(x) == str(value) for x in col_data])


def _get_row_count(columns: Dict[str, np.ndarray]) -> int:
    """Get the number of rows from any column."""
    for arr in columns.values():
        return len(arr)
    return 0
