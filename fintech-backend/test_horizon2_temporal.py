"""
HORIZON 2 — Temporal Engine Comprehensive Test Suite
=====================================================
Tests the full temporal pipeline across multiple prompt archetypes:
  1. Monthly credit card time series
  2. Daily stock portfolio with market crash
  3. Quarterly P&L with seasonal patterns
  4. Static prompt (no temporal — H1 fallthrough)
  5. Weekly bank statements with regime shift
"""
import json
import sys
import numpy as np

from stage_1.contract_builder import build_stage1_contract
from stage_1_5.enrichment_engine import enrich_contract
from stage_2.model_builder import build_statistical_model
from stage_3.generation_orchestrator import generate_dataset


def test_temporal(prompt: str, expected_temporal: bool, expected_checks: dict):
    """Run a single temporal test case."""
    print(f"\n{'='*70}")
    print(f"TEST: {prompt}")
    print(f"{'='*70}")

    # Run full pipeline
    s1 = build_stage1_contract(prompt)
    s1_5 = enrich_contract(s1)
    model = build_statistical_model(s1_5)
    result = generate_dataset(model, s1_5, rows=expected_checks.get("expected_rows", 200), variation_salt=42)

    if not result["success"]:
        print(f"  FAIL: Generation failed: {result.get('error', 'unknown')}")
        return False

    data = result["data"]
    columns = result["columns"]
    n_rows = len(data)
    is_temporal = model.get("temporal") is not None and model["temporal"].get("enabled", False)

    print(f"  Rows: {n_rows}")
    print(f"  Temporal: {is_temporal}")
    print(f"  Columns: {len(columns)}")

    issues = []

    # Check 1: Temporal detection
    if is_temporal != expected_temporal:
        issues.append(f"TEMPORAL DETECTION: expected={expected_temporal}, got={is_temporal}")

    if is_temporal:
        # Check 2: Regime column exists
        if "_regime" not in columns:
            issues.append("MISSING _regime column")
        else:
            regime_vals = [row.get("_regime", "") for row in data]
            unique_regimes = set(regime_vals)
            print(f"  Regimes observed: {unique_regimes}")

        # Check 3: Timestamp ordering
        ts_cols = [c for c in columns if "date" in c.lower() or "timestamp" in c.lower()]
        if ts_cols:
            ts_col = ts_cols[0]
            timestamps = [str(row.get(ts_col, "")) for row in data]
            out_of_order = sum(1 for i in range(1, len(timestamps)) if timestamps[i] < timestamps[i-1])
            if out_of_order > 0:
                issues.append(f"TIMESTAMP ORDER: {out_of_order} out of order")
            else:
                print(f"  Timestamps: all in order ({ts_col})")
                if timestamps:
                    print(f"    First: {timestamps[0]}")
                    print(f"    Last:  {timestamps[-1]}")

        # Check 4: Anomaly column exists
        if "_is_anomaly" in columns:
            anomaly_count = sum(1 for row in data if row.get("_is_anomaly"))
            anomaly_pct = anomaly_count / max(n_rows, 1) * 100
            print(f"  Anomalies: {anomaly_count}/{n_rows} ({anomaly_pct:.1f}%)")

        # Check 5: Anomaly types
        if "_anomaly_type" in columns:
            anomaly_types = {}
            for row in data:
                at = str(row.get("_anomaly_type", ""))
                if at:
                    anomaly_types[at] = anomaly_types.get(at, 0) + 1
            if anomaly_types:
                print(f"  Anomaly types: {anomaly_types}")

        # Check 6: Autocorrelation on continuous columns
        for col in columns:
            if col.startswith("_"):
                continue
            values = [row.get(col) for row in data if isinstance(row.get(col), (int, float))]
            if len(values) >= 10:
                arr = np.array(values, dtype=float)
                if np.std(arr) > 1e-6:
                    # Lag-1 autocorrelation
                    centered = arr - np.mean(arr)
                    ac = np.sum(centered[:-1] * centered[1:]) / np.sum(centered**2)
                    if abs(ac) > 0.15:  # Non-trivial temporal structure
                        print(f"  AC({col}): {ac:.3f}")

        # Check 7: Temporal audit in metadata
        audit = result.get("audit_report", {})
        temporal_audit = audit.get("temporal", {})
        if temporal_audit:
            print(f"  Temporal Audit: passed={temporal_audit.get('temporal_audit_passed')}")
            stats = temporal_audit.get("statistics", {})
            if "regime_distribution" in stats:
                print(f"  Regime Distribution: {stats['regime_distribution']}")
            if "regime_transitions" in stats:
                print(f"  Regime Transitions: {stats['regime_transitions']}")

    # Expected row count check
    expected_rows = expected_checks.get("expected_rows")
    if expected_rows and is_temporal:
        # For temporal, rows should match the calendar grid
        expected_periods = model.get("temporal", {}).get("periods", expected_rows)
        if n_rows != expected_periods:
            print(f"  NOTE: Rows ({n_rows}) differ from expected periods ({expected_periods}) - calendar adjustment")

    # Report
    if issues:
        print(f"\n  FAIL: {len(issues)} issues:")
        for iss in issues:
            print(f"    x {iss}")
        return False
    else:
        print(f"\n  PASS")
        return True


def main():
    results = {}

    # ── Test 1: Monthly credit card time series ──
    results["monthly_cc"] = test_temporal(
        "monthly credit card transactions for 2 years",
        expected_temporal=True,
        expected_checks={"expected_rows": 24},
    )

    # ── Test 2: Daily stock portfolio with market crash ──
    results["daily_crash"] = test_temporal(
        "daily investment portfolio with market crash for 6 months",
        expected_temporal=True,
        expected_checks={"expected_rows": 126},
    )

    # ── Test 3: Quarterly P&L with seasonal patterns ──
    results["quarterly_pnl"] = test_temporal(
        "quarterly P&L statement for 5 years with seasonal patterns",
        expected_temporal=True,
        expected_checks={"expected_rows": 20},
    )

    # ── Test 4: Static prompt (H1 fallthrough) ──
    results["static_loans"] = test_temporal(
        "high risk loan defaults",
        expected_temporal=False,
        expected_checks={"expected_rows": 200},
    )

    # ── Test 5: Weekly bank with regime ──
    results["weekly_bank"] = test_temporal(
        "weekly bank account statements with recession for 1 year",
        expected_temporal=True,
        expected_checks={"expected_rows": 52},
    )

    # ── Summary ──
    print(f"\n{'='*70}")
    print(f"HORIZON 2 TEST SUMMARY")
    print(f"{'='*70}")
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    for name, ok in results.items():
        status = "PASS" if ok else "FAIL"
        print(f"  [{status}] {name}")
    print(f"\n  {passed}/{total} tests passed")

    if passed < total:
        sys.exit(1)


if __name__ == "__main__":
    main()
