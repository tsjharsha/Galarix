# =====================================================
# REGIONAL BENCHMARK REGISTRY
# =====================================================
# Real-world benchmarks per region that the trust engine
# validates generated data against.
#
# Separate from localization_engine.py distribution
# overrides: those define HOW to generate, this defines
# WHAT the generated data should look like.
#
# Sources:
#   US: Federal Reserve, BLS, FICO
#   UK: Bank of England, ONS, Experian
#   EU: ECB, Eurostat, SCHUFA
#   IN: RBI, PLFS, CIBIL/TransUnion
#   JP: BOJ, JICC, Statistics Bureau
#   AU: RBA, ABS, Equifax
#   BR: BCB, IBGE, Serasa
# =====================================================

from typing import Any, Dict, Optional, Tuple


REGIONAL_BENCHMARKS: Dict[str, Dict[str, Any]] = {

    "US": {
        "name": "United States",
        "currency": "USD",
        "currency_symbol": "$",
        "central_bank": "Federal Reserve",
        "credit_score": {
            "system": "FICO",
            "range": (300, 850),
            "national_mean": 717,
            "source": "FICO Score Distribution Report",
            "source_url": "https://www.fico.com/blogs/average-u-s-fico-score",
        },
        "interest_rate": {
            "personal_loan_mean": 12.35,
            "mortgage_30yr_mean": 6.8,
            "credit_card_mean": 20.7,
            "source": "Federal Reserve H.15 Selected Interest Rates",
        },
        "income": {
            "median_annual": 49500,
            "mean_annual": 67920,
            "source": "U.S. Bureau of Labor Statistics — OEWS May 2024",
        },
    },

    "UK": {
        "name": "United Kingdom",
        "currency": "GBP",
        "currency_symbol": "£",
        "central_bank": "Bank of England",
        "credit_score": {
            "system": "Experian",
            "range": (0, 999),
            "national_mean": 580,
            "source": "Experian UK Credit Score Distribution",
        },
        "interest_rate": {
            "personal_loan_mean": 6.5,
            "mortgage_mean": 4.5,
            "source": "Bank of England Bankstats — Effective Interest Rates",
        },
        "income": {
            "median_annual": 31772,
            "source": "ONS Annual Survey of Hours and Earnings (ASHE) 2024",
        },
    },

    "EU": {
        "name": "European Union",
        "currency": "EUR",
        "currency_symbol": "€",
        "central_bank": "European Central Bank",
        "credit_score": {
            "system": "SCHUFA",
            "range": (0, 100),
            "national_mean": 72,
            "source": "SCHUFA Kredit-Kompass Report",
        },
        "interest_rate": {
            "personal_loan_mean": 4.2,
            "mortgage_mean": 3.5,
            "source": "ECB MFI Interest Rate Statistics",
        },
        "income": {
            "median_annual": 44000,
            "source": "Eurostat Structure of Earnings Survey (SES)",
        },
    },

    "IN": {
        "name": "India",
        "currency": "INR",
        "currency_symbol": "₹",
        "central_bank": "Reserve Bank of India",
        "credit_score": {
            "system": "CIBIL",
            "range": (300, 900),
            "national_mean": 650,
            "source": "CIBIL TransUnion India Credit Landscape Report",
        },
        "interest_rate": {
            "personal_loan_mean": 18.5,
            "home_loan_mean": 8.5,
            "repo_rate": 6.5,
            "source": "RBI Master Direction — Interest Rate on Advances",
        },
        "income": {
            "median_annual": 600000,
            "source": "Periodic Labour Force Survey (PLFS), Ministry of Statistics, India",
        },
    },

    "JP": {
        "name": "Japan",
        "currency": "JPY",
        "currency_symbol": "¥",
        "central_bank": "Bank of Japan",
        "credit_score": {
            "system": "JICC",
            "range": (0, 1000),
            "national_mean": 650,
            "source": "JICC (Japan Credit Information Reference Center)",
        },
        "interest_rate": {
            "personal_loan_mean": 1.5,
            "mortgage_mean": 0.5,
            "source": "BOJ Financial System Report — Lending Rate Data",
        },
        "income": {
            "median_annual": 4890000,
            "source": "Statistics Bureau of Japan — Labour Force Survey",
        },
    },

    "AU": {
        "name": "Australia",
        "currency": "AUD",
        "currency_symbol": "A$",
        "central_bank": "Reserve Bank of Australia",
        "credit_score": {
            "system": "Equifax",
            "range": (0, 1200),
            "national_mean": 750,
            "source": "Equifax Australia Credit Scorecard",
        },
        "interest_rate": {
            "personal_loan_mean": 7.5,
            "mortgage_mean": 6.0,
            "source": "RBA Statistical Tables — Lending Rates",
        },
        "income": {
            "median_annual": 65000,
            "source": "ABS Employee Earnings and Hours Survey",
        },
    },

    "BR": {
        "name": "Brazil",
        "currency": "BRL",
        "currency_symbol": "R$",
        "central_bank": "Banco Central do Brasil",
        "credit_score": {
            "system": "Serasa",
            "range": (0, 1000),
            "national_mean": 600,
            "source": "Serasa Experian Score Distribution — Brazil",
        },
        "interest_rate": {
            "personal_loan_mean": 30.0,
            "mortgage_mean": 10.0,
            "selic_rate": 13.75,
            "source": "BCB — SGS Interest Rate Statistics",
        },
        "income": {
            "median_annual": 36000,
            "source": "IBGE (Brazilian Institute of Geography and Statistics) — PNAD",
        },
    },
}


def get_benchmarks(region: str) -> Dict[str, Any]:
    """Get benchmarks for a region, fallback to US."""
    return REGIONAL_BENCHMARKS.get(region.upper(), REGIONAL_BENCHMARKS["US"])


def get_credit_range(region: str) -> Tuple[int, int]:
    """Get the valid credit score range for a region."""
    bm = get_benchmarks(region)
    return bm["credit_score"]["range"]


def get_credit_system(region: str) -> str:
    """Get the credit scoring system name for a region."""
    bm = get_benchmarks(region)
    return bm["credit_score"]["system"]


def get_currency_symbol(region: str) -> str:
    """Get the currency symbol for a region."""
    bm = get_benchmarks(region)
    return bm.get("currency_symbol", "$")


def get_rate_baseline(region: str) -> float:
    """Get the personal loan interest rate baseline for a region."""
    bm = get_benchmarks(region)
    return bm["interest_rate"]["personal_loan_mean"]


def get_income_median(region: str) -> float:
    """Get the median annual income for a region."""
    bm = get_benchmarks(region)
    return bm["income"]["median_annual"]


def list_regions() -> list:
    """List all supported region codes."""
    return list(REGIONAL_BENCHMARKS.keys())
