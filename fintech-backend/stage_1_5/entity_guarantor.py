# =====================================================
# ENTITY GUARANTOR — Ensure entity is ALWAYS valid
# =====================================================
# If entity is missing, invalid, or unrecognized:
#   1. Try to re-resolve from the prompt
#   2. Fall back to "generic"
#
# After this module, entity is GUARANTEED to be a valid,
# recognized entity string.
#
# NEVER throws. ALWAYS produces a valid entity.
# =====================================================

from typing import Any, Dict

from stage_1_5.constants import SUPPORTED_ENTITIES, DEFAULTS


def guarantee_entity(contract: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ensure the contract has a valid entity.

    Args:
        contract: Contract from previous pipeline stages

    Returns:
        Contract with guaranteed valid entity and entities list
    """
    try:
        entity = contract.get("entity", "")
        entities = contract.get("entities", [])

        # ── Case 1: Entity is valid ──
        if entity and entity in SUPPORTED_ENTITIES:
            # Make sure entities list is consistent
            if not entities:
                contract["entities"] = [entity]
            return contract

        # ── Case 2: Entity is "multi_entity" — check sub-entities ──
        if entity == "multi_entity" and entities:
            valid_entities = [e for e in entities if e in SUPPORTED_ENTITIES]
            if valid_entities:
                contract["entities"] = valid_entities
                contract["entity"] = "multi_entity" if len(valid_entities) > 1 else valid_entities[0]
                return contract

        # ── Case 3: Entity is missing/invalid — try from entities list ──
        if entities:
            valid_entities = [e for e in entities if e in SUPPORTED_ENTITIES]
            if valid_entities:
                contract["entities"] = valid_entities
                contract["entity"] = valid_entities[0] if len(valid_entities) == 1 else "multi_entity"
                return contract

        # ── Case 4: Try re-resolving from prompt ──
        prompt = contract.get("prompt", "")
        if prompt:
            resolved_entity = _quick_resolve(prompt)
            if resolved_entity:
                contract["entity"] = resolved_entity
                contract["entities"] = [resolved_entity]
                return contract

        # ── Case 5: Absolute fallback → generic ──
        contract["entity"] = DEFAULTS["entity"]
        contract["entities"] = [DEFAULTS["entity"]]
        return contract

    except Exception:
        contract["entity"] = DEFAULTS["entity"]
        contract["entities"] = [DEFAULTS["entity"]]
        return contract


def _quick_resolve(prompt: str) -> str:
    """
    Quick and dirty entity resolution from prompt.
    Only used as a fallback when the full resolver failed.
    Checks for the most obvious domain keywords.

    Must cover ALL 20 supported entities — not just the original 6.
    Order matters: more specific terms must come before generic ones
    (e.g. 'mortgage' before 'loan' to avoid misrouting).
    """
    prompt_lower = prompt.lower()

    # Ordered list — specific matches first, generic last
    quick_map = [
        # RegTech & Compliance
        ("kyc", "kyc_records"),
        ("know your customer", "kyc_records"),
        ("aml", "aml_transaction_alerts"),
        ("anti money laundering", "aml_transaction_alerts"),
        ("suspicious activity", "aml_transaction_alerts"),
        # Capital Markets
        ("crypto", "crypto_trading_log"),
        ("bitcoin", "crypto_trading_log"),
        ("ethereum", "crypto_trading_log"),
        ("blockchain", "crypto_trading_log"),
        ("forex", "forex_transactions"),
        ("currency pair", "forex_transactions"),
        ("foreign exchange", "forex_transactions"),
        ("options trading", "options_trading"),
        ("call option", "options_trading"),
        ("put option", "options_trading"),
        ("strike price", "options_trading"),
        # Alternative Lending — BEFORE generic 'loan'
        ("mortgage", "mortgage_records"),
        ("refinance", "mortgage_records"),
        ("buy now pay later", "buy_now_pay_later"),
        ("bnpl", "buy_now_pay_later"),
        ("klarna", "buy_now_pay_later"),
        ("afterpay", "buy_now_pay_later"),
        # Banking & Payments
        ("wire transfer", "wire_transfers"),
        ("swift", "wire_transfers"),
        ("remittance", "wire_transfers"),
        ("atm", "atm_withdrawals"),
        ("bank account", "bank_account_statement"),
        ("checking account", "bank_account_statement"),
        ("savings account", "bank_account_statement"),
        # Corporate Finance
        ("expense report", "expense_reports"),
        ("per diem", "expense_reports"),
        ("w2", "tax_records_w2"),
        ("w-2", "tax_records_w2"),
        ("1099", "tax_records_w2"),
        ("tax withholding", "tax_records_w2"),
        ("profit and loss", "pnl_statement"),
        ("pnl", "pnl_statement"),
        ("income statement", "pnl_statement"),
        ("ebitda", "pnl_statement"),
        ("invoice financing", "invoice_financing"),
        ("factoring", "invoice_financing"),
        ("accounts receivable", "invoice_financing"),
        # Original 6
        ("credit card", "credit_card_activity"),
        ("payroll", "payroll"),
        ("salary", "payroll"),
        ("saas", "saas_billing"),
        ("subscription", "saas_billing"),
        ("investment", "investment_statement"),
        ("stock", "investment_statement"),
        ("portfolio", "investment_statement"),
        ("insurance", "insurance_claims"),
        ("claim", "insurance_claims"),
        ("loan", "loans"),
        ("emi", "loans"),
    ]

    for keyword, entity in quick_map:
        if keyword in prompt_lower:
            return entity

    return ""
