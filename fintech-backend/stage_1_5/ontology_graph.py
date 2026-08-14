# =====================================================
# ONTOLOGY GRAPH — Relational Entity Mappings
# =====================================================
# Defines the parent/child relationships between entities.
# Used by the Schema Registry to automatically pull in 
# required dependencies (e.g. loans require users).
# =====================================================

ENTITY_RELATIONSHIPS = {
    "credit_card_activity": {"requires": ["user_profiles"]},
    "loans": {"requires": ["user_profiles", "bank_accounts"]},
    "payroll": {"requires": ["user_profiles", "companies"]},
    "saas_billing": {"requires": ["companies"]},
    "insurance_claims": {"requires": ["user_profiles"]},
    "investment_statement": {"requires": ["user_profiles"]},
    
    # Banking & Payments
    "bank_account_statement": {"requires": ["user_profiles", "bank_accounts"]},
    "wire_transfers": {"requires": ["user_profiles", "bank_accounts"]},
    "atm_withdrawals": {"requires": ["user_profiles", "bank_accounts"]},
    
    # Alternative Lending
    "mortgage_records": {"requires": ["user_profiles", "bank_accounts"]},
    "buy_now_pay_later": {"requires": ["user_profiles"]},
    
    # RegTech & Compliance
    "kyc_records": {"requires": ["user_profiles"]},
    "aml_transaction_alerts": {"requires": ["user_profiles", "bank_accounts"]},
    
    # Capital Markets
    "crypto_trading_log": {"requires": ["user_profiles"]},
    "forex_transactions": {"requires": ["user_profiles", "bank_accounts"]},
    "options_trading": {"requires": ["user_profiles"]},
    
    # Corporate Finance
    "expense_reports": {"requires": ["user_profiles", "companies"]},
    "tax_records_w2": {"requires": ["user_profiles", "companies"]},
    "pnl_statement": {"requires": ["companies"]},
    "invoice_financing": {"requires": ["companies"]},
}

# The actual schemas for the newly introduced parent entities.
# These act just like standard financial entities, but are "base" tables.
PARENT_SCHEMAS = {
    "user_profiles": {
        "variables": {
            "first_name": {"type": "string", "description": "User's first name"},
            "last_name": {"type": "string", "description": "User's last name"},
            "email": {"type": "string", "description": "Primary email address"},
            "credit_score_base": {"type": "integer", "description": "Base credit score (300-850)"},
        },
        "distributions": {
            "credit_score_base": {
                "family": "normal",
                "params": {"mean": 680, "std": 50}
            }
        },
        "dependencies": {},
        "constraints": {
            "credit_score_base": {"min": 300, "max": 850}
        }
    },
    "bank_accounts": {
        "variables": {
            "account_type": {
                "type": "categorical", 
                "categories": ["Checking", "Savings"],
                "description": "Type of bank account"
            },
            "balance": {"type": "continuous", "unit": "USD", "description": "Current balance"},
        },
        "distributions": {
            "balance": {
                "family": "lognormal",
                "params": {"mu": 8.0, "sigma": 1.5}
            }
        },
        "dependencies": {},
        "constraints": {}
    },
    "companies": {
        "variables": {
            "company_name": {"type": "string", "description": "Registered company name"},
            "industry": {
                "type": "categorical", 
                "categories": ["Tech", "Retail", "Finance", "Healthcare"],
                "description": "Company sector"
            },
            "employee_count": {"type": "integer", "description": "Number of employees"},
        },
        "distributions": {
            "employee_count": {
                "family": "lognormal",
                "params": {"mu": 4.0, "sigma": 2.0}
            }
        },
        "dependencies": {},
        "constraints": {}
    }
}
