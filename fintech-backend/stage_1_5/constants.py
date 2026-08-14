# =====================================================
# STAGE 1.5 CONSTANTS — Defaults, valid values, thresholds
# =====================================================
# Everything Stage 1.5 needs to normalize, validate,
# and guarantee contract correctness.
# =====================================================

from typing import Dict, List, Set

# =====================================================
# SUPPORTED ENTITIES (includes "generic" fallback)
# =====================================================
SUPPORTED_ENTITIES: Set[str] = {
    "credit_card_activity",
    "payroll",
    "saas_billing",
    "investment_statement",
    "insurance_claims",
    "loans",
    "bank_account_statement",
    "wire_transfers",
    "atm_withdrawals",
    "mortgage_records",
    "buy_now_pay_later",
    "kyc_records",
    "aml_transaction_alerts",
    "crypto_trading_log",
    "forex_transactions",
    "options_trading",
    "expense_reports",
    "tax_records_w2",
    "pnl_statement",
    "invoice_financing",
    "generic",
    "multi_entity",
}

# =====================================================
# VALID VALUES — Enumerated allowed values for intent fields
# =====================================================
VALID_SCALES = {"tiny", "small", "medium", "large", "massive"}
VALID_RISKS = {"low", "medium", "high", "extreme"}
VALID_FREQUENCIES = {"daily", "weekly", "monthly", "quarterly", "yearly"}

# =====================================================
# DEFAULTS — Used when fields are missing or invalid
# =====================================================
DEFAULTS = {
    "entity": "generic",
    "scale": "medium",
    "risk": "low",
    "categories": ["general"],
    "frequency": "monthly",
    "confidence": 0.0,
    "source": "prompt",
}

# =====================================================
# SYNONYM MAPS — Normalize messy user language
# =====================================================
SCALE_SYNONYMS: Dict[str, str] = {
    # → "small"
    "small": "small", "few": "small",
    "little": "small", "minimal": "small",
    "compact": "small", "narrow": "small", "limited": "small",
    "basic": "small", "slim": "small",
    # → "tiny"
    "tiny": "tiny", "micro": "tiny", "mini": "tiny",
    # → "medium"
    "medium": "medium", "moderate": "medium", "average": "medium",
    "normal": "medium", "standard": "medium", "typical": "medium",
    "regular": "medium", "mid": "medium", "midsize": "medium",
    "middle": "medium", "default": "medium",
    # → "large"
    "large": "large", "big": "large", "huge": "large",
    "extensive": "large", "enterprise": "large",
    "bulk": "large", "heavy": "large", "major": "large",
    "significant": "large", "substantial": "large",
    "comprehensive": "large", "wide": "large", "broad": "large",
    # → "massive"
    "massive": "massive", "enormous": "massive", "gigantic": "massive",
    "mega": "massive", "colossal": "massive", "immense": "massive",
}

RISK_SYNONYMS: Dict[str, str] = {
    # → "low"
    "low": "low", "safe": "low", "conservative": "low",
    "stable": "low", "secure": "low", "reliable": "low",
    "standard": "low", "normal": "low", "typical": "low",
    "minimal": "low", "clean": "low",
    # → "medium"
    "medium": "medium", "moderate": "medium", "balanced": "medium",
    "mixed": "medium", "average": "medium",
    # → "high"
    "high": "high", "risky": "high", "volatile": "high",
    "aggressive": "high", "dangerous": "high",
    "fraudulent": "high", "suspicious": "high",
    "anomalous": "high",
    "premium": "high", "luxury": "high", "expensive": "high",
    # → "extreme"
    "extreme": "extreme", "catastrophic": "extreme", "meltdown": "extreme",
    "collapse": "extreme", "crisis": "extreme", "devastating": "extreme",
}

FREQUENCY_SYNONYMS: Dict[str, str] = {
    # → "daily"
    "daily": "daily", "everyday": "daily", "per day": "daily",
    "each day": "daily", "every day": "daily", "day": "daily",
    # → "weekly"
    "weekly": "weekly", "per week": "weekly",
    "each week": "weekly", "every week": "weekly", "week": "weekly",
    # → "monthly"
    "monthly": "monthly", "per month": "monthly",
    "each month": "monthly", "every month": "monthly", "month": "monthly",
    # → "quarterly"
    "quarterly": "quarterly", "per quarter": "quarterly",
    "each quarter": "quarterly", "every quarter": "quarterly",
    "3 months": "quarterly", "three months": "quarterly",
    # → "yearly"
    "yearly": "yearly", "annual": "yearly", "annually": "yearly",
    "per year": "yearly", "each year": "yearly", "every year": "yearly",
    "12 months": "yearly", "year": "yearly",
}



# =====================================================
# CONTRACT STRUCTURE — Required keys & types
# =====================================================
REQUIRED_CONTRACT_KEYS = [
    "entity", "entities", "intent", "variables",
    "distributions", "dependencies", "constraints", "meta",
]

REQUIRED_INTENT_KEYS = ["scale", "risk", "categories", "frequency"]

REQUIRED_META_KEYS = ["confidence", "source", "is_multi"]