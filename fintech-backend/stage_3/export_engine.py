# =====================================================
# EXPORT ENGINE — Dataset Serialization
# =====================================================
# Converts generated columns (numpy arrays) into
# downloadable formats: CSV, JSON, Parquet.
#
# Every export includes a metadata sidecar with
# generation provenance, tensor signature, and
# audit report summary.
# =====================================================

import json
import os
import time
import numpy as np
from typing import Any, Dict, Optional


def columns_to_records(
    columns: Dict[str, np.ndarray],
) -> list:
    """
    Convert column-oriented data to row-oriented records.

    Args:
        columns: Dict of variable_name -> numpy array

    Returns:
        List of dicts, one per row.
    """
    if not columns:
        return []

    n_rows = len(next(iter(columns.values())))
    col_names = sorted(columns.keys())

    records = []
    for i in range(n_rows):
        row = {}
        for col_name in col_names:
            val = columns[col_name][i]
            # Convert numpy types to Python native for JSON serialization
            if isinstance(val, (np.integer, np.int64, np.int32)):
                row[col_name] = int(val)
            elif isinstance(val, (np.floating, np.float64, np.float32)):
                float_val = float(val)
                if float_val.is_integer():
                    row[col_name] = int(float_val)
                else:
                    row[col_name] = round(float_val, 6)
            elif isinstance(val, np.bool_):
                row[col_name] = bool(val)
            else:
                row[col_name] = str(val) if val is not None else None
        records.append(row)

    return records


def export_csv(
    columns: Dict[str, np.ndarray],
    filepath: str,
) -> str:
    """Export dataset as CSV. Returns filepath."""
    records = columns_to_records(columns)
    if not records:
        return filepath

    col_names = sorted(columns.keys())

    with open(filepath, "w", encoding="utf-8", newline="") as f:
        # Header
        f.write(",".join(col_names) + "\n")

        # Rows
        for row in records:
            values = []
            for col in col_names:
                val = row.get(col, "")
                # Escape commas and quotes in string values
                s = str(val) if val is not None else ""
                if "," in s or '"' in s or "\n" in s:
                    s = '"' + s.replace('"', '""') + '"'
                values.append(s)
            f.write(",".join(values) + "\n")

    return filepath



def build_metadata_sidecar(
    entity: str,
    tensor_signature: str,
    n_rows: int,
    n_cols: int,
    generation_time_ms: float,
    audit_report: Dict[str, Any],
    variation_salt: int = 0,
) -> Dict[str, Any]:
    """
    Build the metadata sidecar that accompanies every dataset.
    This is the provenance chain that enterprise clients need.
    """
    return {
        "galarix_version": "1.0.0",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "entity": entity,
        "tensor_signature": tensor_signature,
        "variation_salt": variation_salt,
        "rows": n_rows,
        "columns": n_cols,
        "generation_time_ms": round(generation_time_ms, 2),
        "quality_score": audit_report.get("overall_score", 0),
        "quality_pass": audit_report.get("pass", False),
        "audit_summary": {
            "ks_tests_passed": sum(
                1 for t in audit_report.get("ks_tests", {}).values()
                if t.get("pass", False)
            ),
            "ks_tests_total": len(audit_report.get("ks_tests", {})),
            "correlation_residuals_passed": sum(
                1 for r in audit_report.get("correlation_residuals", {}).values()
                if r.get("pass", False)
            ),
            "correlation_residuals_total": len(audit_report.get("correlation_residuals", {})),
            "constraint_violations": sum(
                v.get("violations", 0)
                for v in audit_report.get("constraint_violations", {}).values()
            ),
            "uniqueness_score": audit_report.get("uniqueness_score", 0),
            "null_rate": audit_report.get("null_rate", 0),
            "anomaly_rate": audit_report.get("anomaly_check", {}).get("actual_rate", 0),
        },
    }
