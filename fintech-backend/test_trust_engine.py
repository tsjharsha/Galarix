import json
import time
from stage_1.contract_builder import build_stage1_contract
from stage_1_5.enrichment_engine import enrich_contract
from stage_2.model_builder import build_statistical_model
from stage_3.generation_orchestrator import generate_dataset

def test_region(region_code: str):
    print(f"\n{'='*60}")
    print(f"TESTING REGION: {region_code}")
    print(f"{'='*60}")

    prompt = "personal loans with interest rates and credit scores"
    
    print("1. Building Contract...")
    stage1 = build_stage1_contract(prompt, region=region_code)
    contract = enrich_contract(stage1)
    
    print("2. Building Statistical Model...")
    stat_model = build_statistical_model(contract)
    
    print("3. Generating Dataset & Trust Certificate...")
    start_t = time.time()
    result = generate_dataset(stat_model, contract, rows=1000)
    end_t = time.time()
    
    if not result.get("success"):
        print(f"FAILED: Generation error: {result.get('error')}")
        return
        
    trust_cert = result.get("trust_certificate", {}).get("trust_certificate", {})
    if not trust_cert:
        print("FAILED: No trust certificate found!")
        return
        
    print(f"Generation took: {end_t - start_t:.2f}s")
    print(f"Verdict: {trust_cert.get('overall_verdict')}")
    print(f"Trust Score: {trust_cert.get('trust_score')}")
    print(f"Region: {trust_cert.get('region', {}).get('name')} ({trust_cert.get('region', {}).get('credit_system')})")
    
    # Check Regional Fidelity
    rf = trust_cert.get("regional_fidelity", {})
    print(f"Regional Fidelity Verdict: {rf.get('verdict')}")
    if rf.get('hard_fail'):
        print(">>> HARD FAIL TRIGGERED <<<")
        
    print("\nRegional Details:")
    for k, v in rf.get("details", {}).items():
        status = "PASS" if v.get("pass") else "FAIL"
        print(f"  [{status}] {k}: {v}")
        
    # Check Provenance
    prov = trust_cert.get("data_provenance", {})
    print(f"\nProvenance Central Bank: {prov.get('central_bank')}")
    print("Provenance Chain Sample:")
    for item in prov.get("chain", prov.get("provenance_chain", []))[:3]:
        print(f"  - {item.get('variable')}: {item.get('source')} (System: {item.get('scoring_system', 'N/A')})")
        if "verification" in item:
            print(f"    Verification: {item['verification']}")

if __name__ == "__main__":
    for region in ["US", "IN", "UK", "JP"]:
        test_region(region)
