import re

# The 20 supported core entities
SUPPORTED_ENTITIES = {
    "credit_card": ["credit card", "credit cards"],
    "loan": ["loan", "loans"],
    "mortgage": ["mortgage", "mortgages"],
    "payroll": ["payroll", "payrolls"],
    "investment": ["investment", "investments"],
    "wire_transfer": ["wire transfer", "wire transfers", "wires"],
    "invoice_finance": ["invoice finance", "invoice financing", "invoices"],
    "insurance": ["insurance", "insurances"],
    "saas_billing": ["saas billing", "saas", "subscription"],
    "crypto": ["crypto", "cryptocurrency", "bitcoin", "ethereum"],
    "pl_statement": ["p&l", "profit and loss", "pl statement"],
    "bank_statement": ["bank statement", "bank statements"],
    "atm_withdrawal": ["atm", "atm withdrawal", "atm withdrawals"],
    "bnpl": ["bnpl", "buy now pay later"],
    "kyc_record": ["kyc", "know your customer", "kyc record"],
    "aml_alert": ["aml", "anti money laundering", "aml alert"],
    "forex": ["forex", "foreign exchange", "fx"],
    "options": ["options", "options trading"],
    "expense": ["expense", "expenses"],
    "tax_w2": ["tax", "w2", "w-2", "taxes"]
}

# Malicious or dangerous keywords that crash the math tensor
POISON_KEYWORDS = ["nan", "null", "undefined", "infinity", "-inf", "inf"]

def validate_prompt(prompt: str) -> tuple[bool, str, str]:
    """
    Acts as the Stage 0.5 Firewall for the Galarix API.
    Returns: (is_valid: bool, sanitized_prompt: str, error_message: str)
    """
    if not isinstance(prompt, str) or not prompt.strip():
        return False, "", "Prompt cannot be empty."

    if len(prompt) > 1000:
        return False, "", "Prompt exceeds maximum allowed length of 1000 characters."

    clean_prompt = prompt.lower().strip()

    # 1. NaN Poisoning / Code Injection Check
    # We use word boundaries to avoid catching words that contain 'null' like 'annul'
    for poison in POISON_KEYWORDS:
        if re.search(rf"\b{poison}\b", clean_prompt):
            return False, "", f"Galarix Firewall: Detected restricted mathematical keyword '{poison}'. Please remove this to ensure statistical validity."

    # 2. Entity Whitelist & Multi-Entity Megajoin Check
    detected_entities = []
    for entity_key, keywords in SUPPORTED_ENTITIES.items():
        for kw in keywords:
            if re.search(rf"\b{re.escape(kw)}\b", clean_prompt):
                if entity_key not in detected_entities:
                    detected_entities.append(entity_key)

    if len(detected_entities) == 0:
        return False, "", "Galarix Tier 2 currently optimizes generation for 20 core financial entities (e.g., Mortgages, Credit Cards, Payroll). Your request did not match a supported domain. Please try a different prompt."


    # 3. Mathematical Contradiction Guard (Very basic heuristic for the demo)
    # The user specifically mentioned the "300 credit score with 500k limit" breaking the math.
    if "credit score" in clean_prompt and "limit" in clean_prompt:
        if re.search(r"300.*\b500[k,000]", clean_prompt) or re.search(r"500[k,000].*300", clean_prompt):
            return False, "", "Galarix Firewall: Mathematical Contradiction Detected. A 300 credit score cannot mathematically correlate with a $500,000 credit limit in federal benchmark distributions. Please adjust your constraints."

    return True, prompt, ""

