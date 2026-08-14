"""
H2 Temporal Engine — Bulletproof Test
Tests all 7 fixes against the beast crypto prompt.
"""
import sys
sys.path.insert(0, ".")

from stage_1.contract_builder import build_stage1_contract
from stage_1.temporal_intent_extractor import extract_temporal_intent
from stage_1_5.enrichment_engine import enrich_contract
from stage_2.model_builder import build_statistical_model
from stage_3.generation_orchestrator import generate_dataset

PROMPT = "Generate 200 rows of volatile cryptocurrency trading data with weekly frequency over 2 years showing market crashes and regime shifts"

print(f"\n{'='*70}")
print(f"H2 TEMPORAL ENGINE TEST - BEAST CRYPTO PROMPT")
print(f"{'='*70}")
print(f"Prompt: {PROMPT}\n")

# Check temporal intent first (for period count test)
temporal_intent = extract_temporal_intent(PROMPT)

# Run the full pipeline
stage1_contract = build_stage1_contract(PROMPT, region="US")
contract = enrich_contract(stage1_contract)
model = build_statistical_model(contract)
result = generate_dataset(model, contract, rows=200)

print(f"\n{'='*70}")
print(f"TEST RESULTS")
print(f"{'='*70}")

if not result.get("success"):
    print(f"FAIL: GENERATION FAILED: {result.get('error')}")
    sys.exit(1)

data = result["data"]
n_rows = len(data)
print(f"OK: Generated {n_rows} rows")

# -- TEST 1: Period count (should be ~104 for 2 years weekly) --
print(f"\n--- TEST 1: Period Count ---")
if temporal_intent:
    periods = temporal_intent.get("periods", 0)
    print(f"   Parsed periods: {periods}")
    if 90 <= periods <= 120:
        print(f"   PASS: 2 years weekly = ~104 periods (got {periods})")
    else:
        print(f"   FAIL: Expected ~104 periods, got {periods}")
else:
    print(f"   FAIL: No temporal intent detected")

# -- TEST 2: Price sanity check --
print(f"\n--- TEST 2: Price Sanity ---")
price_cols = [k for k in data[0].keys() if "price" in k.lower()]
for col in price_cols:
    values = [float(row[col]) for row in data if row.get(col) is not None]
    if values:
        vmin, vmax = min(values), max(values)
        print(f"   {col}: min={vmin:.2f}, max={vmax:.2f}")
        if vmax > 1_000_000:
            print(f"   FAIL: Price exceeds $1M (got {vmax:.2f})")
        elif vmax < 1e-6:
            print(f"   FAIL: All prices are near-zero")
        else:
            print(f"   PASS: Prices are within realistic bounds")

# -- TEST 3: No zero-value trades --
print(f"\n--- TEST 3: Zero-Value Check ---")
amount_cols = [k for k in data[0].keys() if "amount" in k.lower() or "quantity" in k.lower()]
for col in amount_cols:
    values = [float(row[col]) for row in data if row.get(col) is not None]
    if values:
        n_zeros = sum(1 for v in values if abs(v) < 1e-10)
        pct_zeros = n_zeros / len(values) * 100
        print(f"   {col}: {n_zeros}/{len(values)} zeros ({pct_zeros:.1f}%)")
        if pct_zeros > 30:
            print(f"   WARN: High zero rate")
        else:
            print(f"   PASS")

# -- TEST 4: Regime diversity --
print(f"\n--- TEST 4: Regime Diversity ---")
if "_regime" in data[0]:
    regimes = [str(row["_regime"]) for row in data]
    unique_regimes = set(regimes)
    print(f"   Unique regimes: {unique_regimes}")
    if len(unique_regimes) >= 3:
        print(f"   PASS: {len(unique_regimes)} unique regimes")
    else:
        print(f"   FAIL: Only {len(unique_regimes)} regimes (need >= 3)")

    # Check regime distribution
    from collections import Counter
    regime_counts = Counter(regimes)
    for regime, count in sorted(regime_counts.items(), key=lambda x: -x[1]):
        pct = count / len(regimes) * 100
        print(f"   {regime}: {count} ({pct:.1f}%)")

    # Check max consecutive same-regime
    max_consec = 1
    current_consec = 1
    for i in range(1, len(regimes)):
        if regimes[i] == regimes[i-1]:
            current_consec += 1
            max_consec = max(max_consec, current_consec)
        else:
            current_consec = 1
    print(f"   Max consecutive same regime: {max_consec}")
    if max_consec > n_rows * 0.5:
        print(f"   FAIL: Regime stuck for > 50% of series")
    else:
        print(f"   PASS")
else:
    print(f"   FAIL: No _regime column found")

# -- TEST 5: Anomaly distribution --
print(f"\n--- TEST 5: Anomaly Distribution ---")
if "_is_anomaly" in data[0]:
    anomalies = [bool(row["_is_anomaly"]) for row in data]
    n_anomalies = sum(anomalies)
    pct = n_anomalies / len(anomalies) * 100
    print(f"   Total anomalies: {n_anomalies}/{len(anomalies)} ({pct:.1f}%)")

    # Check anomalies in each third
    third = len(anomalies) // 3
    first_third = sum(anomalies[:third])
    middle_third = sum(anomalies[third:2*third])
    last_third = sum(anomalies[2*third:])
    print(f"   First third:  {first_third}")
    print(f"   Middle third: {middle_third}")
    print(f"   Last third:   {last_third}")
    if last_third == 0:
        print(f"   FAIL: No anomalies in last third of series")
    else:
        print(f"   PASS: Anomalies distributed across full series")

    # Check anomaly types
    atypes = [str(row.get("_anomaly_type", "")) for row in data if row.get("_is_anomaly")]
    from collections import Counter
    type_counts = Counter(atypes)
    for atype, count in sorted(type_counts.items(), key=lambda x: -x[1]):
        print(f"   {atype}: {count}")
else:
    print(f"   FAIL: No _is_anomaly column found")

# -- TEST 6: Entity-specific regime names (Wyckoff for crypto) --
print(f"\n--- TEST 6: Entity-Specific Regimes ---")
if "_regime" in data[0]:
    regimes_set = set(str(row["_regime"]) for row in data)
    wyckoff_names = {"accumulation", "markup", "distribution", "markdown"}
    generic_names = {"normal", "stress", "crisis", "recovery"}
    if regimes_set & wyckoff_names:
        print(f"   PASS: Wyckoff phases detected: {regimes_set & wyckoff_names}")
    elif regimes_set & generic_names:
        print(f"   WARN: Generic regimes used instead of Wyckoff: {regimes_set}")
    else:
        print(f"   FAIL: Unknown regime names: {regimes_set}")

# -- TEST 7: Market value check --
print(f"\n--- TEST 7: Market Value Sanity ---")
mv_cols = [k for k in data[0].keys() if "market_value" in k.lower() or "current_price" in k.lower()]
for col in mv_cols:
    values = [float(row[col]) for row in data if row.get(col) is not None]
    if values:
        vmin, vmax = min(values), max(values)
        print(f"   {col}: min={vmin:.2f}, max={vmax:.2f}")
        if vmax > 1e12:
            print(f"   FAIL: Value exceeds $1T")
        else:
            print(f"   PASS")

print(f"\n{'='*70}")
print(f"TEST COMPLETE")
print(f"{'='*70}")
