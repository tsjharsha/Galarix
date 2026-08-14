# =====================================================
# VARIABLE MAPPER — Entity → variable definitions
# =====================================================
# Maps resolved entities to their variable schemas.
# For multi-entity, variables are namespaced to avoid
# collisions (e.g., loans_amount vs credit_card_amount).
#
# NEVER throws. Returns generic variables as fallback.
# =====================================================

from typing import Any, Dict, List


def map_variables(entities: List[str]) -> Dict[str, Dict[str, Any]]:
    """
    Map entity list to combined variable definitions.

    Args:
        entities: List of resolved entity names

    Returns:
        {
            "variable_name": {
                "type": "continuous|categorical|string|integer|datetime",
                "description": "Human-readable description",
                ...
            }
        }

    For multi-entity, variables are namespaced:
        loans_principal_amount, credit_card_amount, etc.
    """
    try:
        if not entities:
            return _get_generic_variables()

        # Filter valid entities
        valid_entities = [e for e in entities if e in VARIABLE_REGISTRY]
        if not valid_entities:
            return _get_generic_variables()

        # Single entity → direct mapping (no namespace prefix)
        if len(valid_entities) == 1:
            return VARIABLE_REGISTRY.get(valid_entities[0], _get_generic_variables()).copy()

        # Multi-entity → namespaced merge
        merged = {}
        for entity in valid_entities:
            entity_vars = VARIABLE_REGISTRY.get(entity, {})
            for var_name, var_def in entity_vars.items():
                namespaced_name = f"{entity}_{var_name}"
                merged[namespaced_name] = {
                    **var_def,
                    "source_entity": entity,
                }
        return merged

    except Exception:
        return _get_generic_variables()


def _get_generic_variables() -> Dict[str, Dict[str, Any]]:
    """Fallback variable set for unknown/generic entities."""
    return {
        "record_id": {
            "type": "string",
            "description": "Unique record identifier",
        },
        "value": {
            "type": "continuous",
            "description": "Primary numeric value",
            "unit": "USD",
        },
        "category": {
            "type": "categorical",
            "description": "Record category",
            "categories": ["Type_A", "Type_B", "Type_C"],
        },
        "timestamp": {
            "type": "datetime",
            "description": "Record timestamp",
        },
        "status": {
            "type": "categorical",
            "description": "Record status",
            "categories": ["Active", "Inactive", "Pending"],
        },
    }


# =====================================================
# VARIABLE REGISTRY — Per-entity variable definitions
# =====================================================
# These define what variables Stage 2 will generate.
# Each variable has type, description, and optional metadata.
# =====================================================

VARIABLE_REGISTRY: Dict[str, Dict[str, Dict[str, Any]]] = {

    "credit_card_activity": {
        "transaction_id": {"type": "string", "description": "Unique transaction identifier"},
        "card_number": {"type": "string", "description": "Masked card number"},
        "merchant_name": {"type": "string", "description": "Merchant or vendor name"},
        "merchant_category": {
            "type": "categorical",
            "description": "Merchant category code",
            "categories": ["Retail", "Food", "Travel", "Utilities", "Entertainment", "Healthcare", "Education"],
        },
        "amount": {"type": "continuous", "unit": "USD", "description": "Transaction amount"},
        "transaction_date": {"type": "datetime", "description": "Date and time of transaction"},
        "status": {
            "type": "categorical",
            "description": "Transaction status",
            "categories": ["Completed", "Pending", "Declined", "Refunded"],
        },
        "location": {"type": "string", "description": "Geographic location"},
    },

    "payroll": {
        "employee_id": {"type": "string", "description": "Unique employee identifier"},
        "salary_base": {"type": "continuous", "unit": "USD", "description": "Base annual salary"},
        "pay_frequency": {
            "type": "categorical",
            "description": "Pay frequency",
            "categories": ["Monthly", "Bi-weekly", "Weekly"],
        },
        "gross_amount": {"type": "continuous", "unit": "USD", "description": "Gross pay amount"},
        "deductions": {"type": "continuous", "unit": "USD", "description": "Total deductions"},
        "net_amount": {"type": "continuous", "unit": "USD", "description": "Net pay"},
        "pay_date": {"type": "datetime", "description": "Date of payment"},
        "department": {
            "type": "categorical",
            "description": "Department",
            "categories": ["Engineering", "Sales", "HR", "Finance", "Operations", "Marketing"],
        },
    },

    "saas_billing": {
        "subscription_id": {"type": "string", "description": "Unique subscription ID"},
        "customer_id": {"type": "string", "description": "Customer identifier"},
        "plan_name": {
            "type": "categorical",
            "description": "Subscription plan tier",
            "categories": ["Starter", "Pro", "Enterprise"],
        },
        "monthly_recurring_revenue": {"type": "continuous", "unit": "USD", "description": "MRR"},
        "billing_frequency": {
            "type": "categorical",
            "description": "Billing cycle",
            "categories": ["Monthly", "Quarterly", "Annual"],
        },
        "invoice_date": {"type": "datetime", "description": "Invoice generation date"},
        "status": {
            "type": "categorical",
            "description": "Subscription status",
            "categories": ["Active", "Paused", "Cancelled", "Trial"],
        },
        "seats": {"type": "integer", "description": "Number of user seats"},
    },

    "investment_statement": {
        "portfolio_id": {"type": "string", "description": "Portfolio identifier"},
        "symbol": {"type": "string", "description": "Stock or asset ticker symbol"},
        "quantity": {"type": "integer", "description": "Number of shares/units held"},
        "purchase_price": {"type": "continuous", "unit": "USD", "description": "Price per share at purchase"},
        "current_price": {"type": "continuous", "unit": "USD", "description": "Current market price"},
        "asset_class": {
            "type": "categorical",
            "description": "Type of investment asset",
            "categories": ["Equity", "Bond", "Mutual Fund", "ETF", "Commodity"],
        },
        "purchase_date": {"type": "datetime", "description": "Date of purchase"},
        "market_value": {"type": "continuous", "unit": "USD", "description": "Current market value"},
    },

    "insurance_claims": {
        "claim_id": {"type": "string", "description": "Unique claim ID"},
        "policy_number": {"type": "string", "description": "Policy reference number"},
        "claim_type": {
            "type": "categorical",
            "description": "Type of insurance claim",
            "categories": ["Health", "Property", "Casualty", "Life", "Auto"],
        },
        "claim_amount": {"type": "continuous", "unit": "USD", "description": "Claimed amount"},
        "approved_amount": {"type": "continuous", "unit": "USD", "description": "Approved payout"},
        "claim_date": {"type": "datetime", "description": "Date of claim filing"},
        "status": {
            "type": "categorical",
            "description": "Current claim status",
            "categories": ["Approved", "Denied", "Pending", "Under Review", "Paid"],
        },
        "fraud_score": {"type": "continuous", "description": "Fraud detection score (0-1)"},
    },

    "loans": {
        "loan_id": {"type": "string", "description": "Unique loan identifier"},
        "principal_amount": {"type": "continuous", "unit": "USD", "description": "Original loan amount"},
        "interest_rate": {"type": "continuous", "unit": "percent", "description": "Annual interest rate"},
        "loan_term_months": {"type": "integer", "description": "Loan duration in months"},
        "monthly_emi": {"type": "continuous", "unit": "USD", "description": "Equated monthly installment"},
        "credit_score": {"type": "integer", "description": "Borrower credit score"},
        "loan_type": {
            "type": "categorical",
            "description": "Category of loan",
            "categories": ["Personal", "Home", "Auto", "Business", "Education"],
        },
        "loan_status": {
            "type": "categorical",
            "description": "Current loan status",
            "categories": ["Active", "Paid Off", "Default", "Delinquent"],
        },
        "disbursement_date": {"type": "datetime", "description": "Date loan was disbursed"},
    },

    "generic": {
        "record_id": {"type": "string", "description": "Unique record identifier"},
        "value": {"type": "continuous", "unit": "USD", "description": "Primary numeric value"},
        "category": {
            "type": "categorical",
            "description": "Record category",
            "categories": ["Type_A", "Type_B", "Type_C"],
        },
        "timestamp": {"type": "datetime", "description": "Record timestamp"},
        "status": {
            "type": "categorical",
            "description": "Record status",
            "categories": ["Active", "Inactive", "Pending"],
        },
    },
}
