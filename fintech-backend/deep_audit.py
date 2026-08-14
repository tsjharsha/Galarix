"""
DEEP AUDIT — Exhaustive Stage 3 Diagnostic
Runs multiple prompt archetypes through the full pipeline and reports
every numerical anomaly, logical inconsistency, and semantic failure.
"""
import json, sys, math
import numpy as np

from stage_1.contract_builder import build_stage1_contract
from stage_1_5.enrichment_engine import enrich_contract
from stage_2.model_builder import build_statistical_model
from stage_3.generation_orchestrator import generate_dataset

PROMPTS = [
    "high risk massive loan defaults",
    "normal personal credit card transactions",
    "comprehensive personal finances payroll and tax records",
    "small business bank accounts low risk",
    "high frequency forex trading volatile market",
]

def run_audit():
    all_issues = {}
    
    for prompt in PROMPTS:
        print(f"\n{'='*60}")
        print(f"PROMPT: {prompt}")
        print(f"{'='*60}")
        issues = []
        
        s1 = build_stage1_contract(prompt)
        s1_5 = enrich_contract(s1)
        model = build_statistical_model(s1_5)
        result = generate_dataset(model, s1_5, rows=200, variation_salt=7)
        
        if not result["success"]:
            issues.append(f"GENERATION FAILED: {result.get('error','unknown')}")
            all_issues[prompt] = issues
            continue
        
        data = result["data"]
        columns = result["columns"]
        entity = result["entity"]
        behavior = model.get("behavior_used", {})
        parameters = model.get("parameters", {})
        dependencies = model.get("dependencies", {})
        
        print(f"  Entity: {entity}")
        print(f"  Rows: {len(data)}")
        print(f"  Columns: {columns}")
        print(f"  Behavior: mean_mult={behavior.get('mean_multiplier',0):.3f}, var_mult={behavior.get('variance_multiplier',0):.3f}, anomaly_rate={behavior.get('anomaly_rate',0):.3f}")
        
        # ── CHECK 1: Interest rate realism ──
        for col in columns:
            if "interest_rate" in col:
                rates = [r[col] for r in data if isinstance(r.get(col), (int, float))]
                if rates:
                    max_r = max(rates)
                    min_r = min(rates)
                    avg_r = sum(rates)/len(rates)
                    above_30 = sum(1 for r in rates if r > 30)
                    below_1 = sum(1 for r in rates if r < 1.0)
                    print(f"  Interest Rate [{col}]: min={min_r:.2f} max={max_r:.2f} avg={avg_r:.2f} above30={above_30} below1={below_1}")
                    if max_r > 35: issues.append(f"INTEREST RATE too high: {max_r:.2f}% in {col}")
                    if above_30 / len(rates) > 0.5: issues.append(f"INTEREST RATE: {above_30}/{len(rates)} rows above 30% — unrealistic clustering")
                    if below_1 > 0 and min_r < 0.5: issues.append(f"INTEREST RATE impossibly low: {min_r:.4f}% in {col}")
        
        # ── CHECK 2: Credit score realism ──
        for col in columns:
            if "credit_score" in col:
                scores = [r[col] for r in data if isinstance(r.get(col), (int, float))]
                if scores:
                    min_s = min(scores)
                    max_s = max(scores)
                    exact_300 = sum(1 for s in scores if s == 300)
                    exact_850 = sum(1 for s in scores if s == 850)
                    print(f"  Credit Score [{col}]: min={min_s:.0f} max={max_s:.0f} exact300={exact_300} exact850={exact_850}")
                    if min_s < 300: issues.append(f"CREDIT SCORE below 300: {min_s}")
                    if max_s > 850: issues.append(f"CREDIT SCORE above 850: {max_s}")
                    if exact_300 > 5: issues.append(f"CREDIT SCORE wall effect at 300: {exact_300} rows")
                    if exact_850 > 5: issues.append(f"CREDIT SCORE wall effect at 850: {exact_850} rows")
        
        # ── CHECK 3: Principal / loan amount realism ──
        for col in columns:
            if "principal" in col or "loan_amount" in col:
                amts = [r[col] for r in data if isinstance(r.get(col), (int, float))]
                if amts:
                    max_a = max(amts)
                    min_a = min(amts)
                    print(f"  Loan Amount [{col}]: min={min_a:.2f} max={max_a:.2f}")
                    exact_max = sum(1 for a in amts if a == 10000000)
                    exact_min = sum(1 for a in amts if a == 1000)
                    if exact_max > 3: issues.append(f"LOAN AMOUNT wall at 10M: {exact_max} rows")
                    if exact_min > 3: issues.append(f"LOAN AMOUNT wall at 1000: {exact_min} rows")
        
        # ── CHECK 4: EMI / Monthly Payment math check ──
        for col in columns:
            if "emi" in col or "monthly_payment" in col:
                bad_emi = 0
                for row in data:
                    emi_val = row.get(col)
                    # Find principal, rate, term in the same row
                    principal = None
                    rate = None
                    term = None
                    for k, v in row.items():
                        if ("principal" in k or "loan_amount" in k) and isinstance(v, (int, float)):
                            principal = v
                        if "interest_rate" in k and isinstance(v, (int, float)):
                            rate = v
                        if "term" in k and isinstance(v, (int, float, str)):
                            try: term = float(v)
                            except: pass
                    
                    if principal and rate and term and term > 0 and isinstance(emi_val, (int, float)):
                        monthly_rate = rate / 1200.0
                        if monthly_rate > 0:
                            expected = (principal * monthly_rate * (1 + monthly_rate)**term) / ((1 + monthly_rate)**term - 1)
                            if math.isfinite(expected) and expected > 0:
                                ratio = emi_val / expected if expected > 0 else 0
                                if ratio < 0.5 or ratio > 2.0:
                                    bad_emi += 1
                
                if bad_emi > 0:
                    print(f"  EMI Math Error [{col}]: {bad_emi}/{len(data)} rows with >2x or <0.5x expected EMI")
                    issues.append(f"EMI MATH: {bad_emi}/{len(data)} rows have wrong EMI calculation")
        
        # ── CHECK 5: Categorical distribution respect ──
        for col in columns:
            if "loan_status" in col or "loan_type" in col or "account_type" in col:
                counts = {}
                for row in data:
                    v = row.get(col, "MISSING")
                    counts[v] = counts.get(v, 0) + 1
                print(f"  Categorical [{col}]: {counts}")
                if "Default" in counts and "default" in prompt.lower():
                    pct = counts["Default"] / len(data) * 100
                    if pct < 10: issues.append(f"CATEGORICAL SHIFT FAIL: prompt says 'defaults' but only {pct:.1f}% Default")
        
        # ── CHECK 6: Net < Gross for payroll ──
        for col in columns:
            if "net" in col.lower() and "amount" in col.lower():
                gross_col = None
                for c2 in columns:
                    if "gross" in c2.lower() and "amount" in c2.lower():
                        gross_col = c2
                if gross_col:
                    violations = 0
                    for row in data:
                        net = row.get(col, 0)
                        gross = row.get(gross_col, 0)
                        if isinstance(net, (int, float)) and isinstance(gross, (int, float)):
                            if net > gross:
                                violations += 1
                    if violations > 0:
                        print(f"  NET > GROSS VIOLATION: {violations}/{len(data)} rows")
                        issues.append(f"NET > GROSS: {violations}/{len(data)} rows where net_amount > gross_amount")
        
        # ── CHECK 7: Semantic consistency (email matches name) ──
        email_col = None
        fname_col = None
        lname_col = None
        for col in columns:
            if "email" in col: email_col = col
            if "first_name" in col: fname_col = col
            if "last_name" in col: lname_col = col
        
        if email_col and fname_col and lname_col:
            mismatches = 0
            for row in data:
                email = str(row.get(email_col, ""))
                fname = str(row.get(fname_col, "")).lower()
                lname = str(row.get(lname_col, "")).lower()
                if fname not in email or lname not in email:
                    mismatches += 1
            if mismatches > 0:
                pct = mismatches / len(data) * 100
                print(f"  EMAIL MISMATCH: {mismatches}/{len(data)} ({pct:.0f}%) emails don't match first+last name")
                if pct > 5: issues.append(f"SEMANTIC WEAVER FAIL: {pct:.0f}% emails don't match names")
        
        # ── CHECK 8: Duplicate rows ──
        row_strs = set()
        dups = 0
        for row in data:
            rs = str(sorted(row.items()))
            if rs in row_strs:
                dups += 1
            row_strs.add(rs)
        if dups > 0:
            print(f"  DUPLICATES: {dups}")
            issues.append(f"DUPLICATE ROWS: {dups}")
        
        # ── CHECK 9: NaN/None/Inf values ──
        nulls = 0
        infs = 0
        for row in data:
            for k, v in row.items():
                if k == "_is_anomaly": continue
                if v is None:
                    nulls += 1
                elif isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
                    infs += 1
                elif isinstance(v, str) and v.lower() in ("nan", "inf", "-inf", "none"):
                    nulls += 1
        if nulls > 0: issues.append(f"NULL VALUES: {nulls} cells")
        if infs > 0: issues.append(f"INF VALUES: {infs} cells")
        
        # ── CHECK 10: loan_term_months should be reasonable integers ──
        for col in columns:
            if "term" in col and "month" in col:
                bad_terms = 0
                for row in data:
                    v = row.get(col)
                    try:
                        t = float(v)
                        if t < 1 or t > 600: bad_terms += 1
                    except: pass
                if bad_terms > 0:
                    issues.append(f"LOAN TERM: {bad_terms} rows with unrealistic term months")
        
        # ── REPORT ──
        if issues:
            print(f"\n  ⚠ {len(issues)} ISSUES FOUND:")
            for iss in issues:
                print(f"    ✗ {iss}")
        else:
            print(f"\n  ✓ CLEAN — No issues found")
        
        all_issues[prompt] = issues
    
    # ── FINAL SUMMARY ──
    print(f"\n{'='*60}")
    print(f"FINAL AUDIT SUMMARY")
    print(f"{'='*60}")
    total_issues = sum(len(v) for v in all_issues.values())
    for prompt, issues in all_issues.items():
        status = "PASS" if not issues else f"FAIL ({len(issues)} issues)"
        print(f"  [{status}] {prompt}")
    print(f"\nTotal issues across all prompts: {total_issues}")

if __name__ == "__main__":
    run_audit()
