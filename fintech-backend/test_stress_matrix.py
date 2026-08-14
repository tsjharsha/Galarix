import json
import time
import numpy as np
import traceback
from stage_1.contract_builder import build_stage1_contract
from stage_1_5.enrichment_engine import enrich_contract
from stage_2.model_builder import build_statistical_model
from stage_3.generation_orchestrator import generate_dataset

def get_base_contract():
    stage1 = build_stage1_contract("mortgage records", region="US")
    return enrich_contract(stage1)

def run_test(name, func):
    print(f"\n[{name}] Running...")
    try:
        res = func()
        if isinstance(res, dict) and not res.get("success", True):
            print(f"[{name}] FAIL (Handled gracefully): {res.get('error')}")
        else:
            print(f"[{name}] WARNING: Passed without error (or returned silently). Vulnerability might exist.")
    except Exception as e:
        print(f"[{name}] CRITICAL FAIL (Unhandled Exception): {type(e).__name__}: {str(e)}")
        # traceback.print_exc()

def test_zero_variance():
    # Mutate the statistical model to have zero variance
    contract = get_base_contract()
    stat_model = build_statistical_model(contract)
    # find a column and set its std to 0
    if "mortgage records property value" in stat_model.get("marginals", {}):
        stat_model["marginals"]["mortgage records property value"]["std"] = 0.0
    return generate_dataset(stat_model, contract, rows=100)

def test_negative_time_steps():
    contract = get_base_contract()
    contract["intent"]["start_date"] = "2025-01-01"
    contract["intent"]["end_date"] = "2020-01-01"
    stat_model = build_statistical_model(contract)
    return generate_dataset(stat_model, contract, rows=100)

def test_infinite_volatility():
    contract = get_base_contract()
    stat_model = build_statistical_model(contract)
    # Inject garch params > 1 if they exist
    if "temporal_profiles" in stat_model:
        for col, profile in stat_model["temporal_profiles"].items():
            if "garch" in profile:
                profile["garch"]["alpha"] = 0.8
                profile["garch"]["beta"] = 0.8
    return generate_dataset(stat_model, contract, rows=100)

def test_nan_poisoning():
    contract = get_base_contract()
    stat_model = build_statistical_model(contract)
    # Inject NaN into a mean
    col = list(stat_model.get("marginals", {}).keys())[0]
    stat_model["marginals"][col]["mean"] = float('nan')
    return generate_dataset(stat_model, contract, rows=100)

def test_impossible_conditions():
    contract = get_base_contract()
    # Assuming conditions format
    contract["constraints"] = {
        "impossible_rule": "age < 18 AND mortgage_status == 'Approved'"
    }
    stat_model = build_statistical_model(contract)
    return generate_dataset(stat_model, contract, rows=100)

def test_p_value_hack():
    contract = get_base_contract()
    stat_model = build_statistical_model(contract)
    # Generate 5 rows
    res = generate_dataset(stat_model, contract, rows=5)
    cert = res.get("trust_certificate", {}).get("trust_certificate", {})
    print(f"  -> Overall Verdict: {cert.get('overall_verdict')}")
    print(f"  -> Trust Score: {cert.get('trust_score')}")
    return res

def test_categorical_imbalance():
    contract = get_base_contract()
    # Force default rate to 90% (might just be setting probabilities)
    if "mortgage records loan type" in contract.get("distributions", {}):
        contract["distributions"]["mortgage records loan type"] = {"Fixed": 0.1, "ARM": 0.9}
    stat_model = build_statistical_model(contract)
    res = generate_dataset(stat_model, contract, rows=100)
    cert = res.get("trust_certificate", {}).get("trust_certificate", {})
    print(f"  -> Verdict: {cert.get('overall_verdict')}")
    return res

if __name__ == '__main__':
    print("==================================================")
    print("GALARIX MASTER STRESS TEST - VULNERABILITY SWEEP")
    print("==================================================")
    run_test("Stage 2: Zero Variance", test_zero_variance)
    run_test("Stage 2: Negative Time Steps", test_negative_time_steps)
    run_test("Stage 2: Infinite Volatility", test_infinite_volatility)
    run_test("Stage 2: NaN Poisoning", test_nan_poisoning)
    run_test("Stage 3: Impossible Conditions", test_impossible_conditions)
    run_test("Trust Engine: P-Value Hack", test_p_value_hack)
    run_test("Trust Engine: Categorical Imbalance", test_categorical_imbalance)
    print("==================================================")
    print("SWEEP COMPLETE")
