from flask import Flask, request, jsonify
import pdfplumber
import io
import re
import requests
import os

app = Flask(__name__)

@app.route("/")
def home():
    return "Court Tracker API Running"


# ==============================
# ✅ NEW: UPLOAD PDF & EXTRACT
# ==============================
@app.route("/upload-pdf", methods=["POST"])
def upload_pdf():
    try:
        file = request.files["file"]

        pdf_bytes = file.read()
        pdf_file = io.BytesIO(pdf_bytes)

        text = ""

        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                if page.extract_text():
                    text += page.extract_text() + "\n"

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
# 🔴 LIVE STATUS (keep this)
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
        return response.json()

    except Exception as e:
        return jsonify({"error": str(e)})


# ==============================
# 🖥️ SIMPLE UI (optional but useful)
# ==============================
@app.route("/ui")
def ui():
    return """
    <h2>Upload Cause List PDF</h2>
    <input type="file" id="fileInput">
    <button onclick="uploadPDF()">Upload</button>
    <pre id="output"></pre>

    <script>
    function uploadPDF() {
        const file = document.getElementById("fileInput").files[0];
        let formData = new FormData();
        formData.append("file", file);

        fetch("/upload-pdf", {
            method: "POST",
            body: formData
        })
        .then(res => res.json())
        .then(data => {
            document.getElementById("output").innerText =
                JSON.stringify(data, null, 2);
        });
    }
    </script>
    """


# ==============================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)