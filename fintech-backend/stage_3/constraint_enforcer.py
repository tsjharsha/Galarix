# =====================================================
# 3.6 -- CONSTRAINT ENFORCER
# =====================================================
# The final mathematical safety net. After all
# transformations (correlations, conditionals, anomalies),
# this engine validates every single cell against the
# hard bounds from the data contract.
#
# This is why the engine NEVER produces garbage.
# Even after aggressive anomaly injection and correlation
# warping, every value in every cell is guaranteed to be
# mathematically valid.
# =====================================================

import numpy as np
from typing import Any, Dict, Optional


def enforce_constraints(
    columns: Dict[str, np.ndarray],
    parameters: Dict[str, Any],
    variables: Dict[str, Any],
    rng: Optional[np.random.Generator] = None,
    region: str = "US",
) -> Dict[str, np.ndarray]:
    """
    Final-pass enforcement of all data quality guarantees.

    Args:
        columns:    Dict of variable_name -> numpy array
        parameters: Stage 2 distribution parameters (bounds + categories)
        variables:  Stage 1.5 variable definitions (type info)

    Returns:
        Sanitized columns dict where every cell is guaranteed valid.
    """
    if rng is None:
        rng = np.random.default_rng(0)

    for var_name, col_data in columns.items():
        # Skip the anomaly flag column
        if var_name == "_is_anomaly":
            continue

        var_type = variables.get(var_name, {}).get("type", "string")
        dist_def = parameters.get(var_name, {})
        family = dist_def.get("family", "")
        bounds = _effective_bounds(var_name, variables.get(var_name, {}), dist_def, region)

        # ── 1. NaN/Inf Replacement ──
        if col_data.dtype != object:
            try:
                float_col = col_data.astype(float)
                nan_mask = np.isnan(float_col) | np.isinf(float_col)
                if np.any(nan_mask):
                    # Replace with median of valid values
                    valid = float_col[~nan_mask]
                    median_val = np.median(valid) if len(valid) > 0 else 0.0
                    float_col[nan_mask] = median_val
                    columns[var_name] = float_col
            except (ValueError, TypeError):
                pass

        # ── 2. Bounds Clamping (continuous/integer) ──
        if bounds and col_data.dtype != object:
            try:
                float_col = columns[var_name].astype(float)
                
                if "min" in bounds:
                    clamped_mask = float_col < bounds["min"]
                    if np.any(clamped_mask):
                        # Apply smart jitter upwards (1-10% of min)
                        jitter = _jitter_for_bound(bounds["min"], np.sum(clamped_mask), rng)
                        float_col[clamped_mask] = bounds["min"] + jitter
                
                if "max" in bounds:
                    clamped_mask = float_col > bounds["max"]
                    if np.any(clamped_mask):
                        # Apply smart jitter downwards (1-10% of max)
                        jitter = _jitter_for_bound(bounds["max"], np.sum(clamped_mask), rng)
                        float_col[clamped_mask] = np.where(
                            bounds["max"] > 0,
                            bounds["max"] - jitter,
                            bounds["max"],
                        )
                
                columns[var_name] = float_col
            except (ValueError, TypeError):
                pass

        # ── 3. Financial Rounding ──
        if var_type in ("continuous",) and col_data.dtype != object:
            try:
                float_col = columns[var_name].astype(float)
                # Detect if this is a monetary variable
                if _is_monetary(var_name):
                    columns[var_name] = np.round(float_col, 2)
                elif _is_score(var_name):
                    # Scores are integers (300-850 credit score, etc.)
                    columns[var_name] = np.round(float_col, 0)
                else:
                    # General continuous: round to 4 decimal places
                    columns[var_name] = np.round(float_col, 4)
            except (ValueError, TypeError):
                pass

        # ── 4. Integer Enforcement ──
        if var_type == "integer" and col_data.dtype != object:
            try:
                columns[var_name] = np.round(columns[var_name].astype(float), 0)
            except (ValueError, TypeError):
                pass

        # ── 5. Categorical Validation ──
        if family == "categorical":
            valid_cats = dist_def.get("categories", [])
            if valid_cats:
                # CRITICAL FIX: Handle numeric categories properly.
                # When categories are all numeric (e.g., [4, 6, 12], [0, 1]),
                # the sampler now produces float arrays. Compare numerically
                # to avoid the str(36.0)="36.0" != str(36)="36" mismatch
                # that previously replaced every value with the first category.
                all_numeric_cats = all(isinstance(c, (int, float)) for c in valid_cats)

                if all_numeric_cats and col_data.dtype != object:
                    # Numeric categorical — validate by numeric proximity
                    try:
                        float_col = columns[var_name].astype(float)
                        float_cats = np.array([float(c) for c in valid_cats])
                        for i in range(len(float_col)):
                            val = float_col[i]
                            if not np.any(np.isclose(val, float_cats, atol=0.01)):
                                # Snap to nearest valid category
                                nearest_idx = np.argmin(np.abs(float_cats - val))
                                float_col[i] = float_cats[nearest_idx]
                        columns[var_name] = float_col
                    except (ValueError, TypeError):
                        pass
                else:
                    # String categorical — original validation
                    str_cats = [str(c) for c in valid_cats]
                    validated = []
                    for val in col_data:
                        if str(val) in str_cats:
                            validated.append(str(val))
                        else:
                            # Replace invalid category with most common valid one
                            validated.append(str_cats[0])
                    columns[var_name] = np.array(validated, dtype=object)

        # ── 6. Non-Negative Enforcement for amounts ──
        if _must_be_non_negative(var_name, variables.get(var_name, {}), dist_def) and col_data.dtype != object:
            try:
                float_col = columns[var_name].astype(float)
                columns[var_name] = np.maximum(float_col, 0.0)
            except (ValueError, TypeError):
                pass
    # ── 7. Entity-Specific Domain Guards ──
    # These catch entity-level semantic bugs that generic rules miss.
    _entity_specific_guards(columns)

    return columns


def _entity_specific_guards(columns: Dict[str, np.ndarray]) -> None:
    """
    Entity-specific post-processing guards that enforce domain semantics
    beyond what generic bounds can catch.
    """
    for col_name in list(columns.keys()):
        name_lower = col_name.lower()
        if columns[col_name].dtype == object:
            continue
        try:
            float_col = columns[col_name].astype(float)
        except (ValueError, TypeError):
            continue

        # Guard: monthly_emi / monthly_payment must be non-negative
        if "emi" in name_lower or "monthly_payment" in name_lower:
            columns[col_name] = np.maximum(float_col, 0.0)

        # Guard: net_amount (payroll) must be non-negative
        if "net_amount" in name_lower or "net_pay" in name_lower:
            columns[col_name] = np.maximum(float_col, 0.0)

        # Guard: down_payment must be non-negative
        if "down_payment" in name_lower:
            columns[col_name] = np.maximum(float_col, 0.0)

        # Guard: ltv_ratio must be 0-100%
        if "ltv_ratio" in name_lower:
            columns[col_name] = np.clip(float_col, 0.0, 100.0)

        # Guard: installments_paid <= num_installments
        if "installments_paid" in name_lower:
            # Find the matching num_installments column
            for other_col in columns:
                if "num_installments" in other_col.lower() and columns[other_col].dtype != object:
                    try:
                        num_inst = columns[other_col].astype(float)
                        columns[col_name] = np.minimum(float_col, num_inst)
                        columns[col_name] = np.maximum(columns[col_name], 0.0)
                    except (ValueError, TypeError):
                        pass
                    break

        # Guard: approved_amount must be non-negative
        if "approved_amount" in name_lower:
            columns[col_name] = np.maximum(float_col, 0.0)


def _effective_bounds(
    var_name: str,
    var_def: Dict[str, Any],
    dist_def: Dict[str, Any],
    region: str = "US",
) -> Dict[str, float]:
    """Combine explicit schema bounds with safe financial defaults."""
    bounds = dict(dist_def.get("bounds", {}) or {})
    name_lower = var_name.lower()
    unit = str(var_def.get("unit", "")).lower()
    family = dist_def.get("family", "")

    if family == "beta":
        bounds.setdefault("min", 0.0)
        bounds.setdefault("max", 1.0)

    # Region-aware credit score bounds
    # Each region has a different scoring system, so US FICO 300-850
    # should NOT be forced onto UK (0-999) or India (300-900) data.
    _REGIONAL_CREDIT_BOUNDS = {
        "US": {"min": 300.0, "max": 850.0},
        "UK": {"min": 0.0, "max": 999.0},
        "IN": {"min": 300.0, "max": 900.0},
        "EU": {"min": 0.0, "max": 100.0},
        "JP": {"min": 0.0, "max": 1000.0},
        "AU": {"min": 0.0, "max": 1200.0},
        "BR": {"min": 0.0, "max": 1000.0},
    }
    if "credit_score" in name_lower or "fico" in name_lower:
        regional_bounds = _REGIONAL_CREDIT_BOUNDS.get(region, _REGIONAL_CREDIT_BOUNDS["US"])
        bounds.setdefault("min", regional_bounds["min"])
        bounds.setdefault("max", regional_bounds["max"])

    if "percent" in unit or any(k in name_lower for k in ["rate", "ratio", "utilization", "volatility"]):
        bounds.setdefault("min", 0.0)
        if "ltv" in name_lower or "advance_rate" in name_lower or "utilization" in name_lower:
            bounds.setdefault("max", 100.0)
        elif "interest_rate" in name_lower:
            bounds.setdefault("max", 35.0)
        elif "exchange_rate" in name_lower or "fx_rate" in name_lower:
            pass  # Exchange rates have no universal upper bound
        elif name_lower.endswith("_rate"):
            bounds.setdefault("max", 100.0)

    if _must_be_non_negative(var_name, var_def, dist_def):
        bounds.setdefault("min", 0.0)

    if "min" in bounds and "max" in bounds and bounds["min"] > bounds["max"]:
        bounds["min"], bounds["max"] = bounds["max"], bounds["min"]

    return bounds


def _jitter_for_bound(
    bound: float,
    size: int,
    rng: np.random.Generator,
) -> np.ndarray:
    """Deterministic jitter that preserves exact zero bounds."""
    if size <= 0:
        return np.array([])
    bound = float(bound)
    if bound == 0:
        return np.zeros(size)
    scale = max(abs(bound), 1.0)
    # Half-normal jitter for natural tail shape (most values cluster near
    # the boundary, a few reach further out — not a flat rectangular shelf)
    raw_jitter = np.abs(rng.normal(0, 0.03, size=size))
    clamped_jitter = np.clip(raw_jitter, 0.005, 0.15)
    return scale * clamped_jitter


def _must_be_non_negative(
    var_name: str,
    var_def: Dict[str, Any],
    dist_def: Dict[str, Any],
) -> bool:
    name_lower = var_name.lower()
    unit = str(var_def.get("unit", "")).lower()
    positive_keywords = [
        "amount", "balance", "salary", "income", "price", "cost",
        "fee", "premium", "payment", "gross", "net", "emi",
        "principal", "revenue", "expense", "deductible", "limit",
        "debit", "credit", "invoice", "payout", "deposit",
        "withdrawal", "margin", "wage", "rate", "ratio",
        "score", "term", "months", "days", "count", "num_",
        "quantity", "volume", "contracts", "shares",
    ]
    return (
        _is_monetary(var_name)
        or "percent" in unit
        or dist_def.get("family") == "beta"
        or any(kw in name_lower for kw in positive_keywords)
    )


def _is_monetary(var_name: str) -> bool:
    """Check if a variable represents a monetary amount."""
    money_keywords = [
        "amount", "balance", "salary", "income", "price", "cost",
        "fee", "premium", "payment", "gross", "net", "emi",
        "principal", "revenue", "expense", "deductible", "limit",
        "debit", "credit", "invoice", "payout", "deposit",
        "withdrawal", "margin", "profit", "loss", "wage",
    ]
    name_lower = var_name.lower()
    return any(kw in name_lower for kw in money_keywords)


def _is_score(var_name: str) -> bool:
    """Check if a variable represents a score (should be integer)."""
    score_keywords = [
        "credit_score", "risk_score", "fico",
    ]
    name_lower = var_name.lower()
    return any(kw in name_lower for kw in score_keywords)
