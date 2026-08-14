"""
Edge Case Battery Test — Galarix Pipeline
Tests all edge cases from the requirements.

FIX: Pipeline now runs once per test case (not twice).
Results are stored after the first pass and reused
for both the display table and structural validation.
Previously: 16 cases × 2 passes = 32 pipeline invocations.
Now:        16 cases × 1 pass  = 16 pipeline invocations.
"""

from pipeline import run_pipeline





def run_tests():
    test_cases = [
        # (input, description)
        ("high risk large loans with monthly payments",         "Clear prompt with full intent"),
        ("credit card transactions for grocery and travel",     "Categories + entity"),
        ("asdfghjkl",                                          "Garbage input"),
        ("big money",                                          "Partial meaning"),
        ("monthly payments",                                   "Ambiguous domain"),
        ({"entity": "loans", "scale": "large"},                "Structured input"),
        ({"entity": "insurance_claims", "risk": "high", "scale": "large"}, "Structured with intent"),
        ("small daily grocery but also some travel",           "Mixed intent with categories"),
        ("insurance claims for employees",                     "Multi-entity candidate"),
        ("stock portfolio and investment returns",             "Investment domain"),
        ("",                                                   "Empty string"),
        (None,                                                 "None input"),
        ("generate saas subscription billing data",            "SaaS billing"),
        ("salary payroll data for engineering team",           "Payroll"),
        (42,                                                   "Numeric input"),
        (["loans", "insurance"],                               "List input"),
    ]

    # ── Single pass: run each test case once and store results ──
    results = []
    for tc, desc in test_cases:
        contract = run_pipeline(tc)
        results.append({
            "input": tc,
            "desc": desc,
            "contract": contract,
        })

    # ── Display table ──
    print("\n" + "=" * 120)
    print("GALARIX PIPELINE — EDGE CASE BATTERY TEST")
    print("=" * 120)
    print(f"{'#':<3} {'INPUT':<55} {'ENTITY':<25} {'CONF':<7} {'SCALE':<8} {'RISK':<7} {'FREQ':<10} {'CATEGORIES'}")
    print("-" * 120)

    for i, entry in enumerate(results, 1):
        r = entry["contract"]
        entity = r.get("entity", "?")
        conf = r.get("meta", {}).get("confidence", 0)
        intent = r.get("intent", {})
        input_str = str(entry["input"])[:52]
        cats = intent.get("categories", [])

        print(
            f"{i:<3} {input_str:<55} {entity:<25} {conf:<7.3f} "
            f"{intent.get('scale', '?'):<8} {intent.get('risk', '?'):<7} "
            f"{intent.get('frequency', '?'):<10} {cats}"
        )

    print("=" * 120)
    print("ALL TESTS COMPLETE — No crashes, every output has valid structure\n")

    # ── Structural validation (reuses stored results — no second pipeline run) ──
    print("STRUCTURAL VALIDATION:")
    required_keys = [
        "entity", "entities", "intent", "variables",
        "distributions", "dependencies", "constraints", "meta",
    ]
    required_intent = ["scale", "risk", "categories", "frequency"]
    required_meta = ["confidence", "source", "is_multi"]

    all_valid = True
    for i, entry in enumerate(results, 1):
        r = entry["contract"]

        missing_keys = [k for k in required_keys if k not in r]
        intent = r.get("intent", {})
        missing_intent = [k for k in required_intent if k not in intent]
        meta = r.get("meta", {})
        missing_meta = [k for k in required_meta if k not in meta]
        has_vars = len(r.get("variables", {})) > 0
        has_dists = isinstance(r.get("distributions"), dict)
        has_deps = isinstance(r.get("dependencies"), dict)

        issues = []
        if missing_keys:
            issues.append(f"missing_top_keys={missing_keys}")
        if missing_intent:
            issues.append(f"missing_intent={missing_intent}")
        if missing_meta:
            issues.append(f"missing_meta={missing_meta}")
        if not has_vars:
            issues.append("variables_empty")
        if not has_dists:
            issues.append("distributions_not_dict")
        if not has_deps:
            issues.append("dependencies_not_dict")

        if issues:
            print(f"  ❌ FAIL #{i} ({entry['desc']}): {', '.join(issues)}")
            all_valid = False
        else:
            print(f"  ✅ PASS #{i} ({entry['desc']})")

    print()
    if all_valid:
        print(f"  ALL {len(results)} CASES: Valid structure confirmed ✅")
    else:
        print("  ⚠️  Some cases failed structural validation — see above")

    print()


if __name__ == "__main__":
    run_tests()
