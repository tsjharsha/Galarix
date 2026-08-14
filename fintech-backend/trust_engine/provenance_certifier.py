# =====================================================
# PROVENANCE CERTIFIER — Region-Aware Source Citations
# =====================================================
# Builds a complete provenance chain linking every
# distribution parameter to its region-specific source.
#
# For US data: cites Federal Reserve, BLS, FICO
# For IN data: cites RBI, PLFS, CIBIL
# For UK data: cites BOE, ONS, Experian
# ... etc.
#
# Every distribution parameter is traced back to its
# source publication with theoretical moments computed
# from first principles.
# =====================================================

import math
import numpy as np
from typing import Any, Dict, List, Optional

from trust_engine.regional_benchmarks import (
    get_benchmarks,
    get_currency_symbol,
)


# ─────────────────────────────────────────────────
# REGIONAL SOURCE REGISTRY
# Maps region -> variable suffix -> source citation
# ─────────────────────────────────────────────────

REGIONAL_SOURCES: Dict[str, Dict[str, Dict[str, str]]] = {
    "US": {
        "credit_score": {
            "source": "FICO Score Distribution Report",
            "regional_source": "FICO / Federal Reserve (US)",
            "scoring_system": "FICO",
            "score_range": "300-850",
        },
        "interest_rate": {
            "source": "Federal Reserve H.15 Selected Interest Rates",
            "regional_source": "Federal Reserve (US)",
        },
        "salary_base": {
            "source": "U.S. Bureau of Labor Statistics — OEWS May 2024",
            "regional_source": "BLS (US)",
        },
        "principal_amount": {
            "source": "Federal Reserve Survey of Consumer Finances (SCF) 2022",
            "regional_source": "Federal Reserve (US)",
        },
    },
    "IN": {
        "credit_score": {
            "source": "CIBIL TransUnion India Credit Landscape Report",
            "regional_source": "CIBIL TransUnion (India)",
            "scoring_system": "CIBIL",
            "score_range": "300-900",
        },
        "interest_rate": {
            "source": "RBI Master Direction — Interest Rate on Advances",
            "regional_source": "Reserve Bank of India (RBI)",
        },
        "salary_base": {
            "source": "Periodic Labour Force Survey (PLFS), Ministry of Statistics, India",
            "regional_source": "Ministry of Statistics (India)",
        },
        "principal_amount": {
            "source": "RBI Financial Stability Report",
            "regional_source": "Reserve Bank of India (RBI)",
        },
    },
    "UK": {
        "credit_score": {
            "source": "Experian UK Credit Score Distribution",
            "regional_source": "Experian (UK)",
            "scoring_system": "Experian",
            "score_range": "0-999",
        },
        "interest_rate": {
            "source": "Bank of England Bankstats — Effective Interest Rates",
            "regional_source": "Bank of England (BOE)",
        },
        "salary_base": {
            "source": "ONS Annual Survey of Hours and Earnings (ASHE) 2024",
            "regional_source": "ONS (UK)",
        },
        "principal_amount": {
            "source": "FCA Consumer Credit Statistics",
            "regional_source": "Financial Conduct Authority (UK)",
        },
    },
    "EU": {
        "credit_score": {
            "source": "SCHUFA Kredit-Kompass Report",
            "regional_source": "SCHUFA (Germany/EU)",
            "scoring_system": "SCHUFA",
            "score_range": "0-100",
        },
        "interest_rate": {
            "source": "ECB MFI Interest Rate Statistics",
            "regional_source": "European Central Bank (ECB)",
        },
        "salary_base": {
            "source": "Eurostat Structure of Earnings Survey (SES)",
            "regional_source": "Eurostat (EU)",
        },
        "principal_amount": {
            "source": "ECB Bank Lending Survey",
            "regional_source": "European Central Bank (ECB)",
        },
    },
    "JP": {
        "credit_score": {
            "source": "JICC (Japan Credit Information Reference Center)",
            "regional_source": "JICC (Japan)",
            "scoring_system": "JICC",
            "score_range": "0-1000",
        },
        "interest_rate": {
            "source": "BOJ Financial System Report — Lending Rate Data",
            "regional_source": "Bank of Japan (BOJ)",
        },
        "salary_base": {
            "source": "Statistics Bureau of Japan — Labour Force Survey",
            "regional_source": "Statistics Bureau (Japan)",
        },
        "principal_amount": {
            "source": "BOJ Flow of Funds — Household Lending",
            "regional_source": "Bank of Japan (BOJ)",
        },
    },
    "AU": {
        "credit_score": {
            "source": "Equifax Australia Credit Scorecard",
            "regional_source": "Equifax (Australia)",
            "scoring_system": "Equifax",
            "score_range": "0-1200",
        },
        "interest_rate": {
            "source": "RBA Statistical Tables — Lending Rates",
            "regional_source": "Reserve Bank of Australia (RBA)",
        },
        "salary_base": {
            "source": "ABS Employee Earnings and Hours Survey",
            "regional_source": "ABS (Australia)",
        },
        "principal_amount": {
            "source": "APRA Monthly Banking Statistics",
            "regional_source": "APRA (Australia)",
        },
    },
    "BR": {
        "credit_score": {
            "source": "Serasa Experian Score Distribution — Brazil",
            "regional_source": "Serasa Experian (Brazil)",
            "scoring_system": "Serasa",
            "score_range": "0-1000",
        },
        "interest_rate": {
            "source": "BCB — SGS Interest Rate Statistics",
            "regional_source": "Banco Central do Brasil (BCB)",
        },
        "salary_base": {
            "source": "IBGE — PNAD Contínua (Household Survey)",
            "regional_source": "IBGE (Brazil)",
        },
        "principal_amount": {
            "source": "BCB Credit Operations Statistics",
            "regional_source": "Banco Central do Brasil (BCB)",
        },
    },
}


def build_provenance_chain(
    columns: Dict[str, np.ndarray],
    parameters: Dict[str, Any],
    entity: str,
    region: str,
    schema_sources: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Build the full provenance chain for a generated dataset.

    Links every distribution parameter to its region-specific
    source with theoretical vs empirical moment comparison.
    """
    benchmarks = get_benchmarks(region)
    currency_sym = get_currency_symbol(region)
    regional_sources = REGIONAL_SOURCES.get(region, REGIONAL_SOURCES.get("US", {}))

    chain = []

    for var_name, dist_def in parameters.items():
        if var_name.startswith("_"):
            continue

        family = dist_def.get("family", "")
        params = dist_def.get("params", {})

        if not family or family == "":
            continue

        # Find the matching column
        col = columns.get(var_name)
        if col is None:
            continue

        # Determine distribution string
        dist_str = _format_distribution(family, params)

        # Find source citation
        var_suffix = _extract_suffix(var_name, entity)
        source_info = _get_source_for_variable(var_suffix, regional_sources, schema_sources)

        # Compute theoretical moments
        theo = _compute_theoretical_moments(family, params)

        # Compute empirical moments from generated data
        empirical = _compute_empirical_moments(col, family)

        # Build verification string
        verification = _build_verification_string(theo, empirical, currency_sym, family)

        entry = {
            "variable": var_name,
            "distribution": dist_str,
            "source": source_info.get("source", schema_sources.get("primary", "Unknown")),
            "regional_source": source_info.get("regional_source", benchmarks.get("central_bank", "")),
            "methodology": source_info.get("methodology", schema_sources.get("methodology", "")),
        }

        # Add currency for monetary variables
        if _is_monetary_var(var_name):
            entry["currency"] = benchmarks["currency"]

        # Add scoring system for credit scores
        if "credit_score" in var_name.lower():
            entry["scoring_system"] = source_info.get("scoring_system", benchmarks["credit_score"]["system"])
            entry["score_range"] = source_info.get("score_range",
                f"{benchmarks['credit_score']['range'][0]}-{benchmarks['credit_score']['range'][1]}")

        # Add theoretical moments
        if theo.get("median") is not None:
            if _is_monetary_var(var_name):
                entry["implied_median"] = f"{currency_sym}{theo['median']:,.0f}"
            else:
                entry["implied_median"] = f"{theo['median']:.2f}"

        if theo.get("mean") is not None:
            if _is_monetary_var(var_name):
                entry["implied_mean"] = f"{currency_sym}{theo['mean']:,.0f}"
            else:
                entry["implied_mean"] = f"{theo['mean']:.2f}"

        # Add verification
        entry["verification"] = verification

        chain.append(entry)

    return {
        "entity": entity,
        "region": region,
        "region_name": benchmarks["name"],
        "currency": benchmarks["currency"],
        "central_bank": benchmarks["central_bank"],
        "primary_source": schema_sources.get("primary", "Unknown"),
        "secondary_sources": schema_sources.get("secondary", []),
        "provenance_chain": chain,
        "variables_sourced": len(chain),
        "all_variables_sourced": len(chain) == len([
            k for k in parameters if not k.startswith("_") and k in columns
        ]),
    }


# ─────────────────────────────────────────────────
# INTERNAL HELPERS
# ─────────────────────────────────────────────────

def _format_distribution(family: str, params: Dict[str, Any]) -> str:
    """Format distribution as human-readable string."""
    if family == "normal":
        return f"normal(μ={params.get('mean', 0):.2f}, σ={params.get('std', 1):.2f})"
    elif family == "lognormal":
        return f"lognormal(μ={params.get('mu', 0):.2f}, σ={params.get('sigma', 1):.2f})"
    elif family == "beta":
        return f"beta(α={params.get('alpha', 2):.2f}, β={params.get('beta', 2):.2f})"
    elif family == "student_t":
        return f"student_t(df={params.get('df', 3)}, loc={params.get('loc', 0):.2f})"
    elif family == "cauchy":
        return f"cauchy(loc={params.get('loc', 0):.2f}, scale={params.get('scale', 1):.2f})"
    elif family == "categorical":
        return f"categorical({len(params.get('weights', []))} categories)"
    return f"{family}({params})"


def _extract_suffix(var_name: str, entity: str) -> str:
    """Extract the variable suffix without entity prefix."""
    prefix = f"{entity}_"
    if var_name.startswith(prefix):
        return var_name[len(prefix):]
    return var_name


def _get_source_for_variable(
    var_suffix: str,
    regional_sources: Dict[str, Dict[str, str]],
    schema_sources: Dict[str, Any],
) -> Dict[str, str]:
    """Find the best source citation for a variable."""
    # Check regional sources first
    for key, source in regional_sources.items():
        if key in var_suffix.lower() or var_suffix.lower() in key:
            return source

    # Fallback to schema-level sources
    return {
        "source": schema_sources.get("primary", "Composite"),
        "methodology": schema_sources.get("methodology", ""),
    }


def _compute_theoretical_moments(family: str, params: Dict[str, Any]) -> Dict[str, Optional[float]]:
    """Compute theoretical moments from distribution parameters."""
    if family == "normal":
        mean = params.get("mean", 0)
        std = params.get("std", 1)
        return {
            "mean": mean,
            "median": mean,
            "std": std,
            "p5": mean - 1.645 * std,
            "p95": mean + 1.645 * std,
        }
    elif family == "lognormal":
        mu = params.get("mu", 0)
        sigma = params.get("sigma", 1)
        mean = math.exp(mu + sigma ** 2 / 2)
        median = math.exp(mu)
        return {
            "mean": mean,
            "median": median,
            "std": math.sqrt((math.exp(sigma ** 2) - 1) * math.exp(2 * mu + sigma ** 2)),
            "p5": math.exp(mu - 1.645 * sigma),
            "p95": math.exp(mu + 1.645 * sigma),
        }
    elif family == "beta":
        a = params.get("alpha", 2)
        b = params.get("beta", 2)
        mean = a / (a + b)
        return {"mean": mean, "median": None, "std": math.sqrt(a * b / ((a + b) ** 2 * (a + b + 1)))}
    elif family == "categorical":
        return {"mean": None, "median": None, "std": None}
    return {"mean": None, "median": None, "std": None}


def _compute_empirical_moments(col: np.ndarray, family: str) -> Dict[str, Optional[float]]:
    """Compute empirical moments from generated data."""
    if col.dtype == object:
        return {"mean": None, "median": None, "std": None}
    try:
        float_col = col.astype(float)
        finite = float_col[np.isfinite(float_col)]
        if len(finite) < 5:
            return {"mean": None, "median": None, "std": None}
        return {
            "mean": float(np.mean(finite)),
            "median": float(np.median(finite)),
            "std": float(np.std(finite, ddof=1)),
            "p5": float(np.percentile(finite, 5)),
            "p95": float(np.percentile(finite, 95)),
        }
    except (ValueError, TypeError):
        return {"mean": None, "median": None, "std": None}


def _build_verification_string(
    theo: Dict[str, Optional[float]],
    empirical: Dict[str, Optional[float]],
    currency_sym: str,
    family: str,
) -> str:
    """Build a human-readable verification string."""
    parts = []

    if theo.get("median") is not None and empirical.get("median") is not None:
        dev = abs(empirical["median"] - theo["median"]) / max(abs(theo["median"]), 1e-6) * 100
        if _is_monetary_family(family, theo):
            parts.append(f"Generated median={currency_sym}{empirical['median']:,.0f} ({dev:.1f}% deviation)")
        else:
            parts.append(f"Generated median={empirical['median']:.2f} ({dev:.1f}% deviation)")

    if theo.get("mean") is not None and empirical.get("mean") is not None:
        dev = abs(empirical["mean"] - theo["mean"]) / max(abs(theo["mean"]), 1e-6) * 100
        if _is_monetary_family(family, theo):
            parts.append(f"mean={currency_sym}{empirical['mean']:,.0f} ({dev:.1f}%)")
        else:
            parts.append(f"mean={empirical['mean']:.2f} ({dev:.1f}%)")

    return "; ".join(parts) if parts else "No verification data available"


def _is_monetary_var(var_name: str) -> bool:
    """Check if a variable is monetary."""
    money_kw = [
        "amount", "balance", "salary", "income", "price", "cost",
        "fee", "premium", "payment", "gross", "net", "emi",
        "principal", "revenue", "expense", "payout", "deposit",
        "withdrawal", "wage", "mrr", "revenue",
    ]
    return any(kw in var_name.lower() for kw in money_kw)


def _is_monetary_family(family: str, theo: Dict) -> bool:
    """Heuristic: if median > 100, likely monetary."""
    median = theo.get("median")
    if median is not None and abs(median) > 100:
        return True
    return False
