"""
DOMAIN REALISM AUDIT — What a fintech engineer would actually notice
"""
import json, math
import numpy as np

from stage_1.contract_builder import build_stage1_contract
from stage_1_5.enrichment_engine import enrich_contract
from stage_2.model_builder import build_statistical_model
from stage_3.generation_orchestrator import generate_dataset

def run_domain_audit():
    issues = []
    
    # ═══════════════ TEST 1: LOAN + EMI MATH ═══════════════
    print("="*60)
    print("TEST 1: Loan EMI Math Validation (200 rows)")
    print("="*60)
    
    s1 = build_stage1_contract("high risk massive loan defaults")
    s1_5 = enrich_contract(s1)
    model = build_statistical_model(s1_5)
    result = generate_dataset(model, s1_5, rows=200, variation_salt=7)
    data = result["data"]
    
    emi_errors = 0
    emi_checked = 0
    worst_ratio = 1.0
    for row in data:
        principal = row.get("loans_principal_amount")
        rate = row.get("loans_interest_rate")
        term_str = row.get("loans_loan_term_months")
        emi = row.get("loans_monthly_emi")
        
        if not all(isinstance(v, (int, float)) for v in [principal, rate, emi]):
            continue
        try:
            term = float(term_str)
        except:
            continue
        if term <= 0 or principal <= 0: continue
        
        emi_checked += 1
        monthly_rate = rate / 1200.0
        if monthly_rate > 0:
            expected = (principal * monthly_rate * (1 + monthly_rate)**term) / ((1 + monthly_rate)**term - 1)
        else:
            expected = principal / term
        
        if math.isfinite(expected) and expected > 0:
            ratio = emi / expected
            if ratio < 0.95 or ratio > 1.05:
                emi_errors += 1
                if abs(ratio - 1.0) > abs(worst_ratio - 1.0):
                    worst_ratio = ratio
                    print(f"  EMI ERROR: principal={principal:.2f}, rate={rate:.4f}%, term={term}, emi={emi:.2f}, expected={expected:.2f}, ratio={ratio:.4f}")
    
    print(f"  EMI Checked: {emi_checked}, Errors (>5% off): {emi_errors}, Worst ratio: {worst_ratio:.4f}")
    if emi_errors > 0:
        issues.append(f"EMI MATH: {emi_errors}/{emi_checked} rows have EMI deviation > 5%")
    
    # ═══════════════ TEST 2: PAYROLL NET < GROSS ═══════════════
    print("\n" + "="*60)
    print("TEST 2: Payroll Net < Gross (200 rows)")
    print("="*60)
    
    s1 = build_stage1_contract("comprehensive personal finances payroll and tax records")
    s1_5 = enrich_contract(s1)
    model = build_statistical_model(s1_5)
    result = generate_dataset(model, s1_5, rows=200, variation_salt=7)
    data = result["data"]
    
    violations = 0
    checked = 0
    for row in data:
        net = row.get("payroll_net_amount")
        gross = row.get("payroll_gross_amount")
        deductions = row.get("payroll_deductions")
        salary = row.get("payroll_salary_base")
        
        if isinstance(net, (int, float)) and isinstance(gross, (int, float)):
            checked += 1
            if net > gross:
                violations += 1
                print(f"  VIOLATION: net={net:.2f} > gross={gross:.2f} (salary={salary}, deductions={deductions})")
        
    print(f"  Checked: {checked}, Violations: {violations}")
    if violations > 0:
        issues.append(f"NET>GROSS: {violations}/{checked}")
    
    # Also check if deductions + net ≈ gross
    math_errors = 0
    for row in data:
        net = row.get("payroll_net_amount")
        gross = row.get("payroll_gross_amount")
        deductions = row.get("payroll_deductions")
        if all(isinstance(v, (int, float)) for v in [net, gross, deductions]):
            expected_net = gross - deductions
            if abs(net - expected_net) > 1.0:
                math_errors += 1
    print(f"  net ≠ gross-deductions: {math_errors}/{checked}")
    if math_errors > 10:
        issues.append(f"PAYROLL MATH: net != gross - deductions in {math_errors}/{checked} rows")
    
    # ═══════════════ TEST 3: CREDIT SCORE ↔ INTEREST RATE RELATIONSHIP ═══════════════
    print("\n" + "="*60)
    print("TEST 3: Credit Score ↔ Interest Rate Correlation")
    print("="*60)
    
    s1 = build_stage1_contract("high risk massive loan defaults")
    s1_5 = enrich_contract(s1)
    model = build_statistical_model(s1_5)
    result = generate_dataset(model, s1_5, rows=500, variation_salt=42)
    data = result["data"]
    
    high_score_high_rate = 0
    low_score_low_rate = 0
    total_with_both = 0
    for row in data:
        score = row.get("loans_credit_score")
        rate = row.get("loans_interest_rate")
        if isinstance(score, (int, float)) and isinstance(rate, (int, float)):
            total_with_both += 1
            if score >= 750 and rate > 15:
                high_score_high_rate += 1
            if score < 600 and rate < 8:
                low_score_low_rate += 1
    
    print(f"  Score>=750 & Rate>15%: {high_score_high_rate}/{total_with_both}")
    print(f"  Score<600 & Rate<8%: {low_score_low_rate}/{total_with_both}")
    # The schema has a conditional: if credit_score >= 750, then interest_rate max 8.0
    # So high_score_high_rate should be 0
    if high_score_high_rate > 5:
        issues.append(f"CONDITIONAL FAIL: {high_score_high_rate} rows with score>=750 but rate>15%")
    
    # ═══════════════ TEST 4: LOAN TYPE HOME → PRINCIPAL >= 50000 ═══════════════
    print("\n" + "="*60)
    print("TEST 4: Home Loan → Principal >= 50000 Conditional")
    print("="*60)
    
    home_loans_below_50k = 0
    home_loans_total = 0
    for row in data:
        lt = row.get("loans_loan_type")
        principal = row.get("loans_principal_amount")
        if lt == "Home" and isinstance(principal, (int, float)):
            home_loans_total += 1
            if principal < 50000:
                home_loans_below_50k += 1
                print(f"  HOME LOAN < 50K: principal={principal:.2f}")
    print(f"  Home loans: {home_loans_total}, Below 50K: {home_loans_below_50k}")
    if home_loans_below_50k > 0:
        issues.append(f"HOME LOAN CONDITIONAL FAIL: {home_loans_below_50k} home loans below 50K")
    
    # ═══════════════ FINAL ═══════════════
    print("\n" + "="*60)
    print("DOMAIN AUDIT FINAL SUMMARY")
    print("="*60)
    if issues:
        print(f"  ⚠ {len(issues)} DOMAIN-LEVEL ISSUES:")
        for iss in issues:
            print(f"    ✗ {iss}")
    else:
        print("  ✓ ALL DOMAIN CHECKS PASSED")

if __name__ == "__main__":
    run_domain_audit()
