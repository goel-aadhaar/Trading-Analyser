#!/usr/bin/env python3
"""
Mobile-friendly web app for the Trading Data Analyzer.

Run with:
    python web_app.py

Then open the shown URL from a phone on the same Wi-Fi network.
"""

from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
import os
import traceback
import tempfile
from pathlib import Path

from flask import Flask, render_template_string, request
from werkzeug.utils import secure_filename

from trading_data_analyzer import TradingDataExtractor


ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tiff", ".tif"}
MAX_FILES_PER_REQUEST = 4

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024


PAGE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Trading Data Analyzer</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #f6f7f9;
      --ink: #17202a;
      --muted: #5f6b7a;
      --line: #d7dde5;
      --accent: #146c94;
      --accent-strong: #0f5474;
      --danger: #b42318;
      --panel: #ffffff;
      --buy: #137333;
      --sell: #b42318;
    }

    * {
      box-sizing: border-box;
    }

    body {
      margin: 0;
      min-height: 100vh;
      background: var(--bg);
      color: var(--ink);
      font-family: Arial, Helvetica, sans-serif;
      line-height: 1.45;
    }

    main {
      width: min(720px, 100%);
      margin: 0 auto;
      padding: 22px 16px 36px;
    }

    header {
      padding: 10px 0 18px;
    }

    h1 {
      margin: 0 0 8px;
      font-size: 28px;
      line-height: 1.12;
      letter-spacing: 0;
    }

    p {
      margin: 0;
      color: var(--muted);
    }

    form {
      margin-top: 18px;
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 16px;
    }

    label {
      display: block;
      margin-bottom: 8px;
      font-weight: 700;
    }

    input[type="file"] {
      width: 100%;
      padding: 14px;
      border: 1px dashed #9aa7b5;
      border-radius: 8px;
      background: #fbfcfd;
      color: var(--ink);
    }

    button {
      width: 100%;
      min-height: 48px;
      margin-top: 16px;
      border: 0;
      border-radius: 8px;
      background: var(--accent);
      color: #fff;
      font-size: 16px;
      font-weight: 700;
      cursor: pointer;
    }

    button:active {
      background: var(--accent-strong);
    }

    .note {
      margin-top: 12px;
      font-size: 14px;
    }

    .error {
      margin-top: 16px;
      padding: 12px;
      border: 1px solid #f1a29b;
      border-radius: 8px;
      background: #fff1ef;
      color: var(--danger);
      font-weight: 700;
    }

    .debug {
      margin-top: 14px;
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 12px;
    }

    .debug h3 {
      margin: 0 0 8px;
      font-size: 16px;
    }

    .debug pre {
      margin: 8px 0 0;
      max-height: 220px;
      overflow: auto;
      white-space: pre-wrap;
      word-break: break-word;
      font-size: 13px;
      line-height: 1.35;
      color: var(--ink);
      background: #f3f5f7;
      border-radius: 6px;
      padding: 10px;
    }

    .steps {
      margin-top: 18px;
      padding: 0;
      list-style: none;
      color: var(--muted);
      font-size: 14px;
    }

    .steps li {
      padding: 8px 0;
      border-top: 1px solid var(--line);
    }

    .results {
      margin-top: 18px;
    }

    .summary-grid {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 10px;
      margin-top: 12px;
    }

    .metric {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 12px;
    }

    .metric span {
      display: block;
      color: var(--muted);
      font-size: 13px;
    }

    .metric strong {
      display: block;
      margin-top: 4px;
      font-size: 18px;
      overflow-wrap: anywhere;
    }

    .table-wrap {
      margin-top: 14px;
      overflow-x: auto;
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
    }

    table {
      width: 100%;
      border-collapse: collapse;
      min-width: 560px;
    }

    th,
    td {
      padding: 10px;
      border-bottom: 1px solid var(--line);
      text-align: left;
      white-space: nowrap;
    }

    th {
      background: #eaf1f7;
      font-size: 13px;
    }

    tr:last-child td {
      border-bottom: 0;
    }

    .number {
      text-align: right;
      font-variant-numeric: tabular-nums;
    }

    .buy {
      color: var(--buy);
      font-weight: 700;
    }

    .sell {
      color: var(--sell);
      font-weight: 700;
    }

    .doc-title {
      margin: 22px 0 0;
      font-size: 18px;
    }

    @media (max-width: 560px) {
      .summary-grid {
        grid-template-columns: 1fr;
      }
    }
  </style>
</head>
<body>
  <main>
    <header>
      <h1>Trading Data Analyzer</h1>
      <p>Upload trading screenshots or images and view the extracted analysis.</p>
    </header>

    {% if error %}
      <div class="error">{{ error }}</div>
    {% endif %}

    {% if diagnostics %}
      {% for item in diagnostics %}
        <section class="debug">
          <h3>{{ item.name }}</h3>
          <p>{{ item.message }}</p>
          {% if item.text %}
            <pre>{{ item.text }}</pre>
          {% endif %}
        </section>
      {% endfor %}
    {% endif %}

    <form method="post" enctype="multipart/form-data">
      <label for="images">Trading images</label>
      <input id="images" name="images" type="file" accept=".jpg,.jpeg,.png,.tif,.tiff,image/*" multiple required>
      <button type="submit">Show Trading Data</button>
      <p class="note">Supported: JPG, PNG, JPEG, TIFF. You can select more than one image.</p>
    </form>

    {% if results %}
      <section class="results">
        <h2>Summary</h2>
        <div class="summary-grid">
          <div class="metric">
            <span>BUY Total</span>
            <strong class="buy">{{ "%.4f"|format(results.buy_total) }}</strong>
          </div>
          <div class="metric">
            <span>SELL Total</span>
            <strong class="sell">{{ "%.4f"|format(results.sell_total) }}</strong>
          </div>
          <div class="metric">
            <span>NET</span>
            <strong>{{ "%.4f"|format(results.net_total) }}</strong>
          </div>
        </div>

        {% for document in results.documents %}
          <h3 class="doc-title">{{ document.name }}</h3>
          <div class="summary-grid">
            <div class="metric">
              <span>BUY</span>
              <strong class="buy">{{ "%.4f"|format(document.buy_total) }}</strong>
            </div>
            <div class="metric">
              <span>SELL</span>
              <strong class="sell">{{ "%.4f"|format(document.sell_total) }}</strong>
            </div>
            <div class="metric">
              <span>Trades</span>
              <strong>{{ document.count }}</strong>
            </div>
          </div>

          <div class="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Sell/Buy</th>
                  <th class="number">Quantity</th>
                  <th class="number">Market Rate</th>
                  <th class="number">Calculated Value</th>
                </tr>
              </thead>
              <tbody>
                {% for trade in document.trades %}
                  <tr>
                    <td class="{{ trade.direction|lower }}">{{ trade.direction }}</td>
                    <td class="number">{{ trade.quantity }}</td>
                    <td class="number">{{ "%.4f"|format(trade.rate) }}</td>
                    <td class="number">{{ "%.4f"|format(trade.calculated) }}</td>
                  </tr>
                {% endfor %}
              </tbody>
            </table>
          </div>
        {% endfor %}
      </section>
    {% endif %}

    <ul class="steps">
      <li>Keep this app running on your computer.</li>
      <li>Open the local network URL on your phone while both devices use the same Wi-Fi.</li>
      <li>Choose images from your phone to view the extracted totals and rows here.</li>
    </ul>
  </main>
</body>
</html>
"""


def is_allowed_file(filename):
    return Path(filename).suffix.lower() in ALLOWED_EXTENSIONS


def build_results(extractor):
    grouped = extractor.calculate_values()
    documents = []

    for doc_name, trades in extractor.documents.items():
        buy_total = sum(trade["calculated"] for trade in trades if trade["direction"] == "BUY")
        sell_total = sum(trade["calculated"] for trade in trades if trade["direction"] == "SELL")
        documents.append(
            {
                "name": doc_name,
                "trades": trades,
                "buy_total": buy_total,
                "sell_total": sell_total,
                "count": len(trades),
            }
        )

    buy_total = sum(trade["calculated"] for trade in grouped["buy"])
    sell_total = sum(trade["calculated"] for trade in grouped["sell"])

    return {
        "buy_total": buy_total,
        "sell_total": sell_total,
        "net_total": buy_total - sell_total,
        "documents": documents,
    }


def process_uploaded_images(image_paths):
    extractor = TradingDataExtractor()
    diagnostics = []

    for image_path in image_paths:
        doc_name = Path(image_path).stem
        text = extractor.extract_text_from_image(image_path)

        if not text:
            diagnostics.append(
                {
                    "name": doc_name,
                    "message": "OCR could not read any text from this image.",
                    "text": "",
                }
            )
            continue

        trades = extractor.parse_trading_data(text)
        if not trades:
            diagnostics.append(
                {
                    "name": doc_name,
                    "message": "OCR read text, but no BUY/SELL rows matched the parser.",
                    "text": text.strip()[:3000],
                }
            )
            continue

        extractor.documents[doc_name] = trades
        extractor.trading_data.extend(trades)

    return extractor, diagnostics


@app.route("/health")
def health():
    return {"status": "ok"}


@app.route("/", methods=["GET", "POST"])
def index():
    try:
        if request.method == "GET":
            return render_template_string(PAGE)

        files = request.files.getlist("images")
        files = [file for file in files if file and file.filename]

        if not files:
            return render_template_string(PAGE, error="Please choose at least one image.")

        if len(files) > MAX_FILES_PER_REQUEST:
            return render_template_string(
                PAGE,
                error=f"Please upload {MAX_FILES_PER_REQUEST} images or fewer at a time.",
            )

        invalid_files = [file.filename for file in files if not is_allowed_file(file.filename)]
        if invalid_files:
            return render_template_string(
                PAGE,
                error=f"Unsupported file type: {', '.join(invalid_files)}",
            )

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            image_paths = []

            for index, uploaded_file in enumerate(files, start=1):
                original_name = secure_filename(uploaded_file.filename)
                if not original_name:
                    original_name = f"image_{index}.png"
                image_path = temp_path / f"{index}_{original_name}"
                uploaded_file.save(image_path)
                image_paths.append(image_path)

            output_capture = StringIO()

            with redirect_stdout(output_capture), redirect_stderr(output_capture):
                extractor, diagnostics = process_uploaded_images(image_paths)

            if not extractor.trading_data:
                return render_template_string(
                    PAGE,
                    error="No trading data could be extracted. Try a clearer image.",
                    diagnostics=diagnostics,
                )

            results = build_results(extractor)

        return render_template_string(PAGE, results=results, diagnostics=diagnostics)
    except Exception:
        error = traceback.format_exc()
        print(error, flush=True)
        return render_template_string(PAGE, error=error), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=False)
