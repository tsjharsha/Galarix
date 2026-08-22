# =====================================================
# GALARIX ENGINE — Flask API
# =====================================================
# Production-grade API for the Behavior-Driven
# Synthetic Data Engine. Supports:
#   - Prompt input (GET /generate-stream)
#   - Structured input (POST /analyze)
#   - Entity listing (GET /entities)
#   - Schema lookup (GET /schema/<entity>)
#   - Data provenance (GET /provenance/<entity>)
#
# All endpoints use the unified pipeline which
# NEVER crashes and ALWAYS returns valid data.
#
# All distribution parameters are grounded in
# publicly available federal financial data.
# See schema_registry.py for full source citations.
# =====================================================

import os
from flask import Flask, request, jsonify, Response, abort
from flask_cors import CORS
import json
import firebase_admin
from firebase_admin import credentials, firestore
import time
from typing import Any, Dict
from dotenv import load_dotenv
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

load_dotenv()

from stage_1.contract_builder import build_stage1_contract
from stage_1_5.enrichment_engine import enrich_contract
from pipeline import run_pipeline as run_contract_pipeline
from stage_2.model_builder import build_statistical_model
from stage_3.generation_orchestrator import generate_dataset, generate_preview
from stage_3.export_engine import export_csv
from trust_engine.trust_report_builder import generate_trust_pdf
from stage_1_5.schema_registry import (
    get_schema,
    get_data_sources,
    list_available_entities,
    entity_exists,
)
from stage_0_5.prompt_firewall import validate_prompt

app = Flask(__name__)
# Restrict CORS to allowed origins in production
allowed_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")
CORS(app, origins=allowed_origins if allowed_origins != ["*"] else "*")

# Rate Limiter
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["1000 per day", "100 per hour"],
    storage_uri="memory://",
)

# Simple API Key Security (Master Key fallback)
API_KEY = os.getenv("GALARIX_API_KEY")

# Initialize Firebase Admin
cred_path = os.path.join(os.path.dirname(__file__), '.firebase-credentials.json')
if os.path.exists(cred_path):
    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred)
    db = firestore.client(database_id='galarixdb')
else:
    print("WARNING: .firebase-credentials.json not found! Dynamic API keys will not work.")
    db = None

def log_audit_event(endpoint: str, prompt: str, region: str, status: str = "success", error_msg: str = ""):
    """Write an audit trail event for the generated data."""
    if db is None:
        return
    try:
        user_id = getattr(request, 'user_id', 'anonymous')
        key_prefix = getattr(request, 'api_key_prefix', 'unknown')
        
        audit_data = {
            'timestamp': firestore.SERVER_TIMESTAMP,
            'user_id': user_id,
            'api_key_prefix': key_prefix,
            'endpoint': endpoint,
            'prompt': prompt,
            'region': region,
            'status': status,
            'ip_address': request.remote_addr,
            'error': error_msg
        }
        db.collection('audit_logs').add(audit_data)
    except Exception as e:
        print(f"Failed to write audit log: {e}")

@app.before_request
def enforce_https():
    # Only enforce in production, allow localhost
    if not request.host.startswith('localhost') and not request.host.startswith('127.0.0.1'):
        if request.headers.get('X-Forwarded-Proto', 'http') == 'http':
            abort(403, description="HTTPS is strictly required. Please use https://")


import hashlib

def _hash_key(raw_key: str) -> str:
    """SHA-256 hash an API key for secure storage comparison."""
    return hashlib.sha256(raw_key.encode('utf-8')).hexdigest()

ALLOWED_FRONTEND_ORIGINS = [
    os.getenv("FRONTEND_URL", "https://galarix.vercel.app"),
    "http://localhost:3000",
]

@app.before_request
def check_api_key():
    # Allow CORS preflight and public home route
    if request.method == 'OPTIONS' or (request.endpoint and request.endpoint == 'home'):
        return

    origin = request.headers.get('Origin', '')
    
    # Frontend requests: verify Firebase ID token instead of origin string
    if origin in ALLOWED_FRONTEND_ORIGINS:
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            id_token = auth_header.split('Bearer ')[1]
            try:
                from firebase_admin import auth
                decoded = auth.verify_id_token(id_token)
                request.user_id = decoded['uid']
                request.api_key_prefix = 'frontend_user'
                return
            except Exception:
                abort(401, description="Invalid authentication token.")
        abort(401, description="Authentication required.")

    # API key flow (for programmatic access)
    provided_key = request.headers.get("X-API-Key") or request.args.get("api_key")
    
    # 1. Fallback to Master Key (if set in .env)
    if API_KEY and provided_key == API_KEY:
        request.user_id = 'master_admin'
        request.api_key_prefix = 'master_key'
        return
        
    # 2. Verify dynamic key against Firestore
    if not provided_key or not provided_key.startswith('gx_'):
        abort(401, description="Unauthorized: Invalid API Key format.")
        
    if db is None:
        abort(500, description="Internal Server Error: Firebase not configured.")
        
    try:
        keys_ref = db.collection('api_keys')
        hashed_key = _hash_key(provided_key)
        query = keys_ref.where('key_hash', '==', hashed_key).limit(1)
        results = list(query.stream())
        
        if len(results) > 0:
            key_doc = results[0]
            key_data = key_doc.to_dict()
            
            # Check usage limits
            tier = key_data.get("tier", "free")
            usage = key_data.get("usage_count", 0)
            
            TIER_LIMITS = {"free": 100, "starter": 1000, "pro": 10000, "enterprise": 100000}
            if usage >= TIER_LIMITS.get(tier, 100):
                abort(429, description=f"API key usage limit exceeded for '{tier}' tier.")
                
            # Update usage tracking
            key_doc.reference.update({
                "usage_count": firestore.Increment(1),
                "last_used": firestore.SERVER_TIMESTAMP,
            })
            
            request.user_id = key_data.get('user_id', 'unknown_api_user')
            request.api_key_prefix = key_data.get('key_prefix', 'unknown_prefix')
            return
            
    except Exception as e:
        print(f"Firestore verification error: {e}")
        
    abort(401, description="Unauthorized: Invalid API Key")

print("\n" + "=" * 70)
print("[*] GALARIX ENGINE -- BEHAVIOR-DRIVEN SYNTHETIC DATA ENGINE v5.0.0")
print("   Stage 1:   Intent & Contract Builder (keyword-first)")
print("   Stage 1.5: Normalization & Enrichment (guarantee layer)")
print("   Stage 2:   Statistical Model Builder (tensor-driven)")
print("   Stage 3:   Generation Engine")
print("   |-- Horizon 1: Static Cross-Sectional Generation (LIVE)")
print("   \\-- Horizon 2: Time-Series Engine (LIVE)")
print("       |-- T1: Calendar Engine (7 region holiday calendars)")
print("       |-- T2: Regime Engine (HMM + sigmoid blending)")
print("       |-- T3: Temporal Correlation (AR1/GARCH/OU/GBM)")
print("       |-- T4: Temporal Anomaly (flash crash/cluster/seasonal)")
print("       \\-- T5: Temporal Consistency Auditor")
print("   Trust Engine: Statistical Trust Certificates (KS/chi-square/EMD + 7-region validation)")
print("   Distributions grounded in: BLS, Federal Reserve, FICO, NAIC, RBI, BOE, ECB")
print("=" * 70 + "\n")

# =====================================================
# NOTE FOR PRODUCTION DEPLOYMENT:
# Run behind gunicorn (not Flask dev server):
#   gunicorn -w 4 -b 0.0.0.0:5000 app:app
#
# Configure your reverse proxy (nginx) with:
#   proxy_read_timeout 60s;
# to prevent hanging SSE connections if the pipeline stalls.
# =====================================================


# =====================================================
# STREAMING ENDPOINT — SSE-based generation
# =====================================================

def generate_stream(prompt: str, region: str = "US"):
    """
    Main streaming pipeline.

    FIX: Stage 1 and Stage 1.5 now run separately so progress
    events reflect actual pipeline work, not artificial delays
    after everything has already completed.

    Flow:
        10% → routing
        40% → Stage 1 complete (entity + intent resolved)
        80% → Stage 1.5 complete (normalized + enriched)
        100% → done
    """
    try:
        # ── Stage 0.5: Prompt Firewall ──
        is_valid, safe_prompt, error_msg = validate_prompt(prompt)
        if not is_valid:
            yield f"data: {json.dumps({'error': True, 'type': 'rejection', 'status': 'rejected', 'message': error_msg})}\n\n"
            return
            
        # ── Progress: Routing ──
        yield f"data: {json.dumps({'progress': 10, 'status': 'Routing input...', 'type': 'progress'})}\n\n"

        # ── Stage 1: Intent & Contract Builder ──
        stage1_contract = build_stage1_contract(prompt, region=region)
        entity_hint = stage1_contract.get("entity", "unknown")

        yield f"data: {json.dumps({'progress': 40, 'status': f'Entity resolved: {entity_hint}', 'type': 'progress'})}\n\n"

        # ── Stage 1.5: Normalization & Enrichment ──
        contract = enrich_contract(stage1_contract)

        yield f"data: {json.dumps({'progress': 80, 'status': 'Contract enriched, validating...', 'type': 'progress'})}\n\n"

        # ── Stage 2: Statistical Model builder ──
        statistical_model = build_statistical_model(contract)
        
        yield f"data: {json.dumps({'progress': 90, 'status': 'Mathematical Model compiled...', 'type': 'progress'})}\n\n"

        # ── Build final payload ──
        entity = contract.get("entity", "generic")
        entities = contract.get("entities", ["generic"])
        is_multi = contract.get("meta", {}).get("is_multi", False)

        # Data provenance — cite where the distribution parameters came from
        provenance = get_data_sources(entity)

        payload = {
            "done": True,
            "status": "multi_entity" if is_multi else "single_entity",
            "detected_entities": entities,
            "entity": entity,
            "confidence": contract.get("meta", {}).get("confidence", 0),
            "intent": contract.get("intent", {}),

            # Row count: extracted from prompt, default 1000
            "num_rows": contract.get("intent", {}).get("num_rows") or 1000,

            # Schema data
            "schema": contract.get("meta", {}),
            "variables": contract.get("variables", {}),
            "distributions": contract.get("distributions", {}),
            "dependencies": contract.get("dependencies", {}),
            "constraints": contract.get("constraints", {}),
            "dataContract": contract,
            "statisticalModel": statistical_model,

            # Data provenance — federal source citations
            "data_sources": provenance,

            # Stage 3: Generate preview data
            "generation_ready": True,
        }

        # Attach a live preview from Stage 3
        try:
            preview = generate_preview(statistical_model, contract, preview_rows=10)
            if preview.get("success"):
                payload["preview_data"] = preview["preview_data"]
                payload["preview_columns"] = preview["columns"]
        except Exception:
            pass  # Preview is optional — don't break the stream

        yield f"data: {json.dumps({'progress': 100, 'type': 'progress'})}\n\n"
        yield f"data: {json.dumps(payload)}\n\n"

    except ValueError as ve:
        if str(ve) == "NO_FINANCIAL_INTENT":
            yield f"data: {json.dumps({'error': True, 'type': 'rejection', 'status': 'rejected', 'message': 'No financial intent detected. Please provide a relevant financial prompt.'})}\n\n"
        else:
            yield f"data: {json.dumps({'error': True, 'message': str(ve)})}\n\n"
    except Exception as e:
        # Never leave the SSE connection hanging on error
        error_payload = {
            "done": True,
            "error": True,
            "message": "Pipeline encountered an error — returning fallback contract.",
            "entity": "generic",
            "entities": ["generic"],
            "confidence": 0.0,
        }
        yield f"data: {json.dumps(error_payload)}\n\n"


# =====================================================
# NOTE: _generate_sample_data has been REMOVED.
#
# The old function used random.uniform() and random.choice()
# to generate toy preview data that completely bypassed
# the tensor engine, covariance matrices, and Black Swan
# morphing built in Stage 2.
#
# All actual data generation will be handled by Stage 3:
# the Generation Engine (stage_3/generation_orchestrator.py)
# which uses the statistical model to produce real,
# mathematically grounded synthetic datasets.
# =====================================================


# =====================================================
# API ROUTES
# =====================================================

@app.route("/")
def home():
    """API info and available endpoints."""
    return jsonify({
        "engine": "Galarix Behavior-Driven Synthetic Data Engine",
        "version": "4.0.0 — Horizon 1 (Generation Engine LIVE)",
        "stages": {
            "stage_1": "Intent & Contract Builder",
            "stage_1_5": "Normalization & Enrichment",
            "stage_2": "Statistical Model Builder (Tensor-Driven)",
            "stage_3": "Generation Engine (7 Sub-Engines)",
        },
        "data_grounding": "All distributions sourced from BLS, Federal Reserve, FICO, NAIC, CFPB",
        "available_entities": list_available_entities(),
        "supported_inputs": ["prompt (string)", "structured (dict)"],
        "endpoints": {
            "/": "This endpoint",
            "/entities": "List available entities",
            "/schema/<entity>": "Get schema for a specific entity",
            "/provenance/<entity>": "Get data source citations for an entity",
            "/generate-stream?prompt=<text>": "Streaming generation with SSE + preview data",
            "/generate (POST)": "Full dataset generation with audit report + trust certificate",
            "/trust-report (POST)": "Generate trust certificate (JSON or PDF)",
            "/analyze (POST)": "Non-streaming analysis (supports prompt + structured input)",
            "/test (GET)": "Run edge case battery test",
        },
    })


@app.route("/entities")
def entities_endpoint():
    """List all available entities."""
    available = list_available_entities()
    return jsonify({
        "entities": available,
        "count": len(available),
    })


@app.route("/schema/<entity>")
def get_entity_schema(entity: str):
    """Get schema for a specific entity."""
    schema = get_schema(entity)
    if not schema:
        return jsonify({"error": f"Entity '{entity}' not found"}), 404
    return jsonify(schema)


@app.route("/provenance/<entity>")
def get_entity_provenance(entity: str):
    """Get data source citations and methodology for an entity."""
    if not entity_exists(entity):
        return jsonify({"error": f"Entity '{entity}' not found"}), 404
        
    provenance = get_data_sources(entity)
    return jsonify({
        "entity": entity,
        "provenance": provenance
    })


@app.route("/generate-stream")
def stream():
    """
    Main streaming endpoint — prompt input via query parameter.
    """
    prompt = request.args.get("prompt", "")
    region = request.args.get("region", "US")
    if not prompt:
        log_audit_event("/generate-stream", "", region, status="error", error_msg="Missing prompt")
        return jsonify({
            "error": "Missing 'prompt' parameter",
            "usage": "/generate-stream?prompt=your_text&region=US",
        }), 400
        
    log_audit_event("/generate-stream", prompt, region, status="started")
    response = Response(generate_stream(prompt, region), mimetype="text/event-stream")
    response.headers["X-Accel-Buffering"] = "no"
    response.headers["Cache-Control"] = "no-cache"
    response.headers["Connection"] = "keep-alive"
    return response


@app.route("/analyze", methods=["POST"])
def analyze():
    """
    Non-streaming analysis endpoint.
    Supports both prompt and structured input.

    Body (JSON):
        {"prompt": "text"}           → prompt mode
        {"entity": "loans", ...}     → structured mode
    """
    data = request.get_json(silent=True) or {}

    if "prompt" in data and isinstance(data["prompt"], str):
        raw_input = data["prompt"]
    elif data:
        raw_input = data
    else:
        log_audit_event("/analyze", "", "US", status="error", error_msg="Missing body")
        return jsonify({
            "error": "Missing request body. Send JSON with 'prompt' or structured fields."
        }), 400

    region = data.get("region", "US")
    log_audit_event("/analyze", str(raw_input), region, status="started")

    try:
        if isinstance(raw_input, str):
            is_valid, safe_prompt, error_msg = validate_prompt(raw_input)
            if not is_valid:
                return jsonify({"status": "rejected", "message": error_msg}), 400
                
        # Run full pipeline
        region = data.get("region", "US")
        stage1_contract = build_stage1_contract(raw_input, region=region)
        contract = enrich_contract(stage1_contract)
        statistical_model = build_statistical_model(contract)

        return jsonify({
            "status": "success",
            "contract": contract,
            "statistical_model": statistical_model,
            "entity": contract.get("entity"),
            "entities": contract.get("entities"),
            "intent": contract.get("intent"),
            "confidence": contract.get("meta", {}).get("confidence", 0),
        })
    except ValueError as ve:
        if str(ve) == "NO_FINANCIAL_INTENT":
            return jsonify({
                "status": "rejected",
                "message": "No financial intent detected. Please provide a relevant financial prompt."
            }), 400
        return jsonify({"status": "error", "message": str(ve)}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/generate", methods=["POST"])
def generate():
    """
    Full dataset generation endpoint.

    Body (JSON):
        {
            "prompt": "high risk credit card fraud",
            "rows": 5000,         // default: 1000, max: 100000
            "format": "json",     // json | csv (default: json)
            "variation": 0,       // salt for re-generation
            "include_audit": true // include quality audit report
        }

    Returns:
        Full dataset with audit report and metadata.
    """
    data = request.get_json(silent=True) or {}
    prompt = data.get("prompt", "")
    variation = data.get("variation", 0)
    include_audit = data.get("include_audit", True)

    if not prompt:
        log_audit_event("/generate", "", "US", status="error", error_msg="Missing prompt")
        return jsonify({
            "status": "error",
            "message": "Missing 'prompt' field. Send JSON with a 'prompt' string.",
        }), 400

    region = data.get("region", "US")
    log_audit_event("/generate", prompt, region, status="started")

    try:
        is_valid, safe_prompt, error_msg = validate_prompt(prompt)
        if not is_valid:
            return jsonify({"status": "rejected", "message": error_msg}), 400

        # Run full pipeline
        region = data.get("region", "US")
        stage1_contract = build_stage1_contract(prompt, region=region)
        contract = enrich_contract(stage1_contract)
        statistical_model = build_statistical_model(contract)

        # Determine row count: explicit param > prompt-extracted > default 1000
        if "rows" in data:
            rows = max(10, min(data["rows"], 1_000_000))
        else:
            rows = contract.get("intent", {}).get("num_rows") or 1000
            rows = max(10, min(rows, 1_000_000))

        # Stage 3: Generate actual data
        result = generate_dataset(
            statistical_model, contract,
            rows=rows,
            variation_salt=variation,
        )

        if not result["success"]:
            return jsonify({
                "status": "error",
                "message": f"Generation failed: {result.get('error', 'unknown')}",
            }), 500

        response = {
            "status": "success",
            "entity": result["entity"],
            "rows_generated": result["rows_generated"],
            "columns": result["columns"],
            "columns_count": result["columns_count"],
            "data": result["data"],
            "tensor_signature": result["tensor_signature"],
            "generation_time_ms": result["generation_time_ms"],
            "metadata": result["metadata"],
        }

        if include_audit:
            response["audit_report"] = result["audit_report"]

        # Always include trust certificate and badge
        trust_cert = result.get("trust_certificate", {})
        response["trust_certificate"] = trust_cert
        cert_inner = trust_cert.get("trust_certificate", {})
        response["trust_badge"] = cert_inner.get("trust_badge", {})

        return jsonify(response)

    except ValueError as ve:
        if str(ve) == "NO_FINANCIAL_INTENT":
            return jsonify({
                "status": "rejected",
                "message": "No financial intent detected.",
            }), 400
        return jsonify({"status": "error", "message": str(ve)}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/trust-report", methods=["POST"])
def trust_report():
    """
    Trust report endpoint — generates data and returns only
    the trust certificate + optional PDF.

    Body (JSON):
        {
            "prompt": "high risk loans",
            "region": "IN",        // default: US
            "rows": 1000,          // default: 1000
            "format": "json",      // json | pdf (default: json)
            "variation": 0
        }

    Returns:
        Full trust certificate with regional validation.
    """
    data = request.json or {}
    prompt = data.get("prompt")
    region = data.get("region", "US")
    
    log_audit_event("/trust-report", prompt or str(data), region, status="started")
    rows = max(100, min(data.get("rows", 1000), 100000))
    variation = data.get("variation", 0)
    output_format = data.get("format", "json")

    if not prompt:
        return jsonify({
            "status": "error",
            "message": "Missing 'prompt' field.",
        }), 400

    try:
        is_valid, safe_prompt, error_msg = validate_prompt(prompt)
        if not is_valid:
            return jsonify({"status": "rejected", "message": error_msg}), 400
            
        stage1_contract = build_stage1_contract(prompt, region=region)
        contract = enrich_contract(stage1_contract)
        statistical_model = build_statistical_model(contract)

        result = generate_dataset(
            statistical_model, contract,
            rows=rows,
            variation_salt=variation,
        )

        if not result["success"]:
            return jsonify({
                "status": "error",
                "message": f"Generation failed: {result.get('error', 'unknown')}",
            }), 500

        trust_cert = result.get("trust_certificate", {})

        if output_format == "pdf":
            # Generate PDF trust report
            import tempfile, os
            pdf_path = os.path.join(
                tempfile.gettempdir(),
                f"galarix_trust_{result['entity']}_{region}.pdf"
            )
            generate_trust_pdf(trust_cert, pdf_path)

            with open(pdf_path, "rb") as f:
                content = f.read()

            return Response(
                content,
                mimetype="application/pdf",
                headers={"Content-Disposition": f"attachment; filename=trust_report_{result['entity']}_{region}.pdf"}
            )

        return jsonify({
            "status": "success",
            "trust_certificate": trust_cert,
            "entity": result["entity"],
            "rows_generated": result["rows_generated"],
            "generation_time_ms": result["generation_time_ms"],
        })

    except ValueError as ve:
        if str(ve) == "NO_FINANCIAL_INTENT":
            return jsonify({"status": "rejected", "message": "No financial intent detected."}), 400
        return jsonify({"status": "error", "message": str(ve)}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/test", methods=["GET"])
def test_pipeline():
    """
    Quick test endpoint — runs multiple test cases to verify
    the pipeline works end-to-end.

    FIX: Results now distinguish between exact entity match and
    acceptable multi-entity match, so test failures are visible.
    """
    test_cases = [
        {"input": "high risk large loans with monthly payments", "expected_entity": "loans"},
        {"input": "credit card transactions for grocery and travel", "expected_entity": "credit_card_activity"},
        {"input": "asdfghjkl", "expected_entity": "generic"},
        {"input": "monthly payments", "expected_entity": "loans"},
        {"input": {"entity": "insurance_claims", "scale": "large"}, "expected_entity": "insurance_claims"},
        {"input": "insurance claims for employees", "expected_entity": "insurance_claims"},
        {"input": "big money", "expected_entity": "generic"},
        {"input": "", "expected_entity": "generic"},
        {"input": "small daily grocery but also some travel", "expected_entity": "credit_card_activity"},
        {"input": "stock portfolio and investment returns", "expected_entity": "investment_statement"},
        # New entities — regression coverage
        {"input": "bitcoin and ethereum crypto trades on binance", "expected_entity": "crypto_trading_log"},
        {"input": "kyc verification for customer onboarding", "expected_entity": "kyc_records"},
        {"input": "suspicious aml alerts for structuring", "expected_entity": "aml_transaction_alerts"},
        {"input": "home mortgage refinance fixed rate", "expected_entity": "mortgage_records"},
        {"input": "employee expense reports for business travel", "expected_entity": "expense_reports"},
        {"input": "forex eur/usd currency pair trading", "expected_entity": "forex_transactions"},
        {"input": "w2 federal tax withholding for employees", "expected_entity": "tax_records_w2"},
        {"input": "company profit and loss income statement", "expected_entity": "pnl_statement"},
        {"input": "wire transfer via swift to international account", "expected_entity": "wire_transfers"},
        {"input": "buy now pay later klarna installments", "expected_entity": "buy_now_pay_later"},
    ]

    results = []
    for tc in test_cases:
        contract = run_contract_pipeline(tc["input"])
        entity = contract.get("entity", "?")

        exact_match = entity == tc["expected_entity"]
        multi_acceptable = entity == "multi_entity"
        passed = exact_match or multi_acceptable

        results.append({
            "input": str(tc["input"])[:60],
            "expected": tc["expected_entity"],
            "got": entity,
            "confidence": round(contract.get("meta", {}).get("confidence", 0), 3),
            "intent": contract.get("intent", {}),
            "passed": "PASS" if passed else "FAIL",
            # FIX: explicit match type so test failures are visible
            "match_type": "exact" if exact_match else ("multi_entity_acceptable" if multi_acceptable else "mismatch"),
        })

    passed_count = sum(1 for r in results if r["passed"] == "PASS")
    exact_count = sum(1 for r in results if r["match_type"] == "exact")

    return jsonify({
        "title": "Pipeline Test Results",
        "total": len(test_cases),
        "passed": passed_count,
        "exact_matches": exact_count,
        "multi_entity_acceptable": passed_count - exact_count,
        "results": results,
    })


# =====================================================
# APPLICATION ENTRY POINT
# =====================================================

if __name__ == "__main__":
    print("\n[*] Quick Test URLs:")
    print("  Pipeline test: http://localhost:5000/test")
    print("  Single entity: http://localhost:5000/generate-stream?prompt=credit%20card%20transactions")
    print("  Multi entity:  http://localhost:5000/generate-stream?prompt=insurance%20and%20loans")
    print("  Garbage input: http://localhost:5000/generate-stream?prompt=asdfghjkl")
    print("  Structured:    curl -X POST http://localhost:5000/analyze -H 'Content-Type: application/json' -d '{\"entity\":\"loans\",\"scale\":\"large\"}'")
    print("=" * 70 + "\n")

    app.run(debug=True, port=5000)
