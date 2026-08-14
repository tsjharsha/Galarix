import hashlib
import json
import math

from stage_1.contract_builder import build_stage1_contract
from stage_1_5.enrichment_engine import enrich_contract
from stage_2.model_builder import build_statistical_model
from stage_3.generation_orchestrator import generate_dataset


def _stable_hash(value):
    payload = json.dumps(value, sort_keys=True, default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def test_stage3_determinism_and_loan_math():
    prompt = "Generate 250 high risk personal loan records with user profiles"
    contract = enrich_contract(build_stage1_contract(prompt))
    model = build_statistical_model(contract)

    first = generate_dataset(model, contract, rows=250, variation_salt=0)
    second = generate_dataset(model, contract, rows=250, variation_salt=0)

    assert first["success"], first.get("error")
    assert second["success"], second.get("error")
    assert _stable_hash(first["data"]) == _stable_hash(second["data"])
    assert _stable_hash(first["audit_report"]) == _stable_hash(second["audit_report"])

    for row in first["data"][:50]:
        principal = float(row["loans_principal_amount"])
        rate = float(row["loans_interest_rate"])
        months = float(row["loans_loan_term_months"])
        emi = float(row["loans_monthly_emi"])

        assert principal >= 0
        assert 0 <= rate <= 100
        assert months > 0
        assert emi > 0

        monthly_rate = rate / 1200
        if monthly_rate == 0:
            expected = principal / months
        else:
            expected = (
                principal
                * monthly_rate
                * math.pow(1 + monthly_rate, months)
                / (math.pow(1 + monthly_rate, months) - 1)
            )
        assert abs(emi - expected) / max(expected, 1.0) < 0.02


if __name__ == "__main__":
    test_stage3_determinism_and_loan_math()
    print("Stage 3 hardening checks passed.")
