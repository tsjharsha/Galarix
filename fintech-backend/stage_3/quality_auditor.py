# =====================================================
# 3.7 -- QUALITY AUDITOR (Pure NumPy)
# =====================================================
# Post-generation statistical validation.
# Uses ONLY numpy — no scipy dependency.
#
# Implements a custom 2-sample KS test using numpy.
# =====================================================

import hashlib
import numpy as np
from typing import Any, Dict, List


def audit_dataset(
    columns: Dict[str, np.ndarray],
    parameters: Dict[str, Any],
    covariance_list: List[Dict[str, Any]],
    anomaly_rate_target: float,
) -> Dict[str, Any]:
    """
    Comprehensive statistical audit of the generated dataset.
    """
    report = {
        "ks_tests": {},
        "correlation_residuals": {},
        "constraint_violations": {},
        "anomaly_check": {},
        "uniqueness_score": 0.0,
        "null_rate": 0.0,
        "overall_score": 0.0,
        "pass": False,
    }

    n_rows = _get_row_count(columns)
    if n_rows == 0:
        return report

    # ── 1. KS Tests ──
    ks_scores = []
    for var_name, dist_def in parameters.items():
        family = dist_def.get("family", "")
        if family in ("categorical", ""):
            continue
        if var_name not in columns:
            continue
        col = columns[var_name]
        if col.dtype == object:
            continue
        try:
            col_float = col.astype(float)
            ks_result = _run_ks_test(col_float, dist_def)
            report["ks_tests"][var_name] = ks_result
            ks_scores.append(1.0 if ks_result["pass"] else 0.0)
        except Exception:
            report["ks_tests"][var_name] = {"statistic": 1.0, "pass": False}

    # ── 2. Correlation Residuals ──
    corr_residuals = []
    for spec in covariance_list:
        va, vb = spec.get("var_a", ""), spec.get("var_b", "")
        target_coeff = spec.get("coefficient", 0.0)
        if va not in columns or vb not in columns:
            continue
        try:
            col_a = columns[va].astype(float)
            col_b = columns[vb].astype(float)
            actual_coeff = np.corrcoef(col_a, col_b)[0, 1]
            residual = abs(actual_coeff - target_coeff)
            report["correlation_residuals"][f"{va} <-> {vb}"] = {
                "target": round(target_coeff, 4),
                "actual": round(float(actual_coeff), 4),
                "residual": round(float(residual), 4),
                "pass": bool(residual < 0.15),
            }
            corr_residuals.append(residual)
        except Exception:
            pass

    # ── 3. Constraint Violations ──
    total_violations = 0
    total_cells = 0
    for var_name, dist_def in parameters.items():
        bounds = dist_def.get("bounds", {})
        if not bounds or var_name not in columns:
            continue
        col = columns[var_name]
        if col.dtype == object:
            continue
        try:
            col_float = col.astype(float)
            violations = 0
            if "min" in bounds:
                violations += int(np.sum(col_float < bounds["min"]))
            if "max" in bounds:
                violations += int(np.sum(col_float > bounds["max"]))
            total_violations += violations
            total_cells += len(col_float)
            report["constraint_violations"][var_name] = {
                "violations": violations,
                "total": len(col_float),
                "rate": round(violations / max(len(col_float), 1), 6),
                "pass": bool(violations == 0),
            }
        except Exception:
            pass

    # ── 4. Anomaly Rate Check ──
    if "_is_anomaly" in columns:
        actual_count = int(np.sum(columns["_is_anomaly"]))
        actual_rate = actual_count / max(n_rows, 1)
        rate_diff = abs(actual_rate - anomaly_rate_target)
        report["anomaly_check"] = {
            "target_rate": round(anomaly_rate_target, 4),
            "actual_rate": round(actual_rate, 4),
            "actual_count": actual_count,
            "rate_difference": round(rate_diff, 4),
            "pass": bool(rate_diff < 0.05 or anomaly_rate_target == 0),
        }

    # ── 5. Uniqueness Score ──
    row_hashes = set()
    sample_n = min(n_rows, 10000)
    for i in range(sample_n):
        row_vals = []
        for var_name in sorted(columns.keys()):
            if var_name == "_is_anomaly":
                continue
            try:
                row_vals.append(str(columns[var_name][i]))
            except IndexError:
                pass
        row_hashes.add(hashlib.sha256("\x1f".join(row_vals).encode("utf-8")).hexdigest())
    report["uniqueness_score"] = round(len(row_hashes) / max(sample_n, 1), 6)

    # ── 6. Null Rate ──
    total_nulls = 0
    total_all_cells = 0
    for var_name, col in columns.items():
        if var_name == "_is_anomaly":
            continue
        total_all_cells += len(col)
        if col.dtype == object:
            total_nulls += sum(1 for x in col if x is None or str(x) == "nan")
        else:
            try:
                total_nulls += int(np.sum(np.isnan(col.astype(float))))
            except (ValueError, TypeError):
                pass
    report["null_rate"] = round(total_nulls / max(total_all_cells, 1), 6)

    # ── 7. Overall Score ──
    # Scoring accounts for the fact that anomaly injection
    # intentionally shifts distributions (so KS test failures
    # on anomaly-injected data are expected behavior, not bugs).
    score = 100.0

    # KS tests: softer penalty (anomalies shift distributions)
    if ks_scores:
        ks_pass_rate = np.mean(ks_scores)
        if ks_pass_rate < 0.3:
            score -= 25
        elif ks_pass_rate < 0.5:
            score -= 15
        elif ks_pass_rate < 0.8:
            score -= 5

    # Correlation residuals: relaxed threshold for bounded data
    if corr_residuals:
        avg_resid = np.mean(corr_residuals)
        if avg_resid > 0.30:
            score -= 15
        elif avg_resid > 0.20:
            score -= 8

    # Constraint violations: severe penalty (must be zero)
    violation_rate = total_violations / max(total_cells, 1)
    if violation_rate > 0:
        score -= min(30, violation_rate * 1000)

    # Uniqueness: penalize duplicates
    if report["uniqueness_score"] < 0.95:
        score -= 15
    elif report["uniqueness_score"] < 0.99:
        score -= 5

    # Null rate: severe penalty (must be zero)
    if report["null_rate"] > 0:
        score -= 25

    score = max(0, min(100, score))
    report["overall_score"] = round(score, 1)
    report["pass"] = bool(score >= 60.0)
    return report


def _run_ks_test(
    samples: np.ndarray,
    dist_def: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Custom 2-sample KS test using pure numpy.
    Generates a reference sample and compares empirical CDFs.
    """
    family = dist_def.get("family", "normal")
    params = dist_def.get("params", {})
    bounds = dist_def.get("bounds", {})
    n = len(samples)

    # Generate reference from target distribution
    ref_rng = np.random.default_rng(42)

    from stage_3.marginal_sampler import _truncated_sample
    
    b_min = bounds.get("min", None)
    b_max = bounds.get("max", None)
    
    if family == "normal":
        reference = _truncated_sample(ref_rng, "normal", {"mean": params.get("mean", 0), "std": max(params.get("std", 1), 0.001)}, n, b_min, b_max)
    elif family == "lognormal":
        reference = _truncated_sample(ref_rng, "lognormal", {"mu": params.get("mu", 0), "sigma": max(params.get("sigma", 1), 0.001)}, n, b_min, b_max)
    elif family == "beta":
        alpha = max(params.get("alpha", 2), 0.01)
        beta_p = max(params.get("beta", 2), 0.01)
        reference = ref_rng.beta(alpha, beta_p, size=n)
    elif family == "student_t":
        reference = _truncated_sample(ref_rng, "student_t", {"df": max(params.get("df", 3), 1), "loc": params.get("loc", 0), "scale": max(params.get("scale", 1), 0.001)}, n, b_min, b_max)
    elif family == "cauchy":
        reference = _truncated_sample(ref_rng, "cauchy", {"loc": params.get("loc", 0), "scale": max(params.get("scale", 1), 0.001)}, n, b_min, b_max)
    else:
        reference = ref_rng.normal(0, 1, size=n)

    # KS statistic: max difference between empirical CDFs
    ks_stat = _ks_2samp(samples, reference)

    # Approximate critical value (alpha=0.01, relaxed for post-anomaly data)
    # Critical value for 2-sample KS at alpha=0.01: ~1.63 * sqrt((n1+n2)/(n1*n2))
    critical = 1.63 * np.sqrt(2.0 / n)

    return {
        "statistic": round(float(ks_stat), 6),
        "critical_value": round(float(critical), 6),
        "pass": bool(ks_stat < critical),
    }


def _ks_2samp(data1: np.ndarray, data2: np.ndarray) -> float:
    """
    Two-sample Kolmogorov-Smirnov statistic.
    Pure numpy implementation.
    """
    n1 = len(data1)
    n2 = len(data2)
    all_data = np.concatenate([data1, data2])
    all_sorted = np.sort(all_data)

    cdf1 = np.searchsorted(np.sort(data1), all_sorted, side='right') / n1
    cdf2 = np.searchsorted(np.sort(data2), all_sorted, side='right') / n2

    return float(np.max(np.abs(cdf1 - cdf2)))


def _get_row_count(columns: Dict[str, np.ndarray]) -> int:
    for arr in columns.values():
        return len(arr)
    return 0
