# =====================================================
# 3.3 -- CORRELATION WEAVER (Pure NumPy)
# =====================================================
# Injects multivariate correlations via Cholesky copula.
# Uses ONLY numpy — no scipy dependency.
#
# Algorithm:
#   1. Rank-transform continuous columns to uniform [0,1]
#   2. Map to standard normal via Box-Muller approximation
#   3. Build target correlation matrix
#   4. Validate PSD (eigenvalue repair)
#   5. Cholesky decompose: L = cholesky(R)
#   6. Apply: Z_corr = Z_indep @ L.T
#   7. Map back via quantile-matching
# =====================================================

import numpy as np
from typing import Any, Dict, List


def weave_correlations(
    columns: Dict[str, np.ndarray],
    covariance_list: List[Dict[str, Any]],
    parameters: Dict[str, Any],
) -> Dict[str, np.ndarray]:
    """
    Inject multivariate correlations into independent marginal columns.
    Pure numpy implementation — no scipy.
    """
    if not covariance_list:
        return columns

    # Identify continuous variables in the covariance list
    corr_vars = set()
    for spec in covariance_list:
        va, vb = spec.get("var_a", ""), spec.get("var_b", "")
        if va in columns and vb in columns:
            if _is_continuous(columns[va]) and _is_continuous(columns[vb]):
                corr_vars.add(va)
                corr_vars.add(vb)

    if len(corr_vars) < 2:
        return columns

    corr_var_list = sorted(corr_vars)
    k = len(corr_var_list)
    n = len(columns[corr_var_list[0]])

    # Step 1: Build data matrix
    data_matrix = np.column_stack([columns[v].astype(float) for v in corr_var_list])

    # Step 2: Rank transform to uniform (0, 1)
    uniform_matrix = np.zeros_like(data_matrix)
    for j in range(k):
        col = data_matrix[:, j]
        ranks = _rankdata(col)
        uniform_matrix[:, j] = ranks / (n + 1)

    # Step 3: Map to standard normal using rational approximation of probit
    normal_matrix = _probit(uniform_matrix)
    normal_matrix = np.clip(normal_matrix, -6, 6)

    # Step 4: Build target correlation matrix
    var_index = {v: i for i, v in enumerate(corr_var_list)}
    R = np.eye(k)

    for spec in covariance_list:
        va, vb = spec.get("var_a", ""), spec.get("var_b", "")
        coeff = max(-0.99, min(0.99, spec.get("coefficient", 0.0)))
        coeff = _compensate_small_n(coeff, n)
        if va in var_index and vb in var_index:
            i, j = var_index[va], var_index[vb]
            R[i, j] = coeff
            R[j, i] = coeff

    # Step 5: Validate PSD
    R = _repair_correlation_matrix(R)

    # Step 6: Cholesky decomposition
    try:
        L = np.linalg.cholesky(R)
    except np.linalg.LinAlgError:
        return columns

    # Step 7: Apply correlation
    emp_corr = np.corrcoef(normal_matrix, rowvar=False)
    emp_corr = _repair_correlation_matrix(emp_corr)

    try:
        L_emp = np.linalg.cholesky(emp_corr)
        L_emp_inv = np.linalg.inv(L_emp)
        whitened = normal_matrix @ L_emp_inv.T
        correlated = whitened @ L.T
    except np.linalg.LinAlgError:
        correlated = normal_matrix @ L.T

    # Step 8: Map back via quantile matching
    # Convert correlated normals to uniform via CDF approximation
    correlated_uniform = _normal_cdf(correlated)
    correlated_uniform = np.clip(correlated_uniform, 1e-10, 1 - 1e-10)

    for j, var_name in enumerate(corr_var_list):
        original_sorted = np.sort(data_matrix[:, j])
        # Use linear interpolation instead of index rounding to prevent discretization artifacts
        u_vals = correlated_uniform[:, j]
        emp_cdf = np.linspace(1e-5, 1 - 1e-5, n)
        columns[var_name] = np.interp(u_vals, emp_cdf, original_sorted)

    return columns

def _compensate_small_n(target_corr: float, n: int) -> float:
    """
    Inflate target correlation for small samples.
    Cholesky copula undershoots on small N due to discretization.
    """
    if n >= 500:
        return target_corr
    # Empirical correction factor
    inflation = 1.0 + (0.15 * (500 - n) / 500)
    compensated = target_corr * min(inflation, 1.3)
    return max(-0.99, min(0.99, compensated))

def _is_continuous(arr: np.ndarray) -> bool:
    """Check if array is numeric and has variance."""
    if arr.dtype == object:
        return False
    try:
        f_arr = arr.astype(float)
        if np.std(f_arr) == 0:
            return False
        return True
    except (ValueError, TypeError):
        return False


def _rankdata(arr: np.ndarray) -> np.ndarray:
    """
    Rank data (average method) — pure numpy replacement for scipy.stats.rankdata.
    """
    sorter = np.argsort(arr)
    ranks = np.empty_like(sorter, dtype=float)
    ranks[sorter] = np.arange(1, len(arr) + 1, dtype=float)

    # Handle ties: average the ranks of tied values
    sorted_arr = arr[sorter]
    i = 0
    while i < len(sorted_arr):
        j = i
        while j < len(sorted_arr) and sorted_arr[j] == sorted_arr[i]:
            j += 1
        if j > i + 1:
            avg_rank = np.mean(np.arange(i + 1, j + 1, dtype=float))
            for idx in sorter[i:j]:
                ranks[idx] = avg_rank
        i = j

    return ranks


def _probit(u: np.ndarray) -> np.ndarray:
    """
    Inverse normal CDF (probit function) using Beasley-Springer-Moro algorithm.
    Pure numpy — no scipy.
    """
    # Rational approximation valid for u in (0, 1)
    a = np.array([
        -3.969683028665376e+01, 2.209460984245205e+02,
        -2.759285104469687e+02, 1.383577518672690e+02,
        -3.066479806614716e+01, 2.506628277459239e+00,
    ])
    b = np.array([
        -5.447609879822406e+01, 1.615858368580409e+02,
        -1.556989798598866e+02, 6.680131188771972e+01,
        -1.328068155288572e+01,
    ])
    c = np.array([
        -7.784894002430293e-03, -3.223964580411365e-01,
        -2.400758277161838e+00, -2.549732539343734e+00,
        4.374664141464968e+00, 2.938163982698783e+00,
    ])
    d = np.array([
        7.784695709041462e-03, 3.224671290700398e-01,
        2.445134137142996e+00, 3.754408661907416e+00,
    ])

    u = np.clip(u, 1e-10, 1 - 1e-10)
    result = np.zeros_like(u)

    # Central region
    mask_central = (0.02425 <= u) & (u <= 0.97575)
    q = u[mask_central] - 0.5
    r = q * q
    result[mask_central] = (((((a[0]*r+a[1])*r+a[2])*r+a[3])*r+a[4])*r+a[5])*q / \
                            (((((b[0]*r+b[1])*r+b[2])*r+b[3])*r+b[4])*r+1)

    # Lower tail
    mask_low = u < 0.02425
    q = np.sqrt(-2 * np.log(u[mask_low]))
    result[mask_low] = (((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / \
                        ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)

    # Upper tail
    mask_high = u > 0.97575
    q = np.sqrt(-2 * np.log(1 - u[mask_high]))
    result[mask_high] = -(((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / \
                         ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)

    return result


def _normal_cdf(x: np.ndarray) -> np.ndarray:
    """
    Standard normal CDF approximation.
    Pure numpy — uses the Abramowitz & Stegun polynomial approximation
    of erf, fully vectorized (no Python-level loops).
    Max absolute error: < 1.5e-7.
    """
    # Abramowitz & Stegun formula 7.1.26 (fully vectorized)
    a1 = 0.254829592
    a2 = -0.284496736
    a3 = 1.421413741
    a4 = -1.453152027
    a5 = 1.061405429
    p = 0.3275911

    sign = np.sign(x)
    t = 1.0 / (1.0 + p * np.abs(x / np.sqrt(2.0)))
    erf_approx = 1.0 - (a1*t + a2*t**2 + a3*t**3 + a4*t**4 + a5*t**5) * np.exp(-(x / np.sqrt(2.0))**2)
    erf_val = sign * erf_approx
    return 0.5 * (1.0 + erf_val)


def _repair_correlation_matrix(R: np.ndarray) -> np.ndarray:
    """Ensure correlation matrix is positive semi-definite."""
    eigenvalues, eigenvectors = np.linalg.eigh(R)
    eigenvalues = np.maximum(eigenvalues, 1e-6)
    R_repaired = eigenvectors @ np.diag(eigenvalues) @ eigenvectors.T
    d = np.sqrt(np.diag(R_repaired))
    d[d == 0] = 1.0
    R_repaired = R_repaired / np.outer(d, d)
    np.fill_diagonal(R_repaired, 1.0)
    return np.clip(R_repaired, -1.0, 1.0)
