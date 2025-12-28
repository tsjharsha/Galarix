from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from faker import Faker
import json, time, random, csv, io
from datetime import datetime

app = Flask(__name__)
CORS(app)

fake = Faker()

# 🧠 In-memory prompt history
PROMPT_HISTORY = []

@app.route("/")
def home():
    return {
        "status": "Backend is running",
        "endpoints": [
            "/generate-stream (SSE)",
            "/download-csv",
            "/history",
            "/history/clear"
        ]
    }

# ================= STREAM GENERATOR =================
def generate_stream(prompt):
    total = 50
    transactions = []

    for i in range(total):
        time.sleep(0.05)

        transactions.append({
            "date": fake.date(),
            "amount": round(random.uniform(10, 5000), 2),
            "type": random.choice(["debit", "credit"])
        })

        progress = int(((i + 1) / total) * 100)
        yield f"data: {json.dumps({'progress': progress})}\n\n"

    # ✅ SAVE HISTORY (THIS WORKS)
    PROMPT_HISTORY.insert(0, {
        "prompt": prompt,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

    # ✅ FINAL EVENT
    yield f"data: {json.dumps({'done': True, 'transactions': transactions})}\n\n"

# ================= SSE ENDPOINT =================
@app.route("/generate-stream", methods=["GET"])
def generate_stream_api():
    prompt = request.args.get("prompt", "")

    # ✅ SAVE HISTORY IMMEDIATELY
    PROMPT_HISTORY.insert(0, {
        "prompt": prompt,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

    return Response(
        generate_stream(prompt),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive"
        }
    )

# ================= CSV DOWNLOAD =================
@app.route("/download-csv", methods=["POST"])
def download_csv():
    data = request.json
    transactions = data.get("transactions", [])

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=["date", "amount", "type"])
    writer.writeheader()
    writer.writerows(transactions)

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=transactions.csv"}
    )

# ================= HISTORY =================
@app.route("/history")
def history():
    return jsonify(PROMPT_HISTORY)

@app.route("/history/clear", methods=["POST"])
def clear_history():
    PROMPT_HISTORY.clear()
    return {"status": "cleared"}

if __name__ == "__main__":
    app.run(debug=True)
