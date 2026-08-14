# =====================================================
# LOCALIZATION ENGINE — Geographic Scaling & Distribution Overrides
# =====================================================
# Applies regional economic realities to the statistical
# schema. Different countries have vastly different:
#   - Currencies & Magnitudes (e.g., INR vs USD)
#   - Credit Scoring Systems (e.g., UK 0-999 vs US 300-850)
#   - Baseline Interest Rates
#   - Income Distribution Shapes (skew, median, spread)
#   - Loan Term Conventions
#
# HARDENED: Now applies FULL DISTRIBUTION OVERRIDES per region,
# not just currency multipliers. India's income distribution
# shape is fundamentally different from the US.
# =====================================================

import math
from typing import Dict, Any

# ─────────────────────────────────────────────────
# REGIONAL ECONOMIC MATRIX
# ─────────────────────────────────────────────────
REGIONS = {
    "US": {
        "name": "United States",
        "currency_multiplier": 1.0,
        "credit_score_bounds": {"min": 300, "max": 850},
        "credit_score_system": "FICO",
        "interest_rate_baseline": 12.35,
        "interest_rate_multiplier": 1.0,
        "median_income_annual": 49500,
        "loan_term_common": [36, 60],
    },
    "UK": {
        "name": "United Kingdom",
        "currency_multiplier": 0.78,
        "credit_score_bounds": {"min": 0, "max": 999},
        "credit_score_system": "Experian",
        "interest_rate_baseline": 6.5,
        "interest_rate_multiplier": 0.53,
        "median_income_annual": 31772,
        "loan_term_common": [24, 60],
    },
    "EU": {
        "name": "European Union",
        "currency_multiplier": 0.92,
        "credit_score_bounds": {"min": 0, "max": 100},
        "credit_score_system": "SCHUFA",
        "interest_rate_baseline": 4.2,
        "interest_rate_multiplier": 0.34,
        "median_income_annual": 44000,
        "loan_term_common": [24, 120],
    },
    "IN": {
        "name": "India",
        "currency_multiplier": 83.0 * 0.3,
        "credit_score_bounds": {"min": 300, "max": 900},
        "credit_score_system": "CIBIL",
        "interest_rate_baseline": 18.5,
        "interest_rate_multiplier": 1.5,
        "median_income_annual": 600000,  # INR
        "loan_term_common": [12, 84],
    },
    "JP": {
        "name": "Japan",
        "currency_multiplier": 150.0,
        "credit_score_bounds": {"min": 0, "max": 1000},
        "credit_score_system": "JICC",
        "interest_rate_baseline": 1.5,
        "interest_rate_multiplier": 0.12,
        "median_income_annual": 4890000,  # JPY
        "loan_term_common": [60, 360],
    },
    "AU": {
        "name": "Australia",
        "currency_multiplier": 1.5,
        "credit_score_bounds": {"min": 0, "max": 1200},
        "credit_score_system": "Equifax",
        "interest_rate_baseline": 7.5,
        "interest_rate_multiplier": 0.61,
        "median_income_annual": 65000,
        "loan_term_common": [36, 60],
    },
    "BR": {
        "name": "Brazil",
        "currency_multiplier": 5.0,
        "credit_score_bounds": {"min": 0, "max": 1000},
        "credit_score_system": "Serasa",
        "interest_rate_baseline": 30.0,
        "interest_rate_multiplier": 2.43,
        "median_income_annual": 36000,  # BRL
        "loan_term_common": [12, 48],
    },
}

# ─────────────────────────────────────────────────
# REGIONAL DISTRIBUTION OVERRIDES
# ─────────────────────────────────────────────────
# Full replacement distribution parameters per region.
# Key = variable suffix (matches any entity prefix).
# Values override the base schema's distribution params.
REGIONAL_DISTRIBUTION_OVERRIDES = {
    "UK": {
        "salary_base": {"family": "lognormal", "params": {"mu": 10.36, "sigma": 0.58}},
        "gross_amount": {"family": "lognormal", "params": {"mu": 7.89, "sigma": 0.58}},
        "credit_score": {"family": "normal", "params": {"mean": 580, "std": 180}},
        "interest_rate": {"family": "normal", "params": {"mean": 6.5, "std": 2.5}},
    },
    "IN": {
        "salary_base": {"family": "lognormal", "params": {"mu": 13.0, "sigma": 0.85}},
        "gross_amount": {"family": "lognormal", "params": {"mu": 10.53, "sigma": 0.85}},
        "credit_score": {"family": "normal", "params": {"mean": 650, "std": 90}},
        "interest_rate": {"family": "normal", "params": {"mean": 18.5, "std": 5.0}},
    },
    "EU": {
        "salary_base": {"family": "lognormal", "params": {"mu": 10.69, "sigma": 0.55}},
        "gross_amount": {"family": "lognormal", "params": {"mu": 8.22, "sigma": 0.55}},
        "credit_score": {"family": "normal", "params": {"mean": 72, "std": 15}},
        "interest_rate": {"family": "normal", "params": {"mean": 4.2, "std": 1.8}},
    },
    "JP": {
        "salary_base": {"family": "lognormal", "params": {"mu": 15.4, "sigma": 0.45}},
        "gross_amount": {"family": "lognormal", "params": {"mu": 12.93, "sigma": 0.45}},
        "credit_score": {"family": "normal", "params": {"mean": 650, "std": 180}},
        "interest_rate": {"family": "normal", "params": {"mean": 1.5, "std": 0.5}},
    },
    "AU": {
        "salary_base": {"family": "lognormal", "params": {"mu": 11.08, "sigma": 0.60}},
        "gross_amount": {"family": "lognormal", "params": {"mu": 8.61, "sigma": 0.60}},
        "credit_score": {"family": "normal", "params": {"mean": 750, "std": 200}},
        "interest_rate": {"family": "normal", "params": {"mean": 7.5, "std": 3.0}},
    },
    "BR": {
        "salary_base": {"family": "lognormal", "params": {"mu": 10.49, "sigma": 0.80}},
        "gross_amount": {"family": "lognormal", "params": {"mu": 8.02, "sigma": 0.80}},
        "credit_score": {"family": "normal", "params": {"mean": 600, "std": 150}},
        "interest_rate": {"family": "normal", "params": {"mean": 30.0, "std": 10.0}},
    },
}


def apply_localization(contract: Dict[str, Any]) -> Dict[str, Any]:
    """
    Applies the regional economic matrix to the contract distributions
    and constraints. HARDENED: Now applies full distribution overrides
    for key variables, not just multipliers.
    """
    region = contract.get("intent", {}).get("region", "US").upper()
    if region not in REGIONS:
        region = "US"  # Fallback

    matrix = REGIONS[region]

    # Phase 1: Apply FULL distribution overrides for key variables
    # These replace the US-centric distribution shapes entirely.
    overrides = REGIONAL_DISTRIBUTION_OVERRIDES.get(region, {})
    for var_name, dist in contract.get("distributions", {}).items():
        name_lower = var_name.lower()
        # Check if any override suffix matches this variable
        for suffix, override_dist in overrides.items():
            if name_lower.endswith(suffix) or suffix in name_lower:
                # Full replacement of distribution params
                dist["params"] = dict(override_dist["params"])
                if "family" in override_dist:
                    dist["family"] = override_dist["family"]
                break
        else:
            # No override matched — apply multiplier-based scaling
            _localize_distribution(var_name, dist, matrix, contract.get("variables", {}))

    # Phase 2: Apply constraint scaling
    for var_name, constraint in contract.get("constraints", {}).items():
        _localize_constraint(var_name, constraint, matrix)

    return contract


def _localize_distribution(var_name: str, dist: Dict[str, Any], matrix: Dict[str, Any], variables: Dict[str, Any]) -> None:
    """Multiplier-based scaling for variables without full overrides."""
    name_lower = var_name.lower()
    params = dist.get("params", {})
    bounds = dist.get("bounds", {})

    # Scale inner distribution bounds if they exist
    if bounds:
        _localize_constraint(var_name, bounds, matrix)

    # 1. Credit Scores
    if "credit_score" in name_lower or "fico" in name_lower or "cibil" in name_lower:
        if "mean" in params:
            us_range = 850.0 - 300.0
            pct = (params["mean"] - 300.0) / us_range
            pct = max(0.0, min(1.0, pct))
            reg_min = matrix["credit_score_bounds"]["min"]
            reg_max = matrix["credit_score_bounds"]["max"]
            params["mean"] = reg_min + pct * (reg_max - reg_min)

            if "std" in params:
                params["std"] = params["std"] * ((reg_max - reg_min) / us_range)

    # 2. Monetary Amounts
    elif _is_monetary(name_lower):
        mult = matrix["currency_multiplier"]
        if "mean" in params: params["mean"] *= mult
        if "std" in params: params["std"] *= mult
        if "loc" in params: params["loc"] *= mult
        if "scale" in params: params["scale"] *= mult
        if "mu" in params:
            # For lognormal, mu is log(mean). E[X] = exp(mu + sigma^2/2)
            # Multiplying the variable by M adds ln(M) to mu.
            if mult > 0:
                params["mu"] += math.log(mult)

    # 3. Interest Rates
    elif "interest_rate" in name_lower or name_lower.endswith("_rate"):
        mult = matrix["interest_rate_multiplier"]
        if "mean" in params: params["mean"] *= mult
        if "std" in params: params["std"] *= mult
        if "loc" in params: params["loc"] *= mult
        if "scale" in params: params["scale"] *= mult


def _localize_constraint(var_name: str, constraint: Dict[str, Any], matrix: Dict[str, Any]) -> None:
    """Scales min/max bounds based on the regional matrix."""
    name_lower = var_name.lower()

    # 1. Credit Scores
    if "credit_score" in name_lower or "fico" in name_lower or "cibil" in name_lower:
        us_range = 850.0 - 300.0
        reg_min = matrix["credit_score_bounds"]["min"]
        reg_max = matrix["credit_score_bounds"]["max"]

        if "min" in constraint:
            pct = (constraint["min"] - 300.0) / us_range
            constraint["min"] = reg_min + max(0.0, min(1.0, pct)) * (reg_max - reg_min)

        if "max" in constraint:
            pct = (constraint["max"] - 300.0) / us_range
            constraint["max"] = reg_min + max(0.0, min(1.0, pct)) * (reg_max - reg_min)

    # 2. Monetary Amounts
    elif _is_monetary(name_lower):
        mult = matrix["currency_multiplier"]
        if "min" in constraint: constraint["min"] *= mult
        if "max" in constraint: constraint["max"] *= mult


def _is_monetary(var_name: str) -> bool:
    money_keywords = [
        "amount", "balance", "salary", "income", "price", "cost",
        "fee", "premium", "payment", "gross", "net", "emi",
        "principal", "revenue", "expense", "deductible", "limit",
        "debit", "credit", "invoice", "payout", "deposit",
        "withdrawal", "margin", "profit", "loss", "wage",
    ]
    return any(kw in var_name for kw in money_keywords)
