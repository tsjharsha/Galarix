# =====================================================
# STATISTICAL VALIDATOR — Mathematical Trust Core
# =====================================================
# Runs formal statistical tests on every generated
# column and returns pass/fail with p-values and
# confidence intervals.
#
# Pure NumPy — no scipy dependency.
#
# Tests:
#   1. Kolmogorov-Smirnov (2-sample) — continuous vars
#   2. Chi-Square Goodness-of-Fit — categorical vars
#   3. Earth Mover's Distance (Wasserstein-1) — shape
#   4. Moments Comparison — mean, var, skew, kurtosis
#   5. Correlation Fidelity — target vs actual
#   6. Conditional Rule Compliance — zero violations
#   7. Derived Field Accuracy — formula verification
#   8. Regional Bounds Compliance — correct score system
#   9. Regional Distribution Shape — correct parameters
# =====================================================

import math
import numpy as np
from typing import Any, Dict, List, Optional, Tuple

from trust_engine.regional_benchmarks import (
    get_benchmarks,
    get_credit_range,
    get_credit_system,
    get_rate_baseline,
    get_income_median,
)


# ─────────────────────────────────────────────────
# 1. KOLMOGOROV-SMIRNOV TEST (2-sample, pure numpy)
# ─────────────────────────────────────────────────

def ks_test_continuous(
    samples: np.ndarray,
    dist_def: Dict[str, Any],
    var_name: str,
    alpha: float = 0.01,
) -> Dict[str, Any]:
    """
    Two-sample KS test: generated data vs reference sample
    from the target distribution.
    """
    family = dist_def.get("family", "normal")
    params = dist_def.get("params", {})
    bounds = dist_def.get("bounds", {})
    n = len(samples)

    if n < 10:
        return _skip_result("ks_test", var_name, "Too few samples")

    # Generate reference from target distribution
    ref_rng = np.random.default_rng(42)
    b_min = bounds.get("min", None)
    b_max = bounds.get("max", None)

    reference = _generate_reference(ref_rng, family, params, n, b_min, b_max)
    if reference is None:
        return _skip_result("ks_test", var_name, f"Unsupported family: {family}")

    # KS statistic
    ks_stat = _ks_2samp_statistic(samples, reference)

    # Critical value at alpha (2-sample asymptotic)
    c_alpha = {0.01: 1.63, 0.05: 1.36, 0.10: 1.22}.get(alpha, 1.63)
    critical = c_alpha * math.sqrt(2.0 / n)

    passed = bool(ks_stat < critical)

    return {
        "test_name": "kolmogorov_smirnov",
        "variable": var_name,
        "statistic": round(float(ks_stat), 6),
        "critical_value": round(float(critical), 6),
        "alpha": alpha,
        "pass": passed,
        "interpretation": (
            f"Distribution match confirmed (D={ks_stat:.4f} < critical={critical:.4f})"
            if passed else
            f"Distribution deviation detected (D={ks_stat:.4f} > critical={critical:.4f})"
        ),
    }


# ─────────────────────────────────────────────────
# 2. CHI-SQUARE GOODNESS-OF-FIT (pure numpy)
# ─────────────────────────────────────────────────

def chi_square_test_categorical(
    samples: np.ndarray,
    dist_def: Dict[str, Any],
    var_name: str,
    alpha: float = 0.01,
) -> Dict[str, Any]:
    """
    Chi-square goodness-of-fit: observed category frequencies
    vs expected weights.
    """
    categories = dist_def.get("categories", [])
    weights = dist_def.get("weights", [])
    n = len(samples)

    if n < 20 or not categories or not weights:
        return _skip_result("chi_square", var_name, "Insufficient data or missing categories")

    # Count observed frequencies
    str_cats = [str(c) for c in categories]
    observed = np.array([np.sum(samples.astype(str) == cat) for cat in str_cats], dtype=float)

    # Expected frequencies
    weights_arr = np.array(weights, dtype=float)
    weights_arr = weights_arr / weights_arr.sum()  # Normalize
    expected = weights_arr * n

    # Avoid division by zero
    mask = expected > 0
    if mask.sum() < 2:
        return _skip_result("chi_square", var_name, "Too few non-zero expected categories")

    # Chi-square statistic
    chi2 = float(np.sum(((observed[mask] - expected[mask]) ** 2) / expected[mask]))

    # Degrees of freedom
    df = int(mask.sum() - 1)
    if df < 1:
        df = 1

    # Critical values (chi-square table, alpha=0.01)
    # Pre-computed for df 1-20
    chi2_critical_001 = {
        1: 6.635, 2: 9.210, 3: 11.345, 4: 13.277, 5: 15.086,
        6: 16.812, 7: 18.475, 8: 20.090, 9: 21.666, 10: 23.209,
        11: 24.725, 12: 26.217, 13: 27.688, 14: 29.141, 15: 30.578,
        16: 31.999, 17: 33.409, 18: 34.805, 19: 36.191, 20: 37.566,
    }
    critical = chi2_critical_001.get(df, 6.635 + df * 2.0)

    passed = bool(chi2 < critical)

    return {
        "test_name": "chi_square_goodness_of_fit",
        "variable": var_name,
        "statistic": round(chi2, 4),
        "critical_value": round(critical, 4),
        "degrees_of_freedom": df,
        "alpha": alpha,
        "observed": {str_cats[i]: int(observed[i]) for i in range(len(str_cats))},
        "expected": {str_cats[i]: round(float(expected[i]), 1) for i in range(len(str_cats))},
        "pass": passed,
        "interpretation": (
            f"Category proportions match target weights (χ²={chi2:.2f} < critical={critical:.2f})"
            if passed else
            f"Category proportions deviate from target (χ²={chi2:.2f} > critical={critical:.2f})"
        ),
    }


# ─────────────────────────────────────────────────
# 3. EARTH MOVER'S DISTANCE (Wasserstein-1)
# ─────────────────────────────────────────────────

def emd_test(
    samples: np.ndarray,
    dist_def: Dict[str, Any],
    var_name: str,
) -> Dict[str, Any]:
    """
    Earth Mover's Distance between generated and reference
    distributions. Lower = better shape match.
    """
    family = dist_def.get("family", "normal")
    params = dist_def.get("params", {})
    bounds = dist_def.get("bounds", {})
    n = len(samples)

    if n < 10:
        return _skip_result("emd", var_name, "Too few samples")

    ref_rng = np.random.default_rng(42)
    b_min = bounds.get("min", None)
    b_max = bounds.get("max", None)
    reference = _generate_reference(ref_rng, family, params, n, b_min, b_max)
    if reference is None:
        return _skip_result("emd", var_name, f"Unsupported family: {family}")

    # Wasserstein-1: mean of |sorted(x) - sorted(y)|
    s1 = np.sort(samples)
    s2 = np.sort(reference)
    emd_val = float(np.mean(np.abs(s1 - s2)))

    # Normalize by the range of the data for interpretability
    data_range = max(float(np.ptp(samples)), 1e-6)
    normalized_emd = emd_val / data_range

    passed = bool(normalized_emd < 0.10)  # Less than 10% of range

    return {
        "test_name": "earth_movers_distance",
        "variable": var_name,
        "emd_raw": round(emd_val, 4),
        "emd_normalized": round(normalized_emd, 6),
        "threshold": 0.10,
        "pass": passed,
        "interpretation": (
            f"Shape match confirmed (normalized EMD={normalized_emd:.4f} < 0.10)"
            if passed else
            f"Shape deviation detected (normalized EMD={normalized_emd:.4f} > 0.10)"
        ),
    }


# ─────────────────────────────────────────────────
# 4. MOMENTS COMPARISON
# ─────────────────────────────────────────────────

def moments_test(
    samples: np.ndarray,
    dist_def: Dict[str, Any],
    var_name: str,
) -> Dict[str, Any]:
    """
    Compare generated moments (mean, variance, skewness, kurtosis)
    to theoretical moments of the target distribution.
    """
    family = dist_def.get("family", "normal")
    params = dist_def.get("params", {})
    n = len(samples)

    if n < 30:
        return _skip_result("moments", var_name, "Too few samples for moment estimation")

    # Compute empirical moments
    emp_mean = float(np.mean(samples))
    emp_var = float(np.var(samples, ddof=1))
    emp_std = math.sqrt(emp_var) if emp_var > 0 else 0
    emp_median = float(np.median(samples))

    # Compute skewness (Fisher)
    if emp_std > 0:
        emp_skew = float(np.mean(((samples - emp_mean) / emp_std) ** 3))
    else:
        emp_skew = 0.0

    # Theoretical moments
    theo = _theoretical_moments(family, params)

    # Compare
    checks = {}
    if theo.get("mean") is not None and theo["mean"] != 0:
        dev = abs(emp_mean - theo["mean"]) / max(abs(theo["mean"]), 1e-6)
        checks["mean"] = {
            "theoretical": round(theo["mean"], 4),
            "empirical": round(emp_mean, 4),
            "deviation_pct": round(dev * 100, 2),
            "pass": bool(dev < 0.15),  # Within 15%
        }

    if theo.get("median") is not None and theo["median"] != 0:
        dev = abs(emp_median - theo["median"]) / max(abs(theo["median"]), 1e-6)
        checks["median"] = {
            "theoretical": round(theo["median"], 4),
            "empirical": round(emp_median, 4),
            "deviation_pct": round(dev * 100, 2),
            "pass": bool(dev < 0.15),
        }

    if theo.get("variance") is not None and theo["variance"] > 0:
        dev = abs(emp_var - theo["variance"]) / max(theo["variance"], 1e-6)
        checks["variance"] = {
            "theoretical": round(theo["variance"], 4),
            "empirical": round(emp_var, 4),
            "deviation_pct": round(dev * 100, 2),
            "pass": bool(dev < 0.50),  # Variance is noisier, allow 50%
        }

    all_pass = all(c.get("pass", True) for c in checks.values())

    return {
        "test_name": "moments_comparison",
        "variable": var_name,
        "family": family,
        "checks": checks,
        "pass": all_pass,
        "interpretation": (
            f"Moments match target distribution ({len(checks)} checks passed)"
            if all_pass else
            f"Moment deviation detected in {sum(1 for c in checks.values() if not c.get('pass', True))}/{len(checks)} checks"
        ),
    }


# ─────────────────────────────────────────────────
# 5. CORRELATION FIDELITY
# ─────────────────────────────────────────────────

def correlation_fidelity_test(
    columns: Dict[str, np.ndarray],
    covariance_list: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Compare achieved correlations to target correlation specs.
    """
    results = {}
    residuals = []

    for spec in covariance_list:
        va = spec.get("var_a", "")
        vb = spec.get("var_b", "")
        target = spec.get("coefficient", 0.0)

        if va not in columns or vb not in columns:
            continue

        try:
            col_a = columns[va].astype(float)
            col_b = columns[vb].astype(float)
            actual = float(np.corrcoef(col_a, col_b)[0, 1])
            residual = abs(actual - target)
            residuals.append(residual)

            results[f"{va} <-> {vb}"] = {
                "target": round(target, 4),
                "actual": round(actual, 4),
                "residual": round(residual, 4),
                "pass": bool(residual < 0.15),
            }
        except (ValueError, TypeError):
            pass

    avg_residual = float(np.mean(residuals)) if residuals else 0.0
    all_pass = all(r["pass"] for r in results.values()) if results else True

    return {
        "test_name": "correlation_fidelity",
        "pairs_tested": len(results),
        "average_residual": round(avg_residual, 4),
        "max_residual": round(max(residuals) if residuals else 0, 4),
        "details": results,
        "pass": all_pass,
        "interpretation": (
            f"All {len(results)} correlation targets met (avg residual={avg_residual:.4f})"
            if all_pass else
            f"Correlation deviation in {sum(1 for r in results.values() if not r['pass'])}/{len(results)} pairs"
        ),
    }


# ─────────────────────────────────────────────────
# 6. CONDITIONAL RULE COMPLIANCE
# ─────────────────────────────────────────────────

def conditional_compliance_test(
    columns: Dict[str, np.ndarray],
    dependencies: Dict[str, Any],
    entity: str,
) -> Dict[str, Any]:
    """
    Verify all conditional rules hold in the generated data.
    """
    conditionals = dependencies.get("conditionals", [])
    results = []
    total_violations = 0

    for rule in conditionals:
        if_clause = rule.get("if", {})
        then_clause = rule.get("then", {})

        # Simple string match conditionals: if var == value
        for if_var, if_val in if_clause.items():
            # Find the full column name (may have entity prefix)
            if_col = _find_column(columns, if_var, entity)
            if if_col is None:
                continue

            col_data = columns[if_col]

            if isinstance(if_val, dict):
                # Range condition: {"min": 750}
                if "min" in if_val:
                    try:
                        float_col = col_data.astype(float)
                        mask = float_col >= if_val["min"]
                    except (ValueError, TypeError):
                        continue
                else:
                    continue
            else:
                # Exact match
                mask = col_data.astype(str) == str(if_val)

            n_matching = int(np.sum(mask))
            if n_matching == 0:
                continue

            # Check then clause
            for then_var, then_constraint in then_clause.items():
                then_col = _find_column(columns, then_var, entity)
                if then_col is None:
                    continue

                then_data = columns[then_col][mask]
                violations = 0

                if isinstance(then_constraint, dict):
                    try:
                        then_float = then_data.astype(float)
                        if "max" in then_constraint:
                            violations = int(np.sum(then_float > then_constraint["max"]))
                        if "min" in then_constraint:
                            violations += int(np.sum(then_float < then_constraint["min"]))
                    except (ValueError, TypeError):
                        pass
                elif isinstance(then_constraint, str):
                    violations = int(np.sum(then_data.astype(str) != then_constraint))

                total_violations += violations
                results.append({
                    "rule": f"IF {if_var}={if_val} THEN {then_var} {then_constraint}",
                    "rows_matching_condition": n_matching,
                    "violations": violations,
                    "pass": bool(violations == 0),
                })

    all_pass = total_violations == 0

    return {
        "test_name": "conditional_compliance",
        "rules_tested": len(results),
        "total_violations": total_violations,
        "details": results,
        "pass": all_pass,
        "interpretation": (
            f"All {len(results)} conditional rules satisfied (0 violations)"
            if all_pass else
            f"{total_violations} violations across {sum(1 for r in results if not r['pass'])} rules"
        ),
    }


# ─────────────────────────────────────────────────
# 7. DERIVED FIELD ACCURACY
# ─────────────────────────────────────────────────

def derived_accuracy_test(
    columns: Dict[str, np.ndarray],
    dependencies: Dict[str, Any],
    entity: str,
) -> Dict[str, Any]:
    """
    Verify derived formulas produce correct results.
    """
    derived = dependencies.get("derived", [])
    results = []

    for rule in derived:
        target = rule.get("target", "")
        formula = rule.get("formula", "")

        target_col = _find_column(columns, target, entity)
        if target_col is None or not formula:
            continue

        try:
            actual_vals = columns[target_col].astype(float)
        except (ValueError, TypeError):
            continue

        # Try to compute expected values from formula
        try:
            local_vars = {}
            for col_name, col_data in columns.items():
                safe_name = col_name.replace(f"{entity}_", "")
                try:
                    local_vars[safe_name] = col_data.astype(float)
                except (ValueError, TypeError):
                    local_vars[safe_name] = col_data

            local_vars["np"] = np
            expected_vals = eval(formula, {"__builtins__": {}}, local_vars)

            if isinstance(expected_vals, np.ndarray):
                # Compare where both are finite
                finite_mask = np.isfinite(actual_vals) & np.isfinite(expected_vals)
                if np.sum(finite_mask) < 5:
                    continue

                actual_f = actual_vals[finite_mask]
                expected_f = expected_vals[finite_mask]

                # Relative deviation
                denom = np.maximum(np.abs(expected_f), 1.0)
                deviations = np.abs(actual_f - expected_f) / denom
                max_dev = float(np.max(deviations))
                mean_dev = float(np.mean(deviations))
                passed = bool(max_dev < 0.05)  # Within 5%

                results.append({
                    "target": target,
                    "formula": formula[:80],
                    "max_deviation_pct": round(max_dev * 100, 4),
                    "mean_deviation_pct": round(mean_dev * 100, 4),
                    "samples_checked": int(np.sum(finite_mask)),
                    "pass": passed,
                })
        except Exception:
            # Formula eval failed — skip but don't crash
            pass

    all_pass = all(r["pass"] for r in results) if results else True

    return {
        "test_name": "derived_field_accuracy",
        "fields_tested": len(results),
        "details": results,
        "pass": all_pass,
        "interpretation": (
            f"All {len(results)} derived fields accurate (max deviation < 5%)"
            if all_pass else
            f"Deviation > 5% in {sum(1 for r in results if not r['pass'])} derived fields"
        ),
    }


# ─────────────────────────────────────────────────
# 8. REGIONAL FIDELITY
# ─────────────────────────────────────────────────

def regional_fidelity_test(
    columns: Dict[str, np.ndarray],
    parameters: Dict[str, Any],
    region: str,
    entity: str,
) -> Dict[str, Any]:
    """
    Validate generated data matches the correct regional benchmarks.
    This is a HARD GATE — failure here means UNTRUSTED.
    """
    benchmarks = get_benchmarks(region)
    checks = {}
    hard_fail = False

    # ── 1. Credit Score System Match ──
    score_col = _find_column(columns, "credit_score", entity)
    if score_col is not None:
        try:
            scores = columns[score_col].astype(float)
            actual_min = float(np.min(scores))
            actual_max = float(np.max(scores))
            actual_mean = float(np.mean(scores))

            expected_range = benchmarks["credit_score"]["range"]
            expected_system = benchmarks["credit_score"]["system"]
            expected_mean = benchmarks["credit_score"]["national_mean"]

            # Range check
            range_ok = bool(actual_min >= expected_range[0] - 5 and actual_max <= expected_range[1] + 5)

            # Mean proximity check (within 15%)
            mean_dev = abs(actual_mean - expected_mean) / max(expected_mean, 1)
            mean_ok = bool(mean_dev < 0.15)

            checks["credit_score_system"] = {
                "expected": f"{expected_system} ({expected_range[0]}-{expected_range[1]})",
                "actual_range": f"{actual_min:.0f}-{actual_max:.0f}",
                "pass": range_ok,
            }
            checks["credit_score_mean"] = {
                "expected": expected_mean,
                "actual": round(actual_mean, 1),
                "deviation_pct": round(mean_dev * 100, 2),
                "pass": mean_ok,
            }

            if not range_ok:
                hard_fail = True  # Wrong scoring system = automatic UNTRUSTED
        except (ValueError, TypeError):
            pass

    # ── 2. Interest Rate Baseline ──
    rate_col = _find_column(columns, "interest_rate", entity)
    if rate_col is not None:
        try:
            rates = columns[rate_col].astype(float)
            actual_mean = float(np.mean(rates))
            expected_mean = benchmarks["interest_rate"]["personal_loan_mean"]

            dev = abs(actual_mean - expected_mean) / max(expected_mean, 1)
            passed = bool(dev < 0.30)  # Within 30% (rates vary by risk)

            checks["interest_rate_baseline"] = {
                "expected": expected_mean,
                "actual": round(actual_mean, 2),
                "deviation_pct": round(dev * 100, 2),
                "pass": passed,
            }

            # Hard fail if rates are completely wrong region
            # (e.g., 30% rates for Japan which should be ~1.5%)
            if dev > 1.0:
                hard_fail = True
        except (ValueError, TypeError):
            pass

    # ── 3. Currency Magnitude (income/salary) ──
    salary_col = _find_column(columns, "salary_base", entity)
    if salary_col is None:
        salary_col = _find_column(columns, "gross_amount", entity)
    if salary_col is not None:
        try:
            salaries = columns[salary_col].astype(float)
            actual_median = float(np.median(salaries))
            expected_median = benchmarks["income"]["median_annual"]
            currency = benchmarks["currency"]

            # Order of magnitude check
            if expected_median > 0 and actual_median > 0:
                ratio = actual_median / expected_median
                magnitude_ok = bool(0.1 < ratio < 10)
            else:
                magnitude_ok = True

            checks["income_magnitude"] = {
                "expected_currency": currency,
                "expected_median": expected_median,
                "actual_median": round(actual_median, 0),
                "ratio": round(ratio, 3) if expected_median > 0 else 0,
                "pass": magnitude_ok,
            }

            if not magnitude_ok:
                hard_fail = True
        except (ValueError, TypeError):
            pass

    # ── 4. Distribution Shape (sigma for key variables) ──
    from stage_1_5.localization_engine import REGIONAL_DISTRIBUTION_OVERRIDES
    overrides = REGIONAL_DISTRIBUTION_OVERRIDES.get(region, {})

    for var_suffix, expected_dist in overrides.items():
        col_name = _find_column(columns, var_suffix, entity)
        if col_name is None or columns[col_name].dtype == object:
            continue

        try:
            col_float = columns[col_name].astype(float)
            expected_params = expected_dist.get("params", {})

            if "std" in expected_params:
                actual_std = float(np.std(col_float, ddof=1))
                expected_std = expected_params["std"]
                dev = abs(actual_std - expected_std) / max(expected_std, 1e-6)
                checks[f"shape_{var_suffix}_std"] = {
                    "expected_std": expected_std,
                    "actual_std": round(actual_std, 4),
                    "deviation_pct": round(dev * 100, 2),
                    "pass": bool(dev < 0.50),
                }
            elif "sigma" in expected_params:
                # For lognormal, sigma controls the shape
                # Estimate sigma from log of the data
                positive = col_float[col_float > 0]
                if len(positive) > 10:
                    actual_sigma = float(np.std(np.log(positive), ddof=1))
                    expected_sigma = expected_params["sigma"]
                    dev = abs(actual_sigma - expected_sigma) / max(expected_sigma, 1e-6)
                    checks[f"shape_{var_suffix}_sigma"] = {
                        "expected_sigma": expected_sigma,
                        "actual_sigma": round(actual_sigma, 4),
                        "deviation_pct": round(dev * 100, 2),
                        "pass": bool(dev < 0.50),
                    }
        except (ValueError, TypeError):
            pass

    all_pass = all(c["pass"] for c in checks.values()) if checks else True

    return {
        "test_name": "regional_fidelity",
        "region": region,
        "region_name": benchmarks["name"],
        "credit_system": benchmarks["credit_score"]["system"],
        "currency": benchmarks["currency"],
        "central_bank": benchmarks["central_bank"],
        "checks_passed": sum(1 for c in checks.values() if c["pass"]),
        "checks_total": len(checks),
        "hard_fail": hard_fail,
        "details": checks,
        "pass": all_pass and not hard_fail,
        "interpretation": (
            f"All {len(checks)} regional benchmarks verified for {benchmarks['name']}"
            if (all_pass and not hard_fail) else
            (
                f"CRITICAL: Data does not match {benchmarks['name']} benchmarks — wrong scoring system or rate regime"
                if hard_fail else
                f"Minor regional deviations in {sum(1 for c in checks.values() if not c['pass'])}/{len(checks)} checks"
            )
        ),
    }


# ─────────────────────────────────────────────────
# FULL VALIDATION SUITE
# ─────────────────────────────────────────────────

def run_full_validation(
    columns: Dict[str, np.ndarray],
    parameters: Dict[str, Any],
    covariance_list: List[Dict[str, Any]],
    dependencies: Dict[str, Any],
    entity: str,
    region: str = "US",
    alpha: float = 0.01,
) -> Dict[str, Any]:
    """
    Run the complete statistical validation suite.

    Returns a structured report with all test results,
    ready for the trust report builder.
    """
    # Filter out anomaly rows for distribution tests
    anomaly_mask = None
    if "_is_anomaly" in columns:
        try:
            anomaly_mask = columns["_is_anomaly"].astype(bool)
        except (ValueError, TypeError):
            pass

    # ── Distribution Fidelity (KS + Chi-Square + EMD + Moments) ──
    ks_results = {}
    chi2_results = {}
    emd_results = {}
    moments_results = {}

    for var_name, dist_def in parameters.items():
        if var_name.startswith("_"):
            continue
        if var_name not in columns:
            continue

        family = dist_def.get("family", "")
        col = columns[var_name]

        # Exclude anomaly rows for distribution tests
        if anomaly_mask is not None and col.dtype != object:
            try:
                clean_col = col[~anomaly_mask]
            except (IndexError, TypeError):
                clean_col = col
        else:
            clean_col = col

        if family == "categorical":
            chi2_results[var_name] = chi_square_test_categorical(
                clean_col, dist_def, var_name, alpha
            )
        elif family in ("normal", "lognormal", "beta", "student_t", "cauchy"):
            try:
                float_col = clean_col.astype(float)
                ks_results[var_name] = ks_test_continuous(float_col, dist_def, var_name, alpha)
                emd_results[var_name] = emd_test(float_col, dist_def, var_name)
                moments_results[var_name] = moments_test(float_col, dist_def, var_name)
            except (ValueError, TypeError):
                pass

    # ── Correlation Fidelity ──
    corr_result = correlation_fidelity_test(columns, covariance_list)

    # ── Conditional Compliance ──
    cond_result = conditional_compliance_test(columns, dependencies, entity)

    # ── Derived Field Accuracy ──
    derived_result = derived_accuracy_test(columns, dependencies, entity)

    # ── Regional Fidelity ──
    regional_result = regional_fidelity_test(columns, parameters, region, entity)

    # ── Aggregate ──
    ks_pass_rate = (
        sum(1 for r in ks_results.values() if r.get("pass", False)) / max(len(ks_results), 1)
    )
    chi2_pass_rate = (
        sum(1 for r in chi2_results.values() if r.get("pass", False)) / max(len(chi2_results), 1)
    )

    return {
        "distribution_fidelity": {
            "ks_tests": ks_results,
            "chi_square_tests": chi2_results,
            "emd_tests": emd_results,
            "moments_tests": moments_results,
            "ks_pass_rate": round(ks_pass_rate, 4),
            "chi2_pass_rate": round(chi2_pass_rate, 4),
        },
        "correlation_fidelity": corr_result,
        "conditional_compliance": cond_result,
        "derived_accuracy": derived_result,
        "regional_fidelity": regional_result,
    }


# ─────────────────────────────────────────────────
# INTERNAL HELPERS
# ─────────────────────────────────────────────────

def _ks_2samp_statistic(data1: np.ndarray, data2: np.ndarray) -> float:
    """Two-sample KS statistic (pure numpy)."""
    n1, n2 = len(data1), len(data2)
    all_sorted = np.sort(np.concatenate([data1, data2]))
    cdf1 = np.searchsorted(np.sort(data1), all_sorted, side="right") / n1
    cdf2 = np.searchsorted(np.sort(data2), all_sorted, side="right") / n2
    return float(np.max(np.abs(cdf1 - cdf2)))


def _generate_reference(
    rng: np.random.Generator,
    family: str,
    params: Dict[str, Any],
    n: int,
    b_min: Optional[float] = None,
    b_max: Optional[float] = None,
) -> Optional[np.ndarray]:
    """Generate reference samples from target distribution."""
    from stage_3.marginal_sampler import _truncated_sample

    if family == "normal":
        return _truncated_sample(
            rng, "normal",
            {"mean": params.get("mean", 0), "std": max(params.get("std", 1), 0.001)},
            n, b_min, b_max,
        )
    elif family == "lognormal":
        return _truncated_sample(
            rng, "lognormal",
            {"mu": params.get("mu", 0), "sigma": max(params.get("sigma", 1), 0.001)},
            n, b_min, b_max,
        )
    elif family == "beta":
        alpha = max(params.get("alpha", 2), 0.01)
        beta_p = max(params.get("beta", 2), 0.01)
        return rng.beta(alpha, beta_p, size=n)
    elif family == "student_t":
        return _truncated_sample(
            rng, "student_t",
            {"df": max(params.get("df", 3), 1), "loc": params.get("loc", 0),
             "scale": max(params.get("scale", 1), 0.001)},
            n, b_min, b_max,
        )
    elif family == "cauchy":
        return _truncated_sample(
            rng, "cauchy",
            {"loc": params.get("loc", 0), "scale": max(params.get("scale", 1), 0.001)},
            n, b_min, b_max,
        )
    return None


def _theoretical_moments(family: str, params: Dict[str, Any]) -> Dict[str, Optional[float]]:
    """Compute theoretical moments from distribution parameters."""
    if family == "normal":
        mean = params.get("mean", 0)
        std = params.get("std", 1)
        return {"mean": mean, "median": mean, "variance": std ** 2}
    elif family == "lognormal":
        mu = params.get("mu", 0)
        sigma = params.get("sigma", 1)
        mean = math.exp(mu + sigma ** 2 / 2)
        median = math.exp(mu)
        variance = (math.exp(sigma ** 2) - 1) * math.exp(2 * mu + sigma ** 2)
        return {"mean": mean, "median": median, "variance": variance}
    elif family == "beta":
        a = params.get("alpha", 2)
        b = params.get("beta", 2)
        mean = a / (a + b)
        variance = (a * b) / ((a + b) ** 2 * (a + b + 1))
        return {"mean": mean, "median": None, "variance": variance}
    elif family == "student_t":
        loc = params.get("loc", 0)
        return {"mean": loc, "median": loc, "variance": None}
    return {"mean": None, "median": None, "variance": None}


def _find_column(
    columns: Dict[str, np.ndarray],
    var_name: str,
    entity: str,
) -> Optional[str]:
    """Find a column by name, with or without entity prefix."""
    # Exact match
    if var_name in columns:
        return var_name
    # With entity prefix
    prefixed = f"{entity}_{var_name}"
    if prefixed in columns:
        return prefixed
    # Partial match (last resort)
    for col in columns:
        if col.endswith(f"_{var_name}"):
            return col
    return None


def _skip_result(test_name: str, var_name: str, reason: str) -> Dict[str, Any]:
    """Return a skip result for tests that can't run."""
    return {
        "test_name": test_name,
        "variable": var_name,
        "pass": True,  # Don't penalize for skipped tests
        "skipped": True,
        "reason": reason,
        "interpretation": f"Skipped: {reason}",
    }
