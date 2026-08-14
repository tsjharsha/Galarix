# =====================================================
# STAGE 1 CONSTANTS — Entity Keywords, Scoring, Signals
# =====================================================
# This is the "brain" of keyword-based entity resolution.
# Every keyword is weighted: domain-specific terms score higher,
# generic financial terms score lower to avoid false positives.
#
# FIX: Extended from 6 base entities to 20 comprehensive
# financial entities covering RegTech, Capital Markets, and
# Corporate Finance, meeting investor-grade requirements.
# =====================================================

from typing import Dict, List, Set

# =====================================================
# SUPPORTED ENTITIES
# =====================================================
SUPPORTED_ENTITIES: Set[str] = {
    # Original
    "credit_card_activity",
    "payroll",
    "saas_billing",
    "investment_statement",
    "insurance_claims",
    "loans",
    # Banking & Payments
    "bank_account_statement",
    "wire_transfers",
    "atm_withdrawals",
    # Alternative Lending
    "mortgage_records",
    "buy_now_pay_later",
    # RegTech & Compliance
    "kyc_records",
    "aml_transaction_alerts",
    # Capital Markets
    "crypto_trading_log",
    "forex_transactions",
    "options_trading",
    # Corporate Finance
    "expense_reports",
    "tax_records_w2",
    "pnl_statement",
    "invoice_financing",
}

DEFAULT_FALLBACK_ENTITY = "generic"

# =====================================================
# ENTITY KEYWORDS — {entity: {keyword: weight}}
# =====================================================
ENTITY_KEYWORDS: Dict[str, Dict[str, float]] = {

    # ── Original Entities ──
    "credit_card_activity": {
        "credit card": 1.0, "credit cards": 1.0, "card transaction": 1.0,
        "card payment": 1.0, "card spending": 1.0, "swipe": 1.0,
        "pos": 0.9, "plastic": 0.8, "visa": 0.9, "mastercard": 0.9,
        "merchant": 0.9, "merchant category": 1.0, "mcc": 0.9,
        "spending": 0.6, "expenses": 0.6, "purchases": 0.6,
        "shopping": 0.7, "retail": 0.6, "grocery": 0.7,
        "luxury": 0.9, "luxury goods": 1.0, "cash spending": 0.8,
        "dining": 0.7, "restaurant": 0.7, "online shopping": 0.7,
        "card": 0.5, "checkout": 0.6, "refund": 0.5,
    },
    "payroll": {
        "payroll": 1.0, "salary": 1.0, "salaries": 1.0,
        "wages": 1.0, "wage": 1.0, "compensation": 0.9,
        "ctc": 1.0, "cost to company": 1.0,
        "pay slip": 1.0, "payslip": 1.0, "paycheck": 1.0,
        "paycheque": 1.0, "pay stub": 1.0,
        "employee": 0.7, "employees": 0.7, "staff": 0.6,
        "tax deduction": 0.8, "tds": 0.8, "income tax": 0.7,
        "net pay": 0.9, "gross pay": 0.9, "deductions": 0.7,
        "bonus": 0.7, "overtime": 0.7, "hr": 0.5,
    },
    "saas_billing": {
        "saas": 1.0, "subscription": 0.9, "subscriptions": 0.9,
        "recurring billing": 1.0, "recurring revenue": 1.0,
        "mrr": 1.0, "arr": 1.0, "software license": 1.0,
        "invoice": 0.7, "invoices": 0.7,
        "billing": 0.6, "plan": 0.5, "tier": 0.6,
        "renewal": 0.8, "upgrade": 0.7, "downgrade": 0.7,
        "churn": 0.9, "retention": 0.7, "trial": 0.7,
        "freemium": 0.9, "enterprise plan": 0.9,
        "starter": 0.5, "pro plan": 0.7, "seats": 0.7, "per user": 0.6,
        "software charges": 1.0, "software": 0.6, "monthly charges": 0.7,
    },
    "investment_statement": {
        "investment": 0.9, "investments": 0.9, "portfolio": 1.0,
        "stocks": 1.0, "stock": 0.9, "shares": 0.9,
        "equity": 0.8, "equities": 0.9, "stonks": 0.9,
        "mutual fund": 1.0, "mutual funds": 1.0,
        "sip": 0.9, "etf": 0.9, "brokerage": 0.9, "trading": 0.9,
        "holdings": 0.8, "dividend": 0.9, "dividends": 0.9,
        "buy": 0.4, "sell": 0.4, "market": 0.5, "asset": 0.6,
        "returns": 0.6, "yield": 0.6, "bond": 0.8, "bonds": 0.8,
    },
    "insurance_claims": {
        "insurance": 0.9, "insurance claim": 1.0, "insurance claims": 1.0,
        "claim": 0.7, "claims": 0.7, "policy": 0.7,
        "coverage": 0.8, "underwriting": 1.0, "deductible": 0.9, "premium": 0.7,
        "reimbursement": 0.8, "settlement": 0.7,
        "casualty": 0.9, "accident": 0.7, "damage": 0.6,
        "health insurance": 1.0, "auto insurance": 1.0,
        "property insurance": 1.0, "life insurance": 1.0,
        "claim status": 1.0, "approved": 0.4, "denied": 0.5,
        "loss ratio": 1.0, "naic": 1.0, "severity": 0.7, "fraud indicator": 0.9,
    },
    "loans": {
        "loan": 1.0, "loans": 1.0, "lending": 0.9,
        "borrower": 0.9, "borrowing": 0.8,
        "principal": 0.8, "principal amount": 1.0,
        "emi": 1.0, "equated monthly installment": 1.0,
        "home loan": 0.7, "auto loan": 1.0, "personal loan": 1.0,
        "repay": 0.8, "repayment": 0.9, "installment": 0.7,
        "amortization": 0.9, "debt": 0.7,
        "disbursement": 0.9, "tenure": 0.7, "interest rate": 0.7, 
        "credit score": 0.7, "default": 0.5, "delinquent": 0.8,
    },

    # ── Banking & Payments ──
    "bank_account_statement": {
        "bank account": 1.0, "statement": 0.8, "checking account": 1.0,
        "savings account": 1.0, "account balance": 1.0, "deposit": 0.9,
        "deposits": 0.9, "withdrawal": 0.8, "overdraft": 1.0,
        "ach transfer": 1.0, "direct deposit": 1.0, "available balance": 1.0,
        "checking": 0.8, "savings": 0.7, "bank balance": 1.0,
    },
    "wire_transfers": {
        "wire transfer": 1.0, "ibit": 1.0, "swift code": 1.0, "fedwire": 1.0,
        "international transfer": 1.0, "remittance": 1.0, "cross-border": 0.9,
        "iban": 1.0, "bic": 1.0, "transfer amount": 0.8, "clearing": 0.7,
        "swift": 0.9, "mt103": 1.0, "cross border": 0.9, "settlement": 0.7,
        "correspondent bank": 1.0, "sending money overseas": 1.0,
        "overseas": 0.8, "suppliers": 0.5, "internationally": 0.8,
    },
    "atm_withdrawals": {
        "atm": 1.0, "cash withdrawal": 1.0, "atm fee": 1.0,
        "out of network": 0.9, "cash machine": 1.0, "withdrawal amount": 0.9,
        "cash out": 0.8, "machine": 0.6, "dispensation": 0.9, "interbank": 0.7,
    },

    # ── Alternative Lending ──
    "mortgage_records": {
        "mortgage": 1.0, "escrow": 1.0, "home loan": 1.0, "property value": 0.9,
        "down payment": 0.9, "apr": 0.8, "amortization schedule": 1.0,
        "fixed rate": 0.9, "adjustable rate": 0.9, "arm": 0.7, "refinance": 1.0,
        "ltv": 1.0, "ltv ratio": 1.0, "conforming loan": 1.0, "fha": 0.9,
        "homebuyer": 0.9, "house payment": 0.9, "home ownership": 0.9,
    },
    "buy_now_pay_later": {
        "bnpl": 1.0, "buy now pay later": 1.0, "klarna": 1.0, "affirm": 1.0,
        "afterpay": 1.0, "installments": 0.8, "pay in 4": 1.0, "split payment": 1.0,
        "deferred payment": 0.9, "pay in installments": 1.0,
        "split my purchase": 1.0, "4 payments": 0.9, "pay later": 0.9,
        "installments": 0.9, "iphone": 0.7,
        "splitting": 0.8, "easy payments": 0.9, "over time": 0.7,
        "purchases": 0.5, "pay over time": 0.9,
    },

    # ── RegTech & Compliance ──
    "kyc_records": {
        "kyc": 1.0, "know your customer": 1.0, "identity verification": 1.0,
        "aml check": 0.9, "pep status": 1.0, "politically exposed person": 1.0,
        "sanctions list": 1.0, "risk rating": 0.9, "id verification": 0.9,
        "onboarding risk": 0.9, "ssn matches": 0.8,
        "watchlist": 1.0, "sanctions screening": 1.0, "pep screening": 1.0,
        "customer due diligence": 1.0, "cdd": 1.0, "background check": 0.8,
    },
    "aml_transaction_alerts": {
        "aml": 1.0, "anti money laundering": 1.0, "sar": 1.0, 
        "suspicious activity report": 1.0, "structuring": 1.0, "smurfing": 1.0,
        "transaction monitoring": 1.0, "mlro": 1.0, "flagged transaction": 1.0,
        "high risk jurisdiction": 0.9, "alert threshold": 0.9,
        "suspicious transaction": 1.0, "suspicious": 0.7, "compliance": 0.7,
        "money laundering": 1.0, "flagged": 0.7, "9900": 0.9, "9999": 0.9,
        "depositing": 0.8, "under 10000": 1.0,
        "laundering": 0.9, "flagging": 0.8, "weird money": 0.9, "patterns": 0.5,
        "illegal": 0.8, "illegally": 0.8, "cash": 0.6, "luxury goods": 0.7,
    },

    # ── Capital Markets ──
    "crypto_trading_log": {
        "crypto": 1.0, "cryptocurrency": 1.0, "bitcoin": 1.0, "ethereum": 1.0,
        "blockchain": 0.9, "wallet address": 1.0, "txid": 1.0, "gas fee": 1.0,
        "defi": 1.0, "smart contract": 0.9, "token exchange": 0.9, "binance": 1.0,
        "doge": 1.0, "sol": 0.8, "solana": 1.0, "dex": 1.0, "nft": 0.9,
        "coinbase": 1.0, "uniswap": 1.0, "metamask": 1.0, "btc": 1.0, "eth": 0.9,
    },
    "forex_transactions": {
        "forex": 1.0, "fx": 0.9, "currency pair": 1.0, "exchange rate": 0.9,
        "pip": 1.0, "spread": 0.8, "base currency": 0.9, "quote currency": 0.9,
        "foreign exchange": 1.0, "fx swap": 1.0,
        "eur": 0.8, "usd": 0.5, "gbp": 0.8, "jpy": 0.8, "chf": 0.8,
        "eur/usd": 1.0, "usd/jpy": 1.0, "gbp/usd": 1.0, "spot rate": 0.9,
    },
    "options_trading": {
        "options": 1.0, "call option": 1.0, "put option": 1.0, "strike price": 1.0,
        "expiration date": 0.9, "option premium": 1.0, "implied volatility": 1.0,
        "the greeks": 0.9, "delta": 0.8, "theta": 0.8, "contract multiplier": 0.9,
        "covered call": 1.0, "covered calls": 1.0, "naked put": 1.0, "iron condor": 1.0,
        "0dte": 1.0, "weeklies": 0.8, "leaps": 0.9, "straddle": 1.0, "strangle": 1.0,
        "calls": 0.8, "puts": 0.8, "option chain": 1.0, "spx": 0.8,
        "multi leg": 1.0, "multi-leg": 1.0, "greeks": 0.9, "strategy": 0.5,
        "occ": 0.9, "cleared": 0.5,
    },

    # ── Corporate Finance ──
    "expense_reports": {
        "expense report": 1.0, "t&e": 1.0, "travel and expense": 1.0,
        "corporate expense": 0.9, "reimbursement claim": 0.9, "receipt attached": 0.8,
        "per diem": 1.0, "business travel": 0.9, "concur": 0.9,
        "expense it": 0.9, "expense": 0.7, "expensify": 1.0, "mileage": 0.8,
        "client meeting": 0.7, "travel claim": 0.9, "out of pocket": 0.8,
        "reimbursed": 0.9, "conference": 0.7, "business class": 0.8,
    },
    "tax_records_w2": {
        "w2": 1.0, "w-2": 1.0, "1099": 1.0, "tax withholding": 1.0,
        "irs filing": 1.0, "federal tax": 0.9, "state tax": 0.9, "social security tax": 0.9,
        "medicare tax": 0.9, "taxable income": 0.9,
        "uncle sam": 0.9, "irs": 0.9, "tax return": 0.9, "tax refund": 0.9,
        "form w2": 1.0, "form 1099": 1.0, "tax bracket": 0.9,
        "w 2": 1.0, "paycheck": 0.7, "paychecks": 0.7,
        "federal and state tax": 1.0, "tax taken": 0.9,
    },
    "pnl_statement": {
        "pnl": 1.0, "profit and loss": 1.0, "income statement": 1.0,
        "gross margin": 1.0, "net income": 1.0, "operating expenses": 0.9,
        "ebitda": 1.0, "cogs": 1.0, "cost of goods sold": 1.0,
    },
    "invoice_financing": {
        "invoice financing": 1.0, "factoring": 1.0, "accounts receivable": 1.0,
        "advance rate": 1.0, "discount fee": 1.0, "unpaid invoice": 0.9,
        "trade credit": 0.9, "debtor": 0.8,
        "unpaid invoices": 0.9, "receivables": 0.9, "aging invoices": 1.0,
        "invoice factoring": 1.0, "ar financing": 1.0,
        "unpaid customer invoices": 1.0, "cash now": 0.7, "working capital": 0.8,
    },
}

# =====================================================
# SEMANTIC PHRASES — Indirect language → entity mapping
# =====================================================
SEMANTIC_PHRASES: Dict[str, List[str]] = {
    "credit_card_activity": [
        "what i spent", "where my money goes", "spending habits",
        "buying stuff", "shopping data", "purchase history",
        "blowing cash", "luxury goods spending",
    ],
    "payroll": [
        "how much i earn", "take home pay", "what employees make",
        "salary structure", "pay my team", "compensation data",
    ],
    "saas_billing": [
        "recurring payments", "monthly charges", "software costs",
        "app subscriptions", "service billing", "platform revenue",
    ],
    "investment_statement": [
        "my portfolio", "stock performance", "market data",
        "how my investments are doing", "wealth management",
    ],
    "insurance_claims": [
        "file a claim", "claim history", "policy data",
        "accident report", "damage assessment", "coverage details",
    ],
    "loans": [
        "monthly payments", "pay back", "paying back",
        "how much i owe", "outstanding debt", "loan schedule",
    ],
    "bank_account_statement": [
        "what's in my account", "my bank balance", "money in and out",
        "checking and savings", "whats in my checking", "account activity",
    ],
    "wire_transfers": [
        "sending money overseas", "large money movements", "international payments",
        "cross border settlements", "money to another country",
        "sending large amounts overseas", "moving money internationally",
    ],
    "aml_transaction_alerts": [
        "suspicious money movement", "flagged behaviors", "laundering risk",
        "depositing just under 10000", "suspicious transaction", "flagged by compliance",
        "weird money patterns", "look like laundering", "illegally moving cash",
    ],
    "kyc_records": [
        "customer onboarding checks", "verifying identities", "checking backgrounds",
        "on a watchlist", "screening customers", "identity check",
    ],
    "crypto_trading_log": [
        "crypto trades", "buying bitcoin", "blockchain transfers",
        "trading on a dex", "swapping tokens", "defi trading",
    ],
    "expense_reports": [
        "business trips", "employee spending", "corporate travel claims",
        "need to expense it", "client meeting expenses", "travel reimbursement",
        "need to get reimbursed", "flew to a conference",
    ],
    "pnl_statement": [
        "how the business is doing", "company profits", "losing money",
        "margins are shrinking", "revenue vs costs", "bottom line",
        "how much the company made", "company made vs spent",
    ],
    "buy_now_pay_later": [
        "paying in installments", "klarna payments", "splitting the cost",
        "split my purchase", "pay in 4 payments", "pay over time",
        "splitting online purchases", "paying for stuff over time",
    ],
    "mortgage_records": [
        "paying off the house", "home ownership debt", "housing payments",
        "30 year fixed", "buying a home", "house over 30 years",
        "home ownership debt with amortization",
    ],
    "atm_withdrawals": [
        "cash from the machine", "getting cash out", "quick cash withdrawal",
    ],
    "options_trading": [
        "selling covered calls", "buying puts as hedge", "options strategy",
    ],
    "forex_transactions": [
        "buying euros", "selling dollars", "currency exchange",
    ],
    "tax_records_w2": [
        "uncle sam took from my paycheck", "how much tax was withheld", "tax filing",
    ],
    "invoice_financing": [
        "unpaid invoices aging", "need cash from receivables", "factor my invoices",
    ],
}

# =====================================================
# GENERIC TERMS — Low signal, boost existing scores only
# =====================================================
GENERIC_TERMS: Set[str] = {
    "transaction", "transactions", "data", "records", "generate",
    "create", "make", "simulate", "synthetic", "fake",
    "financial", "finance", "fintech", "money", "payment", "payments",
    "report", "statement", "history", "dataset", "sample",
}

# =====================================================
# SCALE INDICATORS
# =====================================================
SCALE_KEYWORDS: Dict[str, List[str]] = {
    "small": ["small", "few", "little", "minimal", "compact", "narrow", "limited", "basic"],
    "tiny": ["tiny", "micro"],
    "medium": ["medium", "moderate", "average", "normal", "standard", "typical", "regular", "mid", "midsize"],
    "large": ["large", "big", "huge", "extensive", "enterprise", "bulk", "heavy", "major", "significant", "substantial", "comprehensive", "wide", "broad"],
    "massive": ["massive", "enormous", "gigantic", "colossal", "immense"],
}

SCALE_NUMERIC_THRESHOLDS = {
    "small": (1, 100),
    "medium": (101, 10000),
    "large": (10001, float("inf")),
}

# =====================================================
# RISK INDICATORS
# =====================================================
RISK_KEYWORDS: Dict[str, List[str]] = {
    "low": ["low risk", "safe", "conservative", "stable", "secure", "reliable", "standard", "normal", "typical", "zero risk", "no risk", "risk free", "risk-free"],
    "medium": ["moderate risk", "balanced", "mixed", "average risk"],
    "high": ["high risk", "risky", "volatile", "aggressive", "dangerous", "fraudulent", "suspicious", "anomalous", "high-risk", "high value", "premium", "luxury", "max risk", "maximum risk"],
    "extreme": ["extreme", "catastrophic", "meltdown", "collapse", "crisis", "devastating", "apocalyptic", "cataclysmic", "insane risk", "highest risk"],
}

# =====================================================
# FREQUENCY INDICATORS
# =====================================================
FREQUENCY_KEYWORDS: Dict[str, List[str]] = {
    "daily": ["daily", "every day", "each day", "per day", "day by day", "24 hours", "everyday"],
    "weekly": ["weekly", "every week", "each week", "per week", "week by week"],
    "monthly": ["monthly", "every month", "each month", "per month", "month by month", "30 days"],
    "quarterly": ["quarterly", "every quarter", "each quarter", "per quarter", "3 months", "three months"],
    "yearly": ["yearly", "annual", "annually", "every year", "each year", "per year", "12 months", "365 days"],
}

# =====================================================
# CATEGORY PATTERNS — Domain-specific categories in prompts
# =====================================================
CATEGORY_KEYWORDS: Dict[str, List[str]] = {
    # Credit card categories
    "grocery": ["grocery", "groceries", "supermarket"],
    "travel": ["travel", "flight", "flights", "hotel", "hotels", "airline", "airfare"],
    "dining": ["dining", "restaurant", "restaurants", "food", "eating"],
    "entertainment": ["entertainment", "movies", "games", "gaming", "streaming"],
    "retail": ["retail", "shopping", "clothes", "clothing", "apparel"],
    "utilities": ["utilities", "utility", "electric", "gas", "water", "internet", "phone"],
    "healthcare": ["healthcare", "medical", "hospital", "pharmacy", "doctor"],
    "education": ["education", "school", "college", "university", "tuition"],
    # Insurance types
    "auto": ["auto", "car", "vehicle", "automobile"],
    "health": ["health", "medical", "clinical"],
    "property": ["property", "home", "house", "real estate", "building"],
    "life": ["life", "death", "beneficiary"],
    # Loan types
    "personal": ["personal"],
    "home_loan": ["home loan", "housing loan", "mortgage"],
    "auto_loan": ["auto loan", "car loan", "vehicle loan"],
    "business": ["business", "commercial", "corporate"],
}

# =====================================================
# SCORING PARAMETERS
# =====================================================
KEYWORD_MATCH_BASE_WEIGHT = 0.40
SEMANTIC_PHRASE_WEIGHT = 0.35
GENERIC_TERM_BOOST = 0.05
GENERIC_TERM_BOOST_CAP = 0.10
CROSS_DOMAIN_PENALTY = 0.10
MULTI_ENTITY_THRESHOLD = 0.30
MULTI_ENTITY_GAP = 0.25
STRUCTURED_INPUT_CONFIDENCE_BOOST = 0.15
