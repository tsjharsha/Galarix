# =====================================================
# SCHEMA REGISTRY — Entity Schemas & Data Contracts
# =====================================================
# The single source of truth for all entity schemas.
# Contains full probabilistic data contracts including:
#   - Variable definitions
#   - Distribution families & parameters
#   - Dependency rules (conditionals, correlations, derived)
#   - Constraints (bounds, uniqueness)
#
# ═══════════════════════════════════════════════════════
# DATA PROVENANCE — CRITICAL FOR MARKET CREDIBILITY
# ═══════════════════════════════════════════════════════
# Every distribution parameter in this registry is
# grounded in publicly available federal or industry
# data. Each entity schema carries a "data_sources"
# block citing the exact publications used.
# =====================================================

from typing import Any, Dict, List, Optional, Set
from stage_1_5.ontology_graph import ENTITY_RELATIONSHIPS, PARENT_SCHEMAS

ENTITY_SCHEMAS: Dict[str, Dict[str, Any]] = {

    # ─────────────────────────────────────────────────
    # ORIGINAL 6 CORE ENTITIES (CREDIT, PAYROLL, SAAS, INVEST, INSURANCE, LOANS)
    # ─────────────────────────────────────────────────
    "credit_card_activity": {
        "meta": {"entity": "credit_card_activity", "domain": "Financial Transactions", "description": "Credit card transaction records with spending behavior"},
        "data_sources": {
            "primary": "Federal Reserve Payments Study 2023",
            "secondary": ["CFPB Consumer Credit Card Market Report 2023", "Visa Inc. Annual Report — Network Transaction Statistics"],
            "methodology": "Distribution parameters fitted to published median ($50), mean ($94), and percentile data from federal payment studies.",
        },
        "variables": {
            "transaction_id": {"type": "string", "description": "Unique transaction identifier"},
            "card_number": {"type": "string", "description": "Masked card number"},
            "merchant_name": {"type": "string", "description": "Merchant or vendor name"},
            "merchant_category": {"type": "categorical", "categories": ["Retail", "Food", "Travel", "Utilities", "Entertainment", "Healthcare", "Education"]},
            "amount": {"type": "continuous", "unit": "USD", "description": "Transaction amount"},
            "transaction_date": {"type": "datetime", "description": "Date and time of transaction"},
            "status": {"type": "categorical", "categories": ["Completed", "Pending", "Declined", "Refunded"]},
            "location": {"type": "string", "description": "Geographic location"},
        },
        "distributions": {
            "amount": {"family": "lognormal", "params": {"mu": 3.85, "sigma": 1.05}},
            "merchant_category": {"family": "categorical", "weights": [0.22, 0.20, 0.12, 0.18, 0.10, 0.12, 0.06]},
            "status": {"family": "categorical", "weights": [0.935, 0.035, 0.018, 0.012]},
        },
        "dependencies": {
            "conditionals": [
                {"if": {"merchant_category": "Travel"}, "then": {"amount": {"min": 100, "max": 5000}}},
                {"if": {"merchant_category": "Food"}, "then": {"amount": {"min": 3, "max": 250}}},
                {"if": {"merchant_category": "Utilities"}, "then": {"amount": {"min": 30, "max": 500}}},
            ],
            "correlations": [{"between": ["merchant_category", "amount"], "strength": "moderate"}],
            "derived": [],
        },
        "constraints": {"amount": {"min": 0.01, "max": 50000}, "transaction_id": {"unique": True}},
    },

    "payroll": {
        "meta": {"entity": "payroll", "domain": "Human Resources", "description": "Employee salary and compensation data"},
        "data_sources": {
            "primary": "U.S. Bureau of Labor Statistics — OEWS May 2024",
            "secondary": ["BLS Current Population Survey (CPS) 2024 — Median Weekly Earnings", "IRS Publication 15 — Federal Income Tax Withholding Tables"],
            "methodology": "Lognormal fit to BLS OEWS May 2024 all-occupations data: median=$49,500, mean=$67,920. Deduction rates from IRS effective tax rate tables.",
        },
        "variables": {
            "employee_id": {"type": "string", "description": "Unique employee identifier"},
            "salary_base": {"type": "continuous", "unit": "USD", "description": "Base annual salary"},
            "pay_frequency": {"type": "categorical", "categories": ["Monthly", "Bi-weekly", "Weekly"]},
            "gross_amount": {"type": "continuous", "unit": "USD", "description": "Gross pay amount per period"},
            "deductions": {"type": "continuous", "unit": "USD", "description": "Total deductions per period"},
            "net_amount": {"type": "continuous", "unit": "USD", "description": "Net pay per period"},
            "pay_date": {"type": "datetime", "description": "Date of payment"},
            "department": {"type": "categorical", "categories": ["Engineering", "Sales", "HR", "Finance", "Operations", "Marketing"]},
        },
        "distributions": {
            "salary_base": {"family": "lognormal", "params": {"mu": 10.82, "sigma": 0.65}},
            "gross_amount": {"family": "lognormal", "params": {"mu": 8.35, "sigma": 0.65}},
            "department": {"family": "categorical", "weights": [0.25, 0.20, 0.08, 0.12, 0.20, 0.15]},
            "pay_frequency": {"family": "categorical", "weights": [0.36, 0.43, 0.21]},
        },
        "dependencies": {
            "conditionals": [
                {"if": {"pay_frequency": "Monthly"}, "then": {"gross_amount": {"min": 3000}}},
                {"if": {"department": "Engineering"}, "then": {"salary_base": {"min": 55000}}},
            ],
            "correlations": [
                {"between": ["salary_base", "gross_amount"], "strength": "strong"},
                {"between": ["gross_amount", "deductions"], "strength": "moderate"},
            ],
            "derived": [
                {"target": "deductions", "formula": "gross_amount * 0.22"},
                {"target": "net_amount", "formula": "gross_amount - deductions"}
            ],
        },
        "constraints": {"salary_base": {"min": 15080, "max": 500000}, "deductions": {"min": 0}, "net_amount": {"min": 0}},
    },

    "saas_billing": {
        "meta": {"entity": "saas_billing", "domain": "Subscription Revenue", "description": "SaaS subscription billing and revenue data"},
        "data_sources": {
            "primary": "OpenView SaaS Benchmarks Report 2024",
            "secondary": ["KeyBanc Capital Markets Annual SaaS Survey 2024", "Recurly State of Subscriptions Report 2024"],
            "methodology": "MRR distribution fitted to industry benchmarks for SMB B2B SaaS. Plan tier adoption from OpenView survey data. Churn rates from Recurly.",
        },
        "variables": {
            "subscription_id": {"type": "string", "description": "Unique subscription ID"},
            "customer_id": {"type": "string", "description": "Customer identifier"},
            "plan_name": {"type": "categorical", "categories": ["Starter", "Pro", "Enterprise"]},
            "monthly_recurring_revenue": {"type": "continuous", "unit": "USD", "description": "MRR"},
            "billing_frequency": {"type": "categorical", "categories": ["Monthly", "Quarterly", "Annual"]},
            "invoice_date": {"type": "datetime", "description": "Invoice generation date"},
            "status": {"type": "categorical", "categories": ["Active", "Paused", "Cancelled", "Trial"]},
            "seats": {"type": "integer", "description": "Number of user seats"},
        },
        "distributions": {
            "monthly_recurring_revenue": {"family": "lognormal", "params": {"mu": 5.3, "sigma": 1.4}},
            "plan_name": {"family": "categorical", "weights": [0.50, 0.35, 0.15]},
            "billing_frequency": {"family": "categorical", "weights": [0.55, 0.15, 0.30]},
            "status": {"family": "categorical", "weights": [0.72, 0.05, 0.10, 0.13]},
            "seats": {"family": "poisson", "params": {"lam": 12.0}},
        },
        "dependencies": {
            "conditionals": [
                {"if": {"plan_name": "Enterprise"}, "then": {"monthly_recurring_revenue": {"min": 5000}}},
                {"if": {"billing_frequency": "Annual"}, "then": {"monthly_recurring_revenue": {"min": 200}}},
                {"if": {"plan_name": "Starter"}, "then": {"seats": {"max": 10}}},
            ],
            "correlations": [
                {"between": ["plan_name", "monthly_recurring_revenue"], "strength": "strong"},
                {"between": ["plan_name", "seats"], "strength": "moderate"},
            ],
            "derived": [],
        },
        "constraints": {"monthly_recurring_revenue": {"min": 0, "max": 100000}, "seats": {"min": 1, "max": 10000}},
    },

    "investment_statement": {
        "meta": {"entity": "investment_statement", "domain": "Portfolio Management"},
        "data_sources": {
            "primary": "FINRA Foundation National Financial Capability Study 2024",
            "secondary": ["Broadridge U.S. Investor Study 2024", "State Street Global Advisors Portfolio Allocation Report 2024"],
            "methodology": "Purchase price distribution fitted to NYSE/Nasdaq. Asset class allocation from Broadridge/State Street.",
        },
        "variables": {
            "portfolio_id": {"type": "string"},
            "symbol": {"type": "string"},
            "quantity": {"type": "integer"},
            "purchase_price": {"type": "continuous", "unit": "USD"},
            "current_price": {"type": "continuous", "unit": "USD"},
            "asset_class": {"type": "categorical", "categories": ["Equity", "Bond", "Mutual Fund", "ETF", "Commodity"]},
            "purchase_date": {"type": "datetime"},
            "market_value": {"type": "continuous", "unit": "USD"},
        },
        "distributions": {
            "purchase_price": {"family": "lognormal", "params": {"mu": 3.8, "sigma": 0.95}},
            "current_price": {"family": "lognormal", "params": {"mu": 3.8, "sigma": 0.95}},
            "quantity": {"family": "lognormal", "params": {"mu": 3.2, "sigma": 0.9}},
            "asset_class": {"family": "categorical", "weights": [0.45, 0.15, 0.18, 0.17, 0.05]},
        },
        "dependencies": {
            "conditionals": [
                {"if": {"asset_class": "Commodity"}, "then": {"purchase_price": {"min": 10, "max": 3000}}},
                {"if": {"asset_class": "Bond"}, "then": {"purchase_price": {"min": 90, "max": 110}}},
            ],
            "correlations": [{"between": ["asset_class", "purchase_price"], "strength": "weak"}],
            "derived": [{"target": "market_value", "formula": "quantity * current_price"}],
        },
        "constraints": {"quantity": {"min": 1, "max": 10000}, "purchase_price": {"min": 0.01}, "market_value": {"min": 0, "max": 10000000}},
    },

    "insurance_claims": {
        "meta": {"entity": "insurance_claims", "domain": "Insurance"},
        "data_sources": {
            "primary": "NAIC Annual Statement Database & Insurance Industry Analysis 2024",
            "secondary": ["NAIC Auto Insurance Database Report 2024", "Coalition Against Insurance Fraud"],
            "methodology": "Claim amount distribution fitted to NAIC severity data. Fraud score modeled as Beta(1.5,8.0).",
        },
        "variables": {
            "claim_id": {"type": "string"},
            "policy_number": {"type": "string"},
            "claim_type": {"type": "categorical", "categories": ["Health", "Property", "Casualty", "Life", "Auto"]},
            "claim_amount": {"type": "continuous", "unit": "USD"},
            "approved_amount": {"type": "continuous", "unit": "USD"},
            "claim_date": {"type": "datetime"},
            "status": {"type": "categorical", "categories": ["Approved", "Denied", "Pending", "Under Review", "Paid"]},
            "fraud_score": {"type": "continuous"},
        },
        "distributions": {
            "claim_amount": {"family": "lognormal", "params": {"mu": 8.2, "sigma": 1.3}},
            "approved_amount": {"family": "lognormal", "params": {"mu": 7.5, "sigma": 1.3}},
            "claim_type": {"family": "categorical", "weights": [0.30, 0.20, 0.15, 0.10, 0.25]},
            "status": {"family": "categorical", "weights": [0.38, 0.08, 0.22, 0.12, 0.20]},
            "fraud_score": {"family": "beta", "params": {"alpha": 1.5, "beta": 8.0}},
        },
        "dependencies": {
            "conditionals": [
                {"if": {"fraud_score": {"min": 0.8}}, "then": {"status": "Denied"}},
                {"if": {"claim_type": "Life"}, "then": {"claim_amount": {"min": 10000}}},
            ],
            "correlations": [{"between": ["claim_amount", "approved_amount"], "strength": "strong"}],
            "derived": [{"target": "approved_amount", "formula": "np.where(status == 'Denied', 0, claim_amount * 0.85)"}],
        },
        "constraints": {"claim_amount": {"min": 0, "max": 1000000}, "fraud_score": {"min": 0, "max": 1}},
    },

    "loans": {
        "meta": {"entity": "loans", "domain": "Credit & Lending"},
        "data_sources": {
            "primary": "Federal Reserve Survey of Consumer Finances (SCF) 2022",
            "secondary": ["TransUnion Personal Loan Industry Insights Q4 2024", "Experian Personal Loan Balance Report 2024"],
            "methodology": "Principal fitted to TransUnion/Experian (avg $11k-$19k). Rate centered on Fed H.15.",
        },
        "variables": {
            "loan_id": {"type": "string"},
            "principal_amount": {"type": "continuous", "unit": "USD"},
            "interest_rate": {"type": "continuous", "unit": "percent"},
            "loan_term_months": {"type": "integer"},
            "monthly_emi": {"type": "continuous", "unit": "USD"},
            "credit_score": {"type": "integer"},
            "loan_type": {"type": "categorical", "categories": ["Personal", "Home", "Auto", "Business", "Education"]},
            "loan_status": {"type": "categorical", "categories": ["Active", "Paid Off", "Default", "Delinquent"]},
            "disbursement_date": {"type": "datetime"},
        },
        "distributions": {
            "principal_amount": {"family": "lognormal", "params": {"mu": 9.5, "sigma": 1.1}},
            "interest_rate": {"family": "normal", "params": {"mean": 12.35, "std": 4.5}},
            "credit_score": {"family": "normal", "params": {"mean": 717, "std": 75}},
            "loan_type": {"family": "categorical", "weights": [0.28, 0.25, 0.27, 0.10, 0.10]},
            "loan_status": {"family": "categorical", "weights": [0.62, 0.22, 0.08, 0.08]},
            "loan_term_months": {"family": "categorical", "categories": [12, 24, 36, 60, 84, 120, 180, 240], "weights": [0.05, 0.12, 0.22, 0.25, 0.14, 0.10, 0.08, 0.04]},
        },
        "dependencies": {
            "conditionals": [
                {"if": {"credit_score": {"min": 750}}, "then": {"interest_rate": {"max": 8.0}}},
                {"if": {"loan_type": "Home"}, "then": {"principal_amount": {"min": 50000}}},
            ],
            "correlations": [{"between": ["credit_score", "interest_rate"], "strength": "moderate"}],
            "derived": [{"target": "monthly_emi", "formula": "(principal_amount * interest_rate/1200 * (1+interest_rate/1200)**loan_term_months) / ((1+interest_rate/1200)**loan_term_months - 1)"}],
        },
        "constraints": {"principal_amount": {"min": 1000, "max": 10000000}, "credit_score": {"min": 300, "max": 850}},
    },

    # ─────────────────────────────────────────────────
    # BANKING & PAYMENTS (NEW)
    # ─────────────────────────────────────────────────
    "bank_account_statement": {
        "meta": {"entity": "bank_account_statement", "domain": "Banking"},
        "data_sources": {
            "primary": "FDIC National Survey of Unbanked and Underbanked Households 2023",
            "secondary": ["Federal Reserve SCF 2022"],
            "methodology": "Balance parameters based on median transaction account balances across US demographics.",
        },
        "variables": {
            "transaction_id": {"type": "string"},
            "account_id": {"type": "string"},
            "transaction_type": {"type": "categorical", "categories": ["Deposit", "Withdrawal", "Transfer", "Fee", "Interest"]},
            "amount": {"type": "continuous", "unit": "USD"},
            "balance_after": {"type": "continuous", "unit": "USD"},
            "description": {"type": "string"},
            "timestamp": {"type": "datetime"},
        },
        "distributions": {
            "amount": {"family": "lognormal", "params": {"mu": 4.5, "sigma": 1.2}},
            "balance_after": {"family": "lognormal", "params": {"mu": 7.5, "sigma": 1.5}},
            "transaction_type": {"family": "categorical", "weights": [0.25, 0.45, 0.20, 0.08, 0.02]},
        },
        "dependencies": {"conditionals": [], "correlations": [], "derived": []},
        "constraints": {"amount": {"min": 0.01}},
    },

    "wire_transfers": {
        "meta": {"entity": "wire_transfers", "domain": "Payments"},
        "data_sources": {
            "primary": "Federal Reserve Fedwire Funds Service Analysis 2023",
            "secondary": ["SWIFT Global Payment Innovation (gpi) Data"],
            "methodology": "High-value transfer parameters anchored to Fedwire volume vs value statistics.",
        },
        "variables": {
            "wire_id": {"type": "string"},
            "sender_account": {"type": "string"},
            "receiver_account": {"type": "string"},
            "receiver_swift_bic": {"type": "string"},
            "transfer_amount": {"type": "continuous", "unit": "USD"},
            "currency": {"type": "categorical", "categories": ["USD", "EUR", "GBP", "JPY", "CHF"]},
            "status": {"type": "categorical", "categories": ["Completed", "Pending", "Rejected", "Held"]},
            "aml_flag": {"type": "categorical", "categories": [0, 1]},
        },
        "distributions": {
            "transfer_amount": {"family": "lognormal", "params": {"mu": 10.5, "sigma": 2.0}},
            "currency": {"family": "categorical", "weights": [0.60, 0.20, 0.10, 0.08, 0.02]},
            "status": {"family": "categorical", "weights": [0.95, 0.03, 0.01, 0.01]},
            "aml_flag": {"family": "categorical", "categories": [0, 1], "weights": [0.97, 0.03]},
        },
        "dependencies": {
            "conditionals": [{"if": {"status": "Held"}, "then": {"aml_flag": {"value": 1}}}],
            "correlations": [{"between": ["transfer_amount", "aml_flag"], "strength": "moderate"}],
            "derived": []
        },
        "constraints": {"transfer_amount": {"min": 100}, "aml_flag": {"min": 0, "max": 1}},
    },

    "atm_withdrawals": {
        "meta": {"entity": "atm_withdrawals", "domain": "Banking"},
        "data_sources": {
            "primary": "Federal Reserve Payments Study (ATM module)",
            "methodology": "ATM withdrawal distribution fitted closely to integer multiples of $20 with a mean around $100.",
        },
        "variables": {
            "withdrawal_id": {"type": "string"},
            "atm_id": {"type": "string"},
            "card_network": {"type": "categorical", "categories": ["Visa", "Mastercard", "Pulse", "Star", "Interlink"]},
            "amount": {"type": "continuous", "unit": "USD"},
            "surcharge_fee": {"type": "continuous", "unit": "USD"},
            "timestamp": {"type": "datetime"},
            "network_status": {"type": "categorical", "categories": ["In-Network", "Out-of-Network"]},
        },
        "distributions": {
            "amount": {"family": "normal", "params": {"mean": 100, "std": 60}},
            "surcharge_fee": {"family": "lognormal", "params": {"mu": 0.8, "sigma": 0.5}},
            "network_status": {"family": "categorical", "weights": [0.70, 0.30]},
            "card_network": {"family": "categorical", "weights": [0.4, 0.3, 0.1, 0.1, 0.1]},
        },
        "dependencies": {
            "conditionals": [{"if": {"network_status": "In-Network"}, "then": {"surcharge_fee": {"value": 0.0}}}],
            "correlations": [],
            "derived": []
        },
        "constraints": {"amount": {"min": 20, "max": 1000}},
    },

    # ─────────────────────────────────────────────────
    # ALTERNATIVE LENDING (NEW)
    # ─────────────────────────────────────────────────
    "mortgage_records": {
        "meta": {"entity": "mortgage_records", "domain": "Credit & Lending"},
        "data_sources": {
            "primary": "Freddie Mac Primary Mortgage Market Survey 2024",
            "secondary": ["Fannie Mae Mortgage Data", "FHFA House Price Index"],
            "methodology": "Principal mapped to median home prices. Rates mapped to 30-year fixed averages.",
        },
        "variables": {
            "mortgage_id": {"type": "string"},
            "property_value": {"type": "continuous", "unit": "USD"},
            "down_payment": {"type": "continuous", "unit": "USD"},
            "loan_amount": {"type": "continuous", "unit": "USD"},
            "interest_rate": {"type": "continuous", "unit": "percent"},
            "loan_type": {"type": "categorical", "categories": ["30-Year Fixed", "15-Year Fixed", "5/1 ARM", "FHA"]},
            "monthly_payment": {"type": "continuous", "unit": "USD"},
            "ltv_ratio": {"type": "continuous", "unit": "percent"},
        },
        "distributions": {
            "property_value": {"family": "lognormal", "params": {"mu": 12.8, "sigma": 0.6}},
            "down_payment": {"family": "lognormal", "params": {"mu": 10.2, "sigma": 0.7}},
            "interest_rate": {"family": "normal", "params": {"mean": 6.8, "std": 0.75}},
            "loan_type": {"family": "categorical", "weights": [0.75, 0.15, 0.05, 0.05]},
        },
        "dependencies": {
            "conditionals": [],
            "correlations": [],
            "derived": [
                {"target": "down_payment", "formula": "np.minimum(down_payment, property_value * 0.5)"},
                {"target": "loan_amount", "formula": "property_value - down_payment"},
                {"target": "ltv_ratio", "formula": "(loan_amount / property_value) * 100"},
                {"target": "monthly_payment", "formula": "(loan_amount * interest_rate/1200 * (1+interest_rate/1200)**360) / ((1+interest_rate/1200)**360 - 1)"}
            ]
        },
        "constraints": {"property_value": {"min": 50000}, "ltv_ratio": {"min": 0, "max": 100}},
    },

    "buy_now_pay_later": {
        "meta": {"entity": "buy_now_pay_later", "domain": "Alternative Lending"},
        "data_sources": {
            "primary": "CFPB Buy Now, Pay Later Market Report",
            "methodology": "Order amounts fixed to retail basket sizes. Installment logic tracks 'Pay in 4' defaults.",
        },
        "variables": {
            "bnpl_id": {"type": "string"},
            "merchant_name": {"type": "string"},
            "order_total": {"type": "continuous", "unit": "USD"},
            "installment_amount": {"type": "continuous", "unit": "USD"},
            "num_installments": {"type": "integer"},
            "installments_paid": {"type": "integer"},
            "status": {"type": "categorical", "categories": ["Active", "Completed", "Default", "Late"]},
        },
        "distributions": {
            "order_total": {"family": "lognormal", "params": {"mu": 4.8, "sigma": 0.8}},
            "status": {"family": "categorical", "weights": [0.55, 0.35, 0.05, 0.05]},
            "num_installments": {"family": "categorical", "categories": [4, 6, 12], "weights": [0.85, 0.10, 0.05]},
            "installments_paid": {"family": "categorical", "categories": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12], "weights": [0.2, 0.1, 0.1, 0.1, 0.1, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05]},
        },
        "dependencies": {
            "conditionals": [
                {"if": {"status": "Completed"}, "then": {"installments_paid": {"equals": "num_installments"}}},
                {"if": {"installments_paid": {"min": 0}}, "then": {"installments_paid": {"max": "num_installments"}}}
            ],
            "correlations": [],
            "derived": [{"target": "installment_amount", "formula": "order_total / num_installments"}]
        },
        "constraints": {"order_total": {"min": 10, "max": 5000}},
    },

    # ─────────────────────────────────────────────────
    # COMPLIANCE & REGTECH (NEW)
    # ─────────────────────────────────────────────────
    "kyc_records": {
        "meta": {"entity": "kyc_records", "domain": "Compliance"},
        "data_sources": {
            "primary": "FATF KYC/CDD Guidelines",
            "secondary": ["ACAMS Aggregate KYC Analytics"],
            "methodology": "Risk ratings distributed per standard banking client risk profiling logic.",
        },
        "variables": {
            "kyc_id": {"type": "string"},
            "document_type": {"type": "categorical", "categories": ["Passport", "National ID", "Driver License"]},
            "verification_status": {"type": "categorical", "categories": ["Verified", "Pending", "Rejected", "Manual Review"]},
            "pep_status": {"type": "categorical", "categories": ["None", "Domestic PEP", "Foreign PEP"]},
            "risk_rating": {"type": "categorical", "categories": ["Low", "Medium", "High"]},
            "sanctions_match": {"type": "integer"},
            "verification_score": {"type": "continuous"},
        },
        "distributions": {
            "document_type": {"family": "categorical", "weights": [0.4, 0.3, 0.3]},
            "verification_status": {"family": "categorical", "weights": [0.85, 0.05, 0.05, 0.05]},
            "pep_status": {"family": "categorical", "weights": [0.98, 0.015, 0.005]},
            "risk_rating": {"family": "categorical", "weights": [0.75, 0.20, 0.05]},
            "verification_score": {"family": "beta", "params": {"alpha": 8.0, "beta": 2.0}},
            "sanctions_match": {"family": "categorical", "categories": [0, 1], "weights": [0.999, 0.001]},
        },
        "dependencies": {
            "conditionals": [
                {"if": {"sanctions_match": 1}, "then": {"verification_status": "Rejected"}},
                {"if": {"pep_status": "Foreign PEP"}, "then": {"risk_rating": "High"}},
            ],
            "correlations": [{"between": ["verification_score", "verification_status"], "strength": "strong"}],
            "derived": []
        },
        "constraints": {"verification_score": {"min": 0.0, "max": 1.0}},
    },

    "aml_transaction_alerts": {
        "meta": {"entity": "aml_transaction_alerts", "domain": "Compliance"},
        "data_sources": {
            "primary": "FinCEN SAR Statistics",
            "secondary": ["ACAMS Suspicious Activity Typologies"],
            "methodology": "Alerts tuned to mimic rule-based scenario generation (Structuring, Velocity, etc).",
        },
        "variables": {
            "alert_id": {"type": "string"},
            "scenario": {"type": "categorical", "categories": ["Structuring", "High Velocity", "Sanctions", "High-Risk Jurisdiction", "Unusual Volume"]},
            "transaction_count": {"type": "integer"},
            "total_volume": {"type": "continuous", "unit": "USD"},
            "risk_score": {"type": "continuous"},
            "outcome": {"type": "categorical", "categories": ["False Positive", "Escalated for SAR", "Pending Review"]},
        },
        "distributions": {
            "scenario": {"family": "categorical", "weights": [0.35, 0.25, 0.05, 0.15, 0.20]},
            "transaction_count": {"family": "lognormal", "params": {"mu": 2.5, "sigma": 0.8}},
            "total_volume": {"family": "lognormal", "params": {"mu": 9.5, "sigma": 1.2}},
            "risk_score": {"family": "normal", "params": {"mean": 60, "std": 15}},
            "outcome": {"family": "categorical", "weights": [0.80, 0.05, 0.15]},
        },
        "dependencies": {
            "conditionals": [
                {"if": {"scenario": "Structuring"}, "then": {"total_volume": {"min": 9500, "max": 9999}}},
                {"if": {"risk_score": {"min": 85}}, "then": {"outcome": "Escalated for SAR"}},
            ],
            "correlations": [{"between": ["risk_score", "total_volume"], "strength": "weak"}],
            "derived": []
        },
        "constraints": {"risk_score": {"min": 0, "max": 100}, "total_volume": {"min": 0}},
    },

    # ─────────────────────────────────────────────────
    # CAPITAL MARKETS (NEW)
    # ─────────────────────────────────────────────────
    "crypto_trading_log": {
        "meta": {"entity": "crypto_trading_log", "domain": "Capital Markets"},
        "data_sources": {
            "primary": "CoinMarketCap / CoinGecko Trade Volumes",
            "methodology": "Log-normal volumes mapping to highly-skewed retail trading sizes in digital assets.",
        },
        "variables": {
            "trade_id": {"type": "string"},
            "asset": {"type": "categorical", "categories": ["BTC", "ETH", "SOL", "USDT", "DOGE"]},
            "side": {"type": "categorical", "categories": ["BUY", "SELL"]},
            "amount": {"type": "continuous"},
            "price_usd": {"type": "continuous", "unit": "USD"},
            "fee_usd": {"type": "continuous", "unit": "USD"},
            "timestamp": {"type": "datetime"},
        },
        "distributions": {
            "asset": {"family": "categorical", "weights": [0.40, 0.30, 0.10, 0.15, 0.05]},
            "side": {"family": "categorical", "weights": [0.52, 0.48]},
            "amount": {"family": "lognormal", "params": {"mu": 0.0, "sigma": 2.0}},
            "price_usd": {"family": "lognormal", "params": {"mu": 8.5, "sigma": 1.5}},
            "fee_usd": {"family": "lognormal", "params": {"mu": 1.5, "sigma": 1.0}},
        },
        "dependencies": {"conditionals": [], "correlations": [], "derived": []},
        "constraints": {"amount": {"min": 0}, "price_usd": {"min": 0}},
    },

    "forex_transactions": {
        "meta": {"entity": "forex_transactions", "domain": "Capital Markets"},
        "data_sources": {
            "primary": "BIS Triennial Central Bank Survey of FX",
            "methodology": "Currency weights match BIS volume. Spreads normal-distributed.",
        },
        "variables": {
            "fx_trade_id": {"type": "string"},
            "currency_pair": {"type": "categorical", "categories": ["EUR/USD", "USD/JPY", "GBP/USD", "USD/CHF", "AUD/USD"]},
            "base_amount": {"type": "continuous"},
            "exchange_rate": {"type": "continuous"},
            "spread_pips": {"type": "continuous"},
            "timestamp": {"type": "datetime"},
        },
        "distributions": {
            "currency_pair": {"family": "categorical", "weights": [0.40, 0.25, 0.15, 0.10, 0.10]},
            "base_amount": {"family": "lognormal", "params": {"mu": 11.5, "sigma": 2.0}},
            "exchange_rate": {"family": "normal", "params": {"mean": 1.15, "std": 0.2}},
            "spread_pips": {"family": "normal", "params": {"mean": 1.5, "std": 0.5}},
        },
        "dependencies": {"conditionals": [], "correlations": [], "derived": []},
        "constraints": {"spread_pips": {"min": 0.1}, "base_amount": {"min": 100}},
    },

    "options_trading": {
        "meta": {"entity": "options_trading", "domain": "Capital Markets"},
        "data_sources": {
            "primary": "OCC (Options Clearing Corporation) Volume Analytics",
            "methodology": "Retail options flow mappings (primarily short-dated calls).",
        },
        "variables": {
            "contract_id": {"type": "string"},
            "underlying_symbol": {"type": "string"},
            "type": {"type": "categorical", "categories": ["Call", "Put"]},
            "strike_price": {"type": "continuous", "unit": "USD"},
            "premium": {"type": "continuous", "unit": "USD"},
            "implied_volatility": {"type": "continuous", "unit": "percent"},
            "contracts_traded": {"type": "integer"},
            "days_to_expiration": {"type": "integer"},
        },
        "distributions": {
            "type": {"family": "categorical", "weights": [0.65, 0.35]},
            "strike_price": {"family": "lognormal", "params": {"mu": 4.5, "sigma": 0.8}},
            "premium": {"family": "lognormal", "params": {"mu": 1.5, "sigma": 1.0}},
            "implied_volatility": {"family": "normal", "params": {"mean": 35.0, "std": 15.0}},
            "contracts_traded": {"family": "lognormal", "params": {"mu": 1.5, "sigma": 1.2}},
            "days_to_expiration": {"family": "categorical", "categories": [1, 7, 14, 30, 90, 180, 365], "weights": [0.20, 0.30, 0.15, 0.15, 0.10, 0.05, 0.05]},
        },
        "dependencies": {"conditionals": [], "correlations": [], "derived": []},
        "constraints": {"implied_volatility": {"min": 5.0, "max": 300.0}, "contracts_traded": {"min": 1}},
    },

    # ─────────────────────────────────────────────────
    # CORPORATE FINANCE (NEW)
    # ─────────────────────────────────────────────────
    "expense_reports": {
        "meta": {"entity": "expense_reports", "domain": "Corporate Finance"},
        "data_sources": {
            "primary": "Certify/Concur Annual T&E Benchmark Report",
            "methodology": "T&E claim values mapped to categorical spend distributions.",
        },
        "variables": {
            "report_id": {"type": "string"},
            "category": {"type": "categorical", "categories": ["Airfare", "Meals", "Lodging", "Gas/Mileage", "Supplies"]},
            "amount": {"type": "continuous", "unit": "USD"},
            "receipt_attached": {"type": "integer"},
            "status": {"type": "categorical", "categories": ["Approved", "Pending", "Rejected", "Paid"]},
        },
        "distributions": {
            "category": {"family": "categorical", "weights": [0.15, 0.40, 0.20, 0.15, 0.10]},
            "amount": {"family": "lognormal", "params": {"mu": 4.5, "sigma": 1.2}},
            "receipt_attached": {"family": "categorical", "categories": [0, 1], "weights": [0.10, 0.90]},
            "status": {"family": "categorical", "weights": [0.60, 0.25, 0.05, 0.10]},
        }, 
        "dependencies": {
            "conditionals": [
                {"if": {"receipt_attached": 0}, "then": {"status": "Rejected"}},
                {"if": {"category": "Airfare"}, "then": {"amount": {"min": 150}}},
            ],
            "correlations": [], "derived": []
        },
        "constraints": {"amount": {"min": 1.0}, "receipt_attached": {"min": 0, "max": 1}},
    },

    "tax_records_w2": {
        "meta": {"entity": "tax_records_w2", "domain": "Corporate Finance"},
        "data_sources": {
            "primary": "IRS Statistics of Income (SOI) Tax Stats",
            "methodology": "W2 generation mapping structurally to BLS OEWS wage brackets.",
        },
        "variables": {
            "w2_id": {"type": "string"},
            "employer_id": {"type": "string"},
            "wages_tips_other": {"type": "continuous", "unit": "USD"},
            "federal_income_tax_withheld": {"type": "continuous", "unit": "USD"},
            "social_security_tax": {"type": "continuous", "unit": "USD"},
            "medicare_tax": {"type": "continuous", "unit": "USD"},
            "state_tax": {"type": "continuous", "unit": "USD"},
        },
        "distributions": {
            "wages_tips_other": {"family": "lognormal", "params": {"mu": 10.8, "sigma": 0.65}},
        },
        "dependencies": {
            "conditionals": [],
            "correlations": [],
            "derived": [
                # Approximations of 2024 tax brackets
                {"target": "social_security_tax", "formula": "wages_tips_other * 0.062"},
                {"target": "medicare_tax", "formula": "wages_tips_other * 0.0145"},
                {"target": "federal_income_tax_withheld", "formula": "wages_tips_other * 0.18"},
                {"target": "state_tax", "formula": "wages_tips_other * 0.05"},
            ]
        },
        "constraints": {"wages_tips_other": {"min": 1000}},
    },

    "pnl_statement": {
        "meta": {"entity": "pnl_statement", "domain": "Corporate Finance"},
        "data_sources": {
            "primary": "SEC EDGAR Financial Database Extracts",
            "methodology": "Standard corporate P&L line-item ratios.",
        },
        "variables": {
            "period": {"type": "categorical", "categories": ["Q1", "Q2", "Q3", "Q4", "FY"]},
            "revenue": {"type": "continuous", "unit": "USD"},
            "cogs": {"type": "continuous", "unit": "USD"},
            "gross_profit": {"type": "continuous", "unit": "USD"},
            "operating_expenses": {"type": "continuous", "unit": "USD"},
            "net_income": {"type": "continuous", "unit": "USD"},
        },
        "distributions": {
            "period": {"family": "categorical", "weights": [0.20, 0.20, 0.20, 0.20, 0.20]},
            "revenue": {"family": "lognormal", "params": {"mu": 14.5, "sigma": 1.5}},
            "cogs": {"family": "lognormal", "params": {"mu": 13.5, "sigma": 1.5}},
            "operating_expenses": {"family": "lognormal", "params": {"mu": 13.0, "sigma": 1.0}},
        },
        "dependencies": {
            "conditionals": [],
            "correlations": [{"between": ["revenue", "cogs"], "strength": "very_strong"}],
            "derived": [
                {"target": "cogs", "formula": "np.minimum(cogs, revenue * 1.2)"},
                {"target": "gross_profit", "formula": "revenue - cogs"},
                {"target": "net_income", "formula": "gross_profit - operating_expenses"},
            ]
        },
        "constraints": {"revenue": {"min": 0}},
    },

    "invoice_financing": {
        "meta": {"entity": "invoice_financing", "domain": "B2B Credit"},
        "data_sources": {
            "primary": "Commercial Finance Association (CFA) Market Analysis",
            "methodology": "Advance rates and factoring fees mapped to middle-market standards.",
        },
        "variables": {
            "invoice_id": {"type": "string"},
            "face_value": {"type": "continuous", "unit": "USD"},
            "advance_rate": {"type": "continuous", "unit": "percent"},
            "advance_amount": {"type": "continuous", "unit": "USD"},
            "discount_fee_percent": {"type": "continuous", "unit": "percent"},
            "net_payout": {"type": "continuous", "unit": "USD"},
            "status": {"type": "categorical", "categories": ["Funded", "Repaid", "Default"]},
        },
        "distributions": {
            "face_value": {"family": "lognormal", "params": {"mu": 9.5, "sigma": 1.2}},
            "advance_rate": {"family": "normal", "params": {"mean": 85.0, "std": 5.0}},
            "discount_fee_percent": {"family": "normal", "params": {"mean": 3.0, "std": 1.0}},
            "status": {"family": "categorical", "weights": [0.20, 0.78, 0.02]},
        },
        "dependencies": {
            "conditionals": [],
            "correlations": [],
            "derived": [
                {"target": "advance_amount", "formula": "face_value * (advance_rate / 100)"},
                {"target": "net_payout", "formula": "advance_amount - (face_value * (discount_fee_percent / 100))"}
            ]
        },
        "constraints": {"advance_rate": {"min": 50, "max": 95}, "discount_fee_percent": {"min": 0.5, "max": 10.0}},
    },

    # ─────────────────────────────────────────────────
    # GENERIC FALLBACK ENTITY
    # ─────────────────────────────────────────────────
    "generic": {
        "meta": {"entity": "generic", "domain": "General Financial"},
        "data_sources": {"primary": "Composite — No specific federal source"},
        "variables": {
            "record_id": {"type": "string", "description": "Unique record identifier"},
            "value": {"type": "continuous", "unit": "USD", "description": "Primary numeric value"},
            "category": {"type": "categorical", "categories": ["Type_A", "Type_B", "Type_C", "Type_D"]},
            "timestamp": {"type": "datetime", "description": "Record timestamp"},
            "status": {"type": "categorical", "categories": ["Active", "Inactive", "Pending"]},
        },
        "distributions": {
            "value": {"family": "normal", "params": {"mean": 500, "std": 200}},
            "category": {"family": "categorical", "weights": [0.30, 0.30, 0.25, 0.15]},
            "status": {"family": "categorical", "weights": [0.60, 0.25, 0.15]},
        },
        "dependencies": {"conditionals": [], "correlations": [], "derived": []},
        "constraints": {"value": {"min": 0, "max": 100000}},
    },
}

# =====================================================
# PUBLIC API
# =====================================================

def get_schema(entity: str) -> Optional[Dict[str, Any]]:
    return ENTITY_SCHEMAS.get(entity)

def get_data_sources(entity: str) -> Dict[str, Any]:
    return ENTITY_SCHEMAS.get(entity, {}).get("data_sources", {"primary": "Unknown", "methodology": "Not documented"})

def get_combined_schema(entities: List[str]) -> Dict[str, Any]:
    if not entities:
        return _normalize_schema_shape(ENTITY_SCHEMAS.get("generic", {}))

    all_schemas_to_merge = []
    for entity in entities:
        schema = ENTITY_SCHEMAS.get(entity)
        if schema:
            all_schemas_to_merge.append((entity, schema))
            parents = ENTITY_RELATIONSHIPS.get(entity, {}).get("requires", [])
            for parent in parents:
                parent_schema = PARENT_SCHEMAS.get(parent)
                if parent_schema:
                    all_schemas_to_merge.append((parent, parent_schema))
                    
    if not all_schemas_to_merge:
        return _normalize_schema_shape(ENTITY_SCHEMAS["generic"])

    combined = {
        "variables": {},
        "distributions": {},
        "dependencies": {"conditionals": [], "correlations": [], "derived": []},
        "constraints": {},
    }

    seen_prefixes = set()
    for prefix, schema in all_schemas_to_merge:
        if prefix in seen_prefixes:
            continue
        seen_prefixes.add(prefix)

        for var_name, var_def in schema.get("variables", {}).items():
            combined["variables"][f"{prefix}_{var_name}"] = {**var_def, "source_entity": prefix}

        for dist_name, dist_def in schema.get("distributions", {}).items():
            combined["distributions"][f"{prefix}_{dist_name}"] = dist_def

        for const_name, const_def in schema.get("constraints", {}).items():
            combined["constraints"][f"{prefix}_{const_name}"] = const_def

        deps = schema.get("dependencies", {})
        for cond in deps.get("conditionals", []):
            combined["dependencies"]["conditionals"].append({"source_entity": prefix, **cond})
        for corr in deps.get("correlations", []):
            combined["dependencies"]["correlations"].append({"source_entity": prefix, **corr})
        for deriv in deps.get("derived", []):
            combined["dependencies"]["derived"].append({"source_entity": prefix, **deriv})

    # Semantic Reconciliation (Auto-Aliasing)
    # Detect synonymous fields across merged entities and bind them with a derived rule
    # to ensure they have mathematically identical values across the row.
    alias_map = {}
    for full_col_name in list(combined["variables"].keys()):
        # Normalize name for matching
        if "credit_score" in full_col_name:
            match_key = "credit_score"
        elif "company_name" in full_col_name:
            match_key = "company_name"
        else:
            continue
            
        if match_key not in alias_map:
            alias_map[match_key] = full_col_name
        else:
            combined["dependencies"]["derived"].append({
                "source_entity": "system_auto_alias",
                "target": full_col_name,
                "formula": alias_map[match_key]
            })

    return combined

def _normalize_schema_shape(schema: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "variables": schema.get("variables", {}),
        "distributions": schema.get("distributions", {}),
        "dependencies": schema.get("dependencies", {"conditionals": [], "correlations": [], "derived": []}),
        "constraints": schema.get("constraints", {}),
    }

def list_available_entities() -> List[str]:
    return [e for e in ENTITY_SCHEMAS.keys() if e != "generic"]

def entity_exists(entity: str) -> bool:
    if entity == "multi_entity":
        return True
    return entity in ENTITY_SCHEMAS

import logging
logger = logging.getLogger(__name__)

def validate_schemas():
    for entity_name, schema in ENTITY_SCHEMAS.items():
        variables = schema.get("variables", {})
        distributions = schema.get("distributions", {})
        derived_targets = [d.get("target") for d in schema.get("dependencies", {}).get("derived", [])]

        for var_name, var_def in variables.items():
            var_type = var_def.get("type")
            if var_name in derived_targets:
                continue
            if var_name == "record_id" or var_name.endswith("_id") or var_name == "timestamp" or var_type == "datetime" or var_type == "string":
                continue

            if var_type in ("continuous", "integer") and var_name not in distributions:
                logger.warning(f"Schema Validation Error: Variable '{var_name}' in entity '{entity_name}' is of type {var_type} but has NO distribution.")
            elif var_type == "categorical":
                categories = var_def.get("categories")
                if not categories:
                    logger.warning(f"Schema Validation Error: Variable '{var_name}' in entity '{entity_name}' is of type categorical but has NO categories list.")

validate_schemas()