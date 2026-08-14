# =====================================================
# TRUST REPORT BUILDER — Statistical Trust Certificate
# =====================================================
# Assembles the full trust certificate from validator
# and certifier outputs. Produces:
#   1. JSON trust certificate (API response)
#   2. PDF trust report (downloadable document)
#
# Scoring:
#   Distribution Fidelity:   25%
#   Regional Fidelity:       20% (HARD GATE)
#   Correlation Fidelity:    15%
#   Conditional Compliance:  15%
#   Derived Field Accuracy:  15%
#   Data Integrity:          10%
#
# Verdicts:
#   TRUSTED (≥85, regional PASS)
#   ACCEPTABLE (60-84, regional PASS)
#   REGIONAL MISMATCH (regional FAIL)
#   UNTRUSTED (<60)
# =====================================================

import time
import os
import numpy as np
from typing import Any, Dict, List, Optional

from trust_engine.statistical_validator import run_full_validation
from trust_engine.provenance_certifier import build_provenance_chain
from trust_engine.regional_benchmarks import get_benchmarks


# ─────────────────────────────────────────────────
# SCORING WEIGHTS
# ─────────────────────────────────────────────────
WEIGHTS = {
    "distribution_fidelity": 0.25,
    "regional_fidelity": 0.20,
    "correlation_fidelity": 0.15,
    "conditional_compliance": 0.15,
    "derived_accuracy": 0.15,
    "data_integrity": 0.10,
}


def build_trust_certificate(
    columns: Dict[str, np.ndarray],
    parameters: Dict[str, Any],
    covariance_list: List[Dict[str, Any]],
    dependencies: Dict[str, Any],
    entity: str,
    region: str,
    schema_sources: Dict[str, Any],
    audit_report: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Build the complete Statistical Trust Certificate.

    This is the MAIN ENTRY POINT for the trust engine.
    Call this after the quality auditor in the generation pipeline.

    Returns a structured certificate with:
      - Overall verdict (TRUSTED / ACCEPTABLE / REGIONAL MISMATCH / UNTRUSTED)
      - Trust score (0-100)
      - Detailed test results for every component
      - Full provenance chain with regional source citations
    """
    # ── Run full statistical validation ──
    validation = run_full_validation(
        columns, parameters, covariance_list,
        dependencies, entity, region,
    )

    # ── Build provenance chain ──
    provenance = build_provenance_chain(
        columns, parameters, entity, region, schema_sources,
    )

    # ── Compute component scores ──
    scores = _compute_component_scores(validation, audit_report)

    # ── Compute overall trust score ──
    trust_score = sum(
        scores[component]["score"] * weight
        for component, weight in WEIGHTS.items()
    )
    trust_score = round(min(100, max(0, trust_score)), 1)

    # ── Determine verdict ──
    regional_pass = validation["regional_fidelity"]["pass"]
    regional_hard_fail = validation["regional_fidelity"].get("hard_fail", False)

    if regional_hard_fail:
        verdict = "REGIONAL MISMATCH"
    elif trust_score >= 85 and regional_pass:
        verdict = "TRUSTED"
    elif trust_score >= 60 and regional_pass:
        verdict = "ACCEPTABLE"
    elif not regional_pass:
        verdict = "REGIONAL MISMATCH"
    else:
        verdict = "UNTRUSTED"

    # ── Build the trust badge (for frontend) ──
    badge = _build_trust_badge(verdict, trust_score, region)

    # ── Get row count ──
    n_rows = 0
    for col in columns.values():
        n_rows = len(col)
        break

    # ── Assemble certificate ──
    benchmarks = get_benchmarks(region)

    certificate = {
        "trust_certificate": {
            "version": "1.0.0",
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "entity": entity,
            "rows_audited": n_rows,

            "overall_verdict": verdict,
            "trust_score": trust_score,
            "trust_badge": badge,

            "region": {
                "code": region,
                "name": benchmarks["name"],
                "credit_system": benchmarks["credit_score"]["system"],
                "currency": benchmarks["currency"],
                "central_bank": benchmarks["central_bank"],
            },

            "distribution_fidelity": {
                "verdict": "PASS" if scores["distribution_fidelity"]["pass"] else "FAIL",
                "score": scores["distribution_fidelity"]["score"],
                "ks_pass_rate": validation["distribution_fidelity"]["ks_pass_rate"],
                "chi2_pass_rate": validation["distribution_fidelity"]["chi2_pass_rate"],
                "details": {
                    "ks_tests": validation["distribution_fidelity"]["ks_tests"],
                    "chi_square_tests": validation["distribution_fidelity"]["chi_square_tests"],
                    "emd_tests": validation["distribution_fidelity"]["emd_tests"],
                    "moments_tests": validation["distribution_fidelity"]["moments_tests"],
                },
            },

            "regional_fidelity": {
                "verdict": "PASS" if validation["regional_fidelity"]["pass"] else "FAIL",
                "hard_fail": regional_hard_fail,
                "checks_passed": validation["regional_fidelity"]["checks_passed"],
                "checks_total": validation["regional_fidelity"]["checks_total"],
                "details": validation["regional_fidelity"]["details"],
            },

            "correlation_fidelity": {
                "verdict": "PASS" if validation["correlation_fidelity"]["pass"] else "FAIL",
                "pairs_tested": validation["correlation_fidelity"]["pairs_tested"],
                "max_residual": validation["correlation_fidelity"]["max_residual"],
                "average_residual": validation["correlation_fidelity"]["average_residual"],
                "details": validation["correlation_fidelity"]["details"],
            },

            "conditional_compliance": {
                "verdict": "PASS" if validation["conditional_compliance"]["pass"] else "FAIL",
                "rules_tested": validation["conditional_compliance"]["rules_tested"],
                "total_violations": validation["conditional_compliance"]["total_violations"],
                "details": validation["conditional_compliance"]["details"],
            },

            "derived_field_accuracy": {
                "verdict": "PASS" if validation["derived_accuracy"]["pass"] else "FAIL",
                "fields_tested": validation["derived_accuracy"]["fields_tested"],
                "details": validation["derived_accuracy"]["details"],
            },

            "data_integrity": {
                "uniqueness_score": audit_report.get("uniqueness_score", 1.0),
                "null_rate": audit_report.get("null_rate", 0.0),
                "constraint_violations": sum(
                    v.get("violations", 0)
                    for v in audit_report.get("constraint_violations", {}).values()
                ),
            },

            "data_provenance": provenance,
        },
    }

    return certificate


# ─────────────────────────────────────────────────
# TRUST BADGE (for frontend display)
# ─────────────────────────────────────────────────

def _build_trust_badge(verdict: str, score: float, region: str) -> Dict[str, Any]:
    """
    Build a compact trust badge for frontend display.
    """
    badge_config = {
        "TRUSTED": {"emoji": "✅", "color": "#22c55e", "bg": "#f0fdf4", "label": "TRUSTED"},
        "ACCEPTABLE": {"emoji": "🟡", "color": "#eab308", "bg": "#fefce8", "label": "ACCEPTABLE"},
        "REGIONAL MISMATCH": {"emoji": "🔴", "color": "#ef4444", "bg": "#fef2f2", "label": "REGIONAL MISMATCH"},
        "UNTRUSTED": {"emoji": "❌", "color": "#ef4444", "bg": "#fef2f2", "label": "UNTRUSTED"},
    }

    config = badge_config.get(verdict, badge_config["UNTRUSTED"])
    benchmarks = get_benchmarks(region)

    return {
        "verdict": verdict,
        "score": score,
        "emoji": config["emoji"],
        "color": config["color"],
        "background": config["bg"],
        "label": f"{config['emoji']} Trust Score: {score} — {config['label']}",
        "region_label": f"{benchmarks['name']} ({benchmarks['credit_score']['system']})",
        "short_label": f"{score:.0f}",
    }


# ─────────────────────────────────────────────────
# SCORING ENGINE
# ─────────────────────────────────────────────────

def _compute_component_scores(
    validation: Dict[str, Any],
    audit_report: Dict[str, Any],
) -> Dict[str, Dict[str, Any]]:
    """Compute 0-100 scores for each trust component."""

    scores = {}

    # ── Distribution Fidelity ──
    ks_rate = validation["distribution_fidelity"]["ks_pass_rate"]
    chi2_rate = validation["distribution_fidelity"]["chi2_pass_rate"]
    emd_tests = validation["distribution_fidelity"]["emd_tests"]
    emd_pass_rate = (
        sum(1 for t in emd_tests.values() if t.get("pass", False)) / max(len(emd_tests), 1)
    )
    dist_score = (ks_rate * 40 + chi2_rate * 30 + emd_pass_rate * 30)
    scores["distribution_fidelity"] = {
        "score": round(dist_score, 1),
        "pass": bool(dist_score >= 60),
    }

    # ── Regional Fidelity ──
    rf = validation["regional_fidelity"]
    if rf.get("hard_fail", False):
        regional_score = 0.0
    elif rf["checks_total"] > 0:
        regional_score = (rf["checks_passed"] / rf["checks_total"]) * 100
    else:
        regional_score = 100.0  # No checks applicable = pass
    scores["regional_fidelity"] = {
        "score": round(regional_score, 1),
        "pass": bool(regional_score >= 80 and not rf.get("hard_fail", False)),
    }

    # ── Correlation Fidelity ──
    cf = validation["correlation_fidelity"]
    if cf["pairs_tested"] > 0:
        corr_score = 100 - min(100, cf["average_residual"] * 500)
    else:
        corr_score = 100.0
    scores["correlation_fidelity"] = {
        "score": round(max(0, corr_score), 1),
        "pass": cf["pass"],
    }

    # ── Conditional Compliance ──
    cc = validation["conditional_compliance"]
    if cc["rules_tested"] > 0:
        violations_per_rule = cc["total_violations"] / cc["rules_tested"]
        cond_score = max(0, 100 - violations_per_rule * 20)
    else:
        cond_score = 100.0
    scores["conditional_compliance"] = {
        "score": round(cond_score, 1),
        "pass": cc["pass"],
    }

    # ── Derived Field Accuracy ──
    da = validation["derived_accuracy"]
    if da["fields_tested"] > 0:
        pass_count = sum(1 for d in da["details"] if d.get("pass", False))
        derived_score = (pass_count / da["fields_tested"]) * 100
    else:
        derived_score = 100.0
    scores["derived_accuracy"] = {
        "score": round(derived_score, 1),
        "pass": da["pass"],
    }

    # ── Data Integrity ──
    uniqueness = audit_report.get("uniqueness_score", 1.0)
    null_rate = audit_report.get("null_rate", 0.0)
    violations = sum(
        v.get("violations", 0)
        for v in audit_report.get("constraint_violations", {}).values()
    )
    integrity_score = 100.0
    if uniqueness < 0.95:
        integrity_score -= 30
    elif uniqueness < 0.99:
        integrity_score -= 10
    if null_rate > 0:
        integrity_score -= 30
    if violations > 0:
        integrity_score -= 30
    scores["data_integrity"] = {
        "score": round(max(0, integrity_score), 1),
        "pass": bool(integrity_score >= 70),
    }

    return scores


# ─────────────────────────────────────────────────
# PDF REPORT GENERATION
# ─────────────────────────────────────────────────

try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    import tempfile
    import os
except ImportError:
    pass # Will be handled by requirements.txt update

def generate_trust_pdf(
    certificate: Dict[str, Any],
    output_path: str,
) -> str:
    """
    Generate a PDF trust report from the certificate.

    Uses pure-Python HTML-to-text approach to create a
    formatted plain-text report that can be saved as a
    readable document. For production PDF rendering,
    integrate with weasyprint or reportlab.

    Returns the output file path.
    """
    cert = certificate.get("trust_certificate", certificate)

    lines = []
    lines.append("=" * 70)
    lines.append("GALARIX — STATISTICAL TRUST CERTIFICATE")
    lines.append("=" * 70)
    lines.append("")
    lines.append(f"  Generated:    {cert.get('generated_at', 'N/A')}")
    lines.append(f"  Entity:       {cert.get('entity', 'N/A')}")
    lines.append(f"  Rows Audited: {cert.get('rows_audited', 0):,}")
    lines.append(f"  Version:      {cert.get('version', '1.0.0')}")
    lines.append("")

    # ── Overall Verdict ──
    lines.append("-" * 70)
    badge = cert.get("trust_badge", {})
    lines.append(f"  VERDICT:      {badge.get('label', cert.get('overall_verdict', 'N/A'))}")
    lines.append(f"  TRUST SCORE:  {cert.get('trust_score', 0):.1f} / 100")
    lines.append("-" * 70)
    lines.append("")

    # ── Region ──
    region = cert.get("region", {})
    lines.append("  REGION")
    lines.append(f"    Country:       {region.get('name', 'N/A')}")
    lines.append(f"    Credit System: {region.get('credit_system', 'N/A')}")
    lines.append(f"    Currency:      {region.get('currency', 'N/A')}")
    lines.append(f"    Central Bank:  {region.get('central_bank', 'N/A')}")
    lines.append("")

    # ── Component Scores ──
    lines.append("  COMPONENT SCORES")
    lines.append("  " + "-" * 50)

    dist = cert.get("distribution_fidelity", {})
    lines.append(f"    Distribution Fidelity:  [{dist.get('verdict', '?')}]")
    lines.append(f"      KS Pass Rate:    {dist.get('ks_pass_rate', 0):.0%}")
    lines.append(f"      Chi² Pass Rate:  {dist.get('chi2_pass_rate', 0):.0%}")

    rf = cert.get("regional_fidelity", {})
    lines.append(f"    Regional Fidelity:      [{rf.get('verdict', '?')}]")
    lines.append(f"      Checks Passed:   {rf.get('checks_passed', 0)}/{rf.get('checks_total', 0)}")
    if rf.get("hard_fail"):
        lines.append(f"      *** HARD FAIL: Data does not match claimed region ***")

    # Regional details
    for check_name, check_data in rf.get("details", {}).items():
        status = "✓" if check_data.get("pass") else "✗"
        lines.append(f"      {status} {check_name}: {_format_check_detail(check_data)}")

    corr = cert.get("correlation_fidelity", {})
    lines.append(f"    Correlation Fidelity:   [{corr.get('verdict', '?')}]")
    lines.append(f"      Pairs Tested:    {corr.get('pairs_tested', 0)}")
    lines.append(f"      Avg Residual:    {corr.get('average_residual', 0):.4f}")

    cond = cert.get("conditional_compliance", {})
    lines.append(f"    Conditional Compliance: [{cond.get('verdict', '?')}]")
    lines.append(f"      Rules Tested:    {cond.get('rules_tested', 0)}")
    lines.append(f"      Violations:      {cond.get('total_violations', 0)}")

    derived = cert.get("derived_field_accuracy", {})
    lines.append(f"    Derived Field Accuracy: [{derived.get('verdict', '?')}]")
    lines.append(f"      Fields Tested:   {derived.get('fields_tested', 0)}")

    integrity = cert.get("data_integrity", {})
    lines.append(f"    Data Integrity:")
    lines.append(f"      Uniqueness:      {integrity.get('uniqueness_score', 0):.4f}")
    lines.append(f"      Null Rate:       {integrity.get('null_rate', 0):.6f}")
    lines.append(f"      Violations:      {integrity.get('constraint_violations', 0)}")
    lines.append("")

    # ── Data Provenance ──
    prov = cert.get("data_provenance", {})
    lines.append("  DATA PROVENANCE")
    lines.append("  " + "-" * 50)
    lines.append(f"    Primary Source:  {prov.get('primary_source', 'N/A')}")
    lines.append(f"    Region:          {prov.get('region_name', 'N/A')} ({prov.get('region', '')})")
    lines.append(f"    Central Bank:    {prov.get('central_bank', 'N/A')}")
    lines.append(f"    Variables Cited:  {prov.get('variables_sourced', 0)}")
    lines.append("")

    for entry in prov.get("provenance_chain", []):
        lines.append(f"    [{entry.get('variable', '?')}]")
        lines.append(f"      Distribution: {entry.get('distribution', '?')}")
        lines.append(f"      Source:       {entry.get('source', '?')}")
        if entry.get("regional_source"):
            lines.append(f"      Region Auth:  {entry['regional_source']}")
        if entry.get("scoring_system"):
            lines.append(f"      Score System: {entry['scoring_system']} ({entry.get('score_range', '')})")
        if entry.get("currency"):
            lines.append(f"      Currency:     {entry['currency']}")
        if entry.get("implied_median"):
            lines.append(f"      Imp. Median:  {entry['implied_median']}")
        if entry.get("verification"):
            lines.append(f"      Verification: {entry['verification']}")
        lines.append("")

    # ── Footer ──
    lines.append("=" * 70)
    lines.append("  GALARIX ENGINE — Behavior-Driven Synthetic Data")
    lines.append("  This certificate is auto-generated. All distribution")
    lines.append("  parameters are grounded in publicly available data")
    lines.append("  from central banks, credit bureaus, and statistical agencies.")
    lines.append("=" * 70)

    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)

    # Write to PDF using reportlab
    c = canvas.Canvas(output_path, pagesize=letter)
    width, height = letter
    
    # Starting coordinates
    x = 40
    y = height - 40
    
    c.setFont("Courier", 10)
    
    for line in lines:
        if y < 40:
            c.showPage()
            c.setFont("Courier", 10)
            y = height - 40
        c.drawString(x, y, line)
        y -= 12 # Line spacing

    c.save()

    return output_path


def _format_check_detail(check: Dict[str, Any]) -> str:
    """Format a single regional check detail for the report."""
    parts = []
    if "expected" in check:
        parts.append(f"expected={check['expected']}")
    if "actual" in check:
        parts.append(f"actual={check['actual']}")
    elif "actual_range" in check:
        parts.append(f"actual={check['actual_range']}")
    if "deviation_pct" in check:
        parts.append(f"dev={check['deviation_pct']}%")
    return ", ".join(parts) if parts else str(check)
