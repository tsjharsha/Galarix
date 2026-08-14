# =====================================================
# GENERATION ORCHESTRATOR — Stage 3 Main Entry Point
# =====================================================
# Ties all 7 sub-engines together in the correct
# execution order to produce a complete, audited,
# downloadable synthetic dataset from a Stage 2
# statistical model.
#
# Pipeline:
#   Seed Engine -> Marginal Sampler -> Correlation Weaver
#   -> Conditional Executor -> Anomaly Injector
#   -> Constraint Enforcer -> Quality Auditor
#   -> Export Engine
#
# Every unique prompt produces unique data.
# Same prompt + same salt = identical data.
# Zero crashes. Zero nulls. Zero garbage.
# =====================================================

import time
import copy
import numpy as np
from typing import Any, Dict, Optional

from stage_3.seed_engine import create_generator
from stage_3.marginal_sampler import sample_all_marginals
from stage_3.correlation_weaver import weave_correlations
from stage_3.conditional_executor import execute_conditionals
from stage_3.anomaly_injector import inject_anomalies
from stage_3.constraint_enforcer import enforce_constraints
from stage_3.quality_auditor import audit_dataset
from stage_3.export_engine import columns_to_records, build_metadata_sidecar
from stage_3.string_generators import weave_semantic_strings

# ── Horizon 2: Temporal Engines ──
from stage_3.temporal_calendar_engine import generate_temporal_grid
from stage_3.temporal_regime_engine import simulate_regime_path
from stage_3.temporal_correlation_engine import apply_temporal_correlations, apply_trend, _clamp_series
from stage_3.temporal_anomaly_engine import inject_temporal_anomalies
from stage_3.temporal_consistency_auditor import audit_temporal_consistency

# ── Trust Engine ──
from trust_engine.trust_report_builder import build_trust_certificate
from stage_1_5.schema_registry import get_data_sources


def generate_dataset(
    statistical_model: Dict[str, Any],
    contract: Dict[str, Any],
    rows: int = 1000,
    variation_salt: int = 0,
) -> Dict[str, Any]:
    """
    The main generation function. Takes a Stage 2 statistical model
    and produces a complete synthetic dataset with quality audit.

    Args:
        statistical_model: Output from stage_2.model_builder.build_statistical_model()
        contract:          Enriched contract from stage_1_5.enrichment_engine.enrich_contract()
        rows:              Number of rows to generate (default 1000, max 1_000_000)
        variation_salt:    Integer salt for generating variations of the same prompt

    Returns:
        {
            "success": True,
            "entity": "credit_card_activity",
            "data": [...records...],       # List of dicts (row-oriented)
            "columns": [...],              # Column names in order
            "rows_generated": 1000,
            "columns_count": 14,
            "audit_report": {...},         # Full quality audit
            "metadata": {...},             # Provenance chain
            "generation_time_ms": 234.5,
            "tensor_signature": "ea88e300acac3964",
        }
    """
    start_time = time.perf_counter()

    try:
        # ── Extract inputs ──
        entity = statistical_model.get("entity", "generic")
        parameters = statistical_model.get("parameters", {})
        covariance = statistical_model.get("covariance", [])
        dependencies = statistical_model.get("dependencies", {})
        behavior = statistical_model.get("behavior_used", {})
        tensor_signature = behavior.get("tensor_signature", "0000000000000000")
        anomaly_rate = behavior.get("anomaly_rate", 0.05)
        variables = contract.get("variables", {})
        temporal_model = statistical_model.get("temporal")

        # Clamp rows to reasonable range
        rows = max(10, min(rows, 1_000_000))

        # ── Merge category names from contract into parameters ──
        # Stage 2 preserves weights but not category labels.
        # The labels live in the contract's variable definitions.
        parameters = _merge_categories_into_params(parameters, variables, behavior)

        # ══════════════════════════════════════════════
        # ENGINE 3.1: SEED
        # ══════════════════════════════════════════════
        rng = create_generator(tensor_signature, variation_salt)

        # ════════════════════════════════════════════════════════════════
        # ROUTING: TEMPORAL vs STATIC PATH
        # ════════════════════════════════════════════════════════════════
        if temporal_model and temporal_model.get("enabled"):
            # ═══════════════════════════════════════════
            #  HORIZON 2: TEMPORAL GENERATION PATH
            # ═══════════════════════════════════════════
            print(f"\n{'='*60}")
            print(f"⏱️  TEMPORAL PATH ACTIVE — {temporal_model.get('frequency')} × {temporal_model.get('periods')} periods")
            print(f"{'='*60}")

            region = contract.get("intent", {}).get("region", "US")

            # ══════════════════════════════════════════════
            # ENGINE 3.T1: CALENDAR GRID
            # ══════════════════════════════════════════════
            timestamps, time_index, calendar_meta = generate_temporal_grid(
                temporal_model, rows, rng, region,
            )
            n_actual = calendar_meta.get("n_actual", len(timestamps))
            rows = n_actual  # Adjust row count to match calendar

            # ══════════════════════════════════════════════
            # ENGINE 3.T2: REGIME PATH
            # ══════════════════════════════════════════════
            regime_labels, regime_multipliers, regime_indices = simulate_regime_path(
                temporal_model, n_actual, rng,
            )

            # ══════════════════════════════════════════════
            # ENGINE 3.2: MARGINAL SAMPLER (regime-aware)
            # ══════════════════════════════════════════════
            columns = sample_all_marginals(
                rng, parameters, variables, entity, n_actual,
                tensor_signature=tensor_signature,
                variation_salt=variation_salt,
                region=region,
            )

            # ══════════════════════════════════════════════
            # ENGINE 3.T3: TEMPORAL CORRELATION
            # (AR(1), GARCH, Ornstein-Uhlenbeck, GBM)
            # ══════════════════════════════════════════════
            seasonal_factors = calendar_meta.get("seasonal_factor", np.ones(n_actual))
            columns = apply_temporal_correlations(
                columns, temporal_model, regime_multipliers,
                seasonal_factors, rng,
            )

            # Apply trend component
            columns = apply_trend(columns, temporal_model, n_actual)

            # ══════════════════════════════════════════════
            # ENGINE 3.3: CROSS-VARIABLE CORRELATION
            # ══════════════════════════════════════════════
            columns = weave_correlations(columns, covariance, parameters)

            # ══════════════════════════════════════════════
            # ENGINE 3.4: CONDITIONAL EXECUTION
            # ══════════════════════════════════════════════
            columns = execute_conditionals(columns, dependencies, entity, rng)

            # ══════════════════════════════════════════════
            # ENGINE 3.4.5: SEMANTIC WEAVER
            # ══════════════════════════════════════════════
            columns = weave_semantic_strings(columns)

            # ══════════════════════════════════════════════
            # INJECT TEMPORAL TIMESTAMPS
            # Replace any datetime columns with calendar-grid timestamps
            # ══════════════════════════════════════════════
            for var_name, var_def in variables.items():
                if var_def.get("type") == "datetime" or "date" in var_name.lower() or "timestamp" in var_name.lower():
                    if var_name in columns:
                        columns[var_name] = timestamps[:n_actual]

            # ══════════════════════════════════════════════
            # ENGINE 3.T4: TEMPORAL ANOMALY INJECTION
            # ══════════════════════════════════════════════
            columns = inject_temporal_anomalies(
                columns, timestamps, regime_labels,
                regime_multipliers, calendar_meta,
                temporal_model, parameters, rng,
            )

            # Post-anomaly domain clamp — anomaly multipliers can push
            # values past realistic bounds (e.g., volume_spike × 10)
            for _vn, _vc in columns.items():
                if _vn.startswith("_") or _vc.dtype == object:
                    continue
                try:
                    columns[_vn] = _clamp_series(_vc.astype(float), _vn)
                except (ValueError, TypeError):
                    pass

            # ══════════════════════════════════════════════
            # ENGINE 3.6: CONSTRAINT ENFORCEMENT
            # ══════════════════════════════════════════════
            columns = enforce_constraints(columns, parameters, variables, rng, region)
            columns = execute_conditionals(
                columns,
                {"conditionals": [], "derived": dependencies.get("derived", [])},
                entity, rng,
            )
            columns = enforce_constraints(columns, parameters, variables, rng, region)

            # ══════════════════════════════════════════════
            # ENGINE 3.6.1: FINAL CONDITIONAL SEAL
            # ══════════════════════════════════════════════
            columns = execute_conditionals(columns, dependencies, entity, rng)
            columns = enforce_constraints(columns, parameters, variables, rng, region)

            # ══════════════════════════════════════════════
            # ZERO-VALUE SAFETY NET
            # For temporal data, zero-value prices/amounts are
            # invalid (e.g., buying 0 BTC at $0). Replace zeros
            # with small values drawn from the non-zero portion.
            # ══════════════════════════════════════════════
            _fix_zero_values(columns, variables, rng)

            # ══════════════════════════════════════════════
            # ADD REGIME METADATA COLUMNS
            # ══════════════════════════════════════════════
            columns["_regime"] = regime_labels[:n_actual]

            # ══════════════════════════════════════════════
            # ENGINE 3.T5: TEMPORAL CONSISTENCY AUDIT
            # ══════════════════════════════════════════════
            temporal_audit = audit_temporal_consistency(
                columns, temporal_model, regime_labels, calendar_meta,
            )

            # ══════════════════════════════════════════════
            # ENGINE 3.7: QUALITY AUDIT
            # ══════════════════════════════════════════════
            audit_report = audit_dataset(columns, parameters, covariance, anomaly_rate)
            audit_report["temporal"] = temporal_audit

            # ══════════════════════════════════════════════
            # ENGINE 3.8: TRUST CERTIFICATE
            # ══════════════════════════════════════════════
            t_region = contract.get("intent", {}).get("region", "US")
            trust_certificate = build_trust_certificate(
                columns, parameters, covariance, dependencies,
                entity, t_region,
                get_data_sources(entity), audit_report,
            )

        else:
            # ═══════════════════════════════════════════
            #  HORIZON 1: STATIC GENERATION PATH (unchanged)
            # ═══════════════════════════════════════════

            region = contract.get("intent", {}).get("region", "US")

            # ══════════════════════════════════════════════
            # ENGINE 3.2: MARGINAL SAMPLER
            # ══════════════════════════════════════════════
            columns = sample_all_marginals(
                rng, parameters, variables, entity, rows,
                tensor_signature=tensor_signature,
                variation_salt=variation_salt,
                region=region,
            )

            # ══════════════════════════════════════════════
            # ENGINE 3.3: CORRELATION WEAVING
            # ══════════════════════════════════════════════
            columns = weave_correlations(columns, covariance, parameters)

            # ══════════════════════════════════════════════
            # ENGINE 3.4: CONDITIONAL EXECUTION
            # ══════════════════════════════════════════════
            columns = execute_conditionals(columns, dependencies, entity, rng)

            # ══════════════════════════════════════════════
            # ENGINE 3.4.5: SEMANTIC WEAVER
            # ══════════════════════════════════════════════
            columns = weave_semantic_strings(columns)

            # ══════════════════════════════════════════════
            # ENGINE 3.5: ANOMALY INJECTION
            # ══════════════════════════════════════════════
            columns = inject_anomalies(columns, parameters, anomaly_rate, rng)

            # ══════════════════════════════════════════════
            # ENGINE 3.6: CONSTRAINT ENFORCEMENT
            # ══════════════════════════════════════════════
            columns = enforce_constraints(columns, parameters, variables, rng, region)
            columns = execute_conditionals(
                columns,
                {"conditionals": [], "derived": dependencies.get("derived", [])},
                entity, rng,
            )
            columns = enforce_constraints(columns, parameters, variables, rng, region)

            # ══════════════════════════════════════════════
            # ENGINE 3.6.1: FINAL CONDITIONAL SEAL
            # ══════════════════════════════════════════════
            columns = execute_conditionals(columns, dependencies, entity, rng)

            # ══════════════════════════════════════════════
            # ENGINE 3.6.2: ABSOLUTE FINAL CONSTRAINT SEAL
            # ══════════════════════════════════════════════
            columns = enforce_constraints(columns, parameters, variables, rng, region)

            # ══════════════════════════════════════════════
            # ENGINE 3.7: QUALITY AUDIT
            # ══════════════════════════════════════════════
            audit_report = audit_dataset(columns, parameters, covariance, anomaly_rate)

            # ══════════════════════════════════════════════
            # ENGINE 3.8: TRUST CERTIFICATE
            # ══════════════════════════════════════════════
            trust_certificate = build_trust_certificate(
                columns, parameters, covariance, dependencies,
                entity, region,
                get_data_sources(entity), audit_report,
            )

        # ══════════════════════════════════════════════
        # BUILD OUTPUT
        # ══════════════════════════════════════════════
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        records = columns_to_records(columns)
        col_names = sorted(columns.keys())

        metadata = build_metadata_sidecar(
            entity=entity,
            tensor_signature=tensor_signature,
            n_rows=rows,
            n_cols=len(col_names),
            generation_time_ms=elapsed_ms,
            audit_report=audit_report,
            variation_salt=variation_salt,
        )

        # Add temporal metadata if applicable
        if temporal_model and temporal_model.get("enabled"):
            metadata["temporal"] = {
                "mode": "temporal",
                "frequency": temporal_model.get("frequency"),
                "periods": temporal_model.get("periods"),
                "pattern": temporal_model.get("temporal_pattern"),
                "regime_hint": temporal_model.get("regime_hint"),
            }

        return {
            "success": True,
            "entity": entity,
            "data": records,
            "columns": col_names,
            "rows_generated": len(records),
            "columns_count": len(col_names),
            "audit_report": audit_report,
            "trust_certificate": trust_certificate,
            "metadata": metadata,
            "generation_time_ms": round(elapsed_ms, 2),
            "tensor_signature": tensor_signature,
        }

    except Exception as e:
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "entity": statistical_model.get("entity", "unknown"),
            "error": str(e),
            "data": [],
            "columns": [],
            "rows_generated": 0,
            "columns_count": 0,
            "audit_report": {},
            "metadata": {},
            "generation_time_ms": round(elapsed_ms, 2),
            "tensor_signature": "",
        }


def generate_preview(
    statistical_model: Dict[str, Any],
    contract: Dict[str, Any],
    preview_rows: int = 10,
) -> Dict[str, Any]:
    """
    Generate a small preview (10-50 rows) for SSE streaming.
    Faster than full generation — skips quality audit.
    """
    start_time = time.perf_counter()

    try:
        entity = statistical_model.get("entity", "generic")
        parameters = statistical_model.get("parameters", {})
        covariance = statistical_model.get("covariance", [])
        dependencies = statistical_model.get("dependencies", {})
        behavior = statistical_model.get("behavior_used", {})
        tensor_signature = behavior.get("tensor_signature", "0000000000000000")
        anomaly_rate = behavior.get("anomaly_rate", 0.05)
        variables = contract.get("variables", {})

        preview_rows = max(5, min(preview_rows, 50))
        parameters = _merge_categories_into_params(parameters, variables, behavior)

        region = contract.get("intent", {}).get("region", "US")
        rng = create_generator(tensor_signature, 0)
        columns = sample_all_marginals(
            rng,
            parameters,
            variables,
            entity,
            preview_rows,
            tensor_signature=tensor_signature,
            variation_salt=0,
            region=region,
        )
        columns = weave_correlations(columns, covariance, parameters)
        columns = execute_conditionals(columns, dependencies, entity, rng)
        columns = weave_semantic_strings(columns)
        # Skip anomaly injection for preview (too small a sample)
        columns["_is_anomaly"] = np.zeros(preview_rows, dtype=bool)
        columns = enforce_constraints(columns, parameters, variables, rng, region)
        columns = execute_conditionals(
            columns,
            {"conditionals": [], "derived": dependencies.get("derived", [])},
            entity,
            rng,
        )
        columns = enforce_constraints(columns, parameters, variables, rng, region)

        records = columns_to_records(columns)
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        return {
            "success": True,
            "entity": entity,
            "preview_data": records,
            "columns": sorted(columns.keys()),
            "preview_rows": len(records),
            "generation_time_ms": round(elapsed_ms, 2),
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "preview_data": [],
            "columns": [],
            "preview_rows": 0,
        }


def _merge_categories_into_params(
    parameters: Dict[str, Any],
    variables: Dict[str, Any],
    behavior: Dict[str, Any] = None,
) -> Dict[str, Any]:
    """
    Merge category labels from the contract's variable definitions
    into the Stage 2 parameter definitions.

    Stage 2 preserves weights but strips category labels.
    The labels (e.g., ["Retail", "Food", "Travel"]) are in
    the contract's variables dict.
    """
    merged = {}
    
    # First, copy existing parameters and merge category labels
    for var_name, dist_def in parameters.items():
        merged[var_name] = copy.deepcopy(dist_def)  # CRIT-1 FIX: Deepcopy to prevent parameter corruption

        if dist_def.get("family") == "categorical":
            # Pull categories from the variable definition
            var_def = variables.get(var_name, {})
            categories = var_def.get("categories", [])

            if categories and not merged[var_name].get("categories"):
                merged[var_name]["categories"] = categories

                # Ensure weights length matches categories length
                weights = merged[var_name].get("weights", [])
                if len(weights) != len(categories):
                    # Re-normalize to match
                    merged[var_name]["weights"] = [1.0 / len(categories)] * len(categories)

            # Apply Dynamic Categorical Shifts based on Tensor Risk
            if behavior:
                var_multi = behavior.get("variance_multiplier", 1.0)
                if var_multi > 1.5:
                    for idx, cat in enumerate(merged[var_name].get("categories", [])):
                        cat_lower = str(cat).lower()
                        # Shift mass to "risky" categories
                        if any(risk_word in cat_lower for risk_word in ["default", "delinquent", "fraud", "suspicious", "rejected"]):
                            merged[var_name]["weights"][idx] *= (var_multi * 0.8)
                    
                    # Re-normalize
                    total = sum(merged[var_name]["weights"])
                    if total > 0:
                        merged[var_name]["weights"] = [w / total for w in merged[var_name]["weights"]]
    for var_name, var_def in variables.items():
        if var_def.get("type") == "categorical" and var_name not in merged:
            categories = var_def.get("categories", ["Category_A", "Category_B"])
            merged[var_name] = {
                "family": "categorical",
                "categories": categories,
                "weights": [1.0 / len(categories)] * len(categories)
            }

    return merged


def _fix_zero_values(
    columns: Dict[str, np.ndarray],
    variables: Dict[str, Any],
    rng: np.random.Generator,
) -> None:
    """
    Replace zero values in price/amount/fee columns with small
    realistic values drawn from the non-zero portion of the
    distribution.

    For temporal data, zero-value trades are invalid. A trade
    with amount=0 and price=0 is nonsensical. This function
    replaces zeros with values at the 5th-25th percentile of
    the non-zero distribution (small but nonzero).
    """
    # Keywords that indicate columns where zero is invalid
    ZERO_INVALID_KEYWORDS = ["price", "amount", "fee", "principal", "emi", "quantity"]

    for var_name, col in columns.items():
        if var_name.startswith("_"):
            continue
        if col.dtype == object:
            continue

        # Check if this variable should not have zeros
        name_lower = var_name.lower()
        should_fix = any(kw in name_lower for kw in ZERO_INVALID_KEYWORDS)
        if not should_fix:
            continue

        try:
            col_float = col.astype(float)
        except (ValueError, TypeError):
            continue

        # Find zero positions
        zero_mask = np.abs(col_float) < 1e-10
        n_zeros = np.sum(zero_mask)
        if n_zeros == 0:
            continue

        # Get non-zero values
        nonzero_vals = col_float[~zero_mask]
        if len(nonzero_vals) < 3:
            # Too few non-zero values — use a small default
            fill_value = 1.0
        else:
            # Draw replacements from the 5th-25th percentile range
            p5 = np.percentile(np.abs(nonzero_vals), 5)
            p25 = np.percentile(np.abs(nonzero_vals), 25)
            if p5 < 1e-6:
                p5 = max(0.01, p25 * 0.1)
            fill_value = None  # Will sample per-zero

        # Replace zeros
        for idx in np.where(zero_mask)[0]:
            if fill_value is not None:
                col_float[idx] = fill_value
            else:
                col_float[idx] = rng.uniform(p5, max(p5 + 0.01, p25))

        columns[var_name] = col_float

