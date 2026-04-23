from flask import Flask, jsonify
import requests
import pdfplumber
import re
import io
import os


app = Flask(__name__)

# Gujarat High Court Cause List URL
CAUSELIST_URL = "https://gujarathighcourt.nic.in/causelist"

@app.route("/")
def home():
    return "Court Tracker API Running"

@app.route("/get-cases")
def get_cases():
    try:
        # Step 1: Download PDF directly (if possible)
        pdf_url = "https://gujarathighcourt.nic.in/causelist/causelist.pdf"

        response = requests.get(pdf_url)
        pdf_file = io.BytesIO(response.content)

        # Step 2: Extract text
        text = ""
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                if page.extract_text():
                    text += page.extract_text()

        lines = text.split("\n")

        results = []
        current_court = "N/A"
        current_board_type = "N/A"

        for line in lines:

            board_match = re.search(r'(DAILY BOARD|SUPPLEMENTARY BOARD)', line, re.I)
            if board_match:
                current_board_type = board_match.group(1)

            court_match = re.search(r'COURT\s*ROOM\s*NO\s*:\s*(\d+)', line, re.I)
            if court_match:
                current_court = court_match.group(1)
                continue

            sr_match = re.match(r'^\s*(\d+)', line)
            case_match = re.search(r'[A-Z/]+/\d+/\d{4}', line)

            if sr_match and case_match:
                results.append({
                    "sr_no": sr_match.group(1),
                    "case_no": case_match.group(),
                    "court": current_court,
                    "board": current_board_type
                })

        return jsonify(results)

    except Exception as e:
        return jsonify({"error": str(e)})

# ==============================
# LIVE COURT STATUS API
# ==============================

@app.route("/live-status")
def live_status():
    try:
        API_URL = "https://gujarathighcourt.nic.in/streamingboard/indexrequest.php"

        payload = {
            "action": "allmattercallOut",
            "cmd": "allmattercallOut"
        }

        headers = {
            "User-Agent": "Mozilla/5.0",
            "X-Requested-With": "XMLHttpRequest"
        }

        response = requests.post(API_URL, headers=headers, data=payload)
        data = response.json()

        return jsonify(data)

    except Exception as e:
        return jsonify({"error": str(e)})

# ==============================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)