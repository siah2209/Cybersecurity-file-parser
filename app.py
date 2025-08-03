from flask import Flask, request, jsonify, send_file
import os
import io
from test_parser import scan_directory, fetch_keywords_from_db, print_results

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

app = Flask(__name__)

# Store scan results in memory
scanned_results = []

def draw_wrapped_text(c, text, x, y, max_chars=90, indent=10, line_height=14):
    import textwrap
    lines = textwrap.wrap(text, width=max_chars)
    for i, line in enumerate(lines):
        offset_x = x if i == 0 else x + indent
        c.drawString(offset_x, y, line)
        y -= line_height
        if y < 100:
            c.showPage()
            y = 750
    return y



@app.route("/analyze", methods=["POST"])
def analyze():
    global scanned_results
    data = request.get_json()
    raw_input_path = data.get("directory")
    directory = os.path.normpath(raw_input_path)

    print("====================================")
    print(f"📥 RAW input path: {raw_input_path}")
    print(f"🛠 Normalized path: {directory}")
    print(f"✅ Path exists? {os.path.exists(directory)}")

    if not os.path.exists(directory):
        return jsonify({"error": "Directory not found"}), 404

    try:
        keywords = fetch_keywords_from_db()
        print(f"🧠 Loaded {len(keywords)} keywords from database")

        scanned_results = scan_directory(directory, keywords)
        print(f"✅ Scan complete. {len(scanned_results)} files processed.")

        print_results(scanned_results)

        return jsonify({"message": "Scan complete. Results are ready to view/download."})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route("/view", methods=["POST"])
def view():
    try:
        if not scanned_results:
            return jsonify({"error": "No scan results available yet."}), 400

        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter
        y = height - 50
        line_height = 14

        for idx, result in enumerate(scanned_results, start=1):
            c.setFont("Helvetica-Bold", 12)
            c.drawString(50, y, f"Document {idx}: {result['file']}")
            y -= line_height
            c.setFont("Helvetica", 10)
            c.drawString(50, y, f"Path: {result['path']}")
            y -= line_height
            c.drawString(50, y, f"Hash: {result['hash']}")
            y -= line_height
            c.drawString(50, y, f"Risk Score: {result['score']:.2f}")
            y -= line_height * 2

            if result['keywords']:
                c.setFont("Helvetica-Bold", 10)
                c.drawString(50, y, "Keyword Matches:")
                y -= line_height
                c.setFont("Helvetica", 10)
                for keyword, entries in result['keywords'].items():
                    c.drawString(60, y, f"- {keyword}")
                    y -= line_height
                    for score, sentence in entries:
                        full_text = f'• "{sentence}" (Score: {score:.4f})'
                        y = draw_wrapped_text(c, full_text, 70, y)

                        if y < 100:
                            c.showPage()
                            y = height - 50
            else:
                c.drawString(50, y, "No keyword matches.")
                y -= line_height

            if result['warnings']:
                c.drawString(50, y, "Warning Words:")
                y -= line_height
                for word, count in result['warnings'].items():
                    c.drawString(60, y, f"- {word}: {count}")
                    y -= line_height
            else:
                c.drawString(50, y, "No warning words detected.")
                y -= line_height

            if result.get("stego"):
                c.setFont("Helvetica-Bold", 10)
                c.drawString(50, y, "Stego Message:")
                y -= line_height
                c.setFont("Helvetica", 10)
                for line in result['stego'].splitlines():
                    y = draw_wrapped_text(c, line, 60, y)

                    if y < 100:
                        c.showPage()
                        y = height - 50

            c.drawString(50, y, "-" * 80)
            y -= line_height * 2

            if y < 100:
                c.showPage()
                y = height - 50

        c.save()
        buffer.seek(0)

        return send_file(
            buffer,
            as_attachment=True,
            download_name="scan_results.pdf",
            mimetype="application/pdf"
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/")
def index():
    # Load the HTML page
    with open("File-parse-test.html", "r", encoding="utf-8") as f:
        html = f.read()
    return html

if __name__ == "__main__":
    app.run(debug=True)
