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

import fitz
from flask import Flask, jsonify, render_template_string, request
import pytesseract
from werkzeug.utils import secure_filename

from trading_data_analyzer import TradingDataExtractor


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tiff", ".tif"}
PDF_EXTENSIONS = {".pdf"}
ALLOWED_EXTENSIONS = IMAGE_EXTENSIONS | PDF_EXTENSIONS
MAX_FILES_PER_REQUEST = 7
MAX_PDF_PAGES = int(os.environ.get("MAX_PDF_PAGES", "12"))
# Target DPI for PDF -> image rendering. ~200 dpi is enough for OCR and far cheaper than
# the previous hard-coded zoom=2 on already-large pages.
PDF_RENDER_DPI = int(os.environ.get("PDF_RENDER_DPI", "200"))

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

    input[type="file"],
    input[type="password"] {
      width: 100%;
      padding: 14px;
      border: 1px dashed #9aa7b5;
      border-radius: 8px;
      background: #fbfcfd;
      color: var(--ink);
    }

    input[type="password"] {
      border-style: solid;
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

    .progress {
      margin-top: 14px;
      color: var(--muted);
      font-weight: 700;
    }

    .hidden {
      display: none;
    }

    .step-log {
      margin-top: 12px;
      padding: 0;
      list-style: none;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fbfcfd;
      overflow: hidden;
    }

    .step-log li {
      display: grid;
      grid-template-columns: 28px 1fr auto;
      gap: 8px;
      padding: 8px 12px;
      border-top: 1px solid var(--line);
      font-size: 13px;
      align-items: start;
    }

    .step-log li:first-child {
      border-top: 0;
    }

    .step-log .step-icon {
      font-weight: 700;
      font-family: Consolas, "Courier New", monospace;
      line-height: 1.4;
    }

    .step-log .step-name {
      font-weight: 700;
      text-transform: uppercase;
      font-size: 11px;
      letter-spacing: 0.04em;
      color: var(--muted);
      margin-right: 6px;
    }

    .step-log .step-time {
      color: var(--muted);
      font-variant-numeric: tabular-nums;
      font-size: 12px;
    }

    .step-log .step-detail {
      grid-column: 2 / 4;
      margin: 4px 0 0;
      padding: 6px 8px;
      background: #f1f4f7;
      border-radius: 4px;
      white-space: pre-wrap;
      word-break: break-word;
      font-family: Consolas, "Courier New", monospace;
      font-size: 12px;
      color: var(--ink);
      max-height: 160px;
      overflow: auto;
    }

    .step-log .ok    .step-icon { color: var(--buy); }
    .step-log .warn  .step-icon { color: #b25f00; }
    .step-log .error .step-icon { color: var(--sell); }
    .step-log .info  .step-icon { color: var(--accent); }

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
          {% if item.steps %}
            <ul class="step-log">
              {% for step in item.steps %}
                <li class="{{ step.status }}">
                  <span class="step-icon">{% if step.status == 'ok' %}✓{% elif step.status == 'warn' %}!{% elif step.status == 'error' %}x{% else %}·{% endif %}</span>
                  <span><span class="step-name">{{ step.step }}</span>{{ step.message }}</span>
                  <span class="step-time">{{ step.elapsed_ms or 0 }} ms</span>
                  {% if step.detail %}
                    <pre class="step-detail">{{ step.detail }}</pre>
                  {% endif %}
                </li>
              {% endfor %}
            </ul>
          {% endif %}
          {% if item.text %}
            <pre>{{ item.text }}</pre>
          {% endif %}
        </section>
      {% endfor %}
    {% endif %}

    <form id="upload-form" method="post" enctype="multipart/form-data">
      <label for="images">Trading files</label>
      <input id="images" name="images" type="file" accept=".jpg,.jpeg,.png,.tif,.tiff,.pdf,image/*,application/pdf" multiple required>
      <label for="pdf-password" style="margin-top: 14px;">PDF password</label>
      <input id="pdf-password" name="pdf_password" type="password" autocomplete="off" placeholder="Only needed for locked PDFs">
      <button type="submit">Show Trading Data</button>
      <p class="note">Supported: PDF, JPG, PNG, JPEG, TIFF. You can select more than one file.</p>
      <p id="progress" class="progress hidden"></p>
    </form>

    <section id="client-results" class="results hidden">
      <h2>Summary</h2>
      <div class="summary-grid">
        <div class="metric">
          <span>BUY Total</span>
          <strong id="client-buy-total" class="buy">0.0000</strong>
        </div>
        <div class="metric">
          <span>SELL Total</span>
          <strong id="client-sell-total" class="sell">0.0000</strong>
        </div>
        <div class="metric">
          <span>NET</span>
          <strong id="client-net-total">0.0000</strong>
        </div>
      </div>
      <div id="client-documents"></div>
    </section>

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

          {% if document.steps %}
            <ul class="step-log">
              {% for step in document.steps %}
                <li class="{{ step.status }}">
                  <span class="step-icon">{% if step.status == 'ok' %}✓{% elif step.status == 'warn' %}!{% elif step.status == 'error' %}x{% else %}·{% endif %}</span>
                  <span><span class="step-name">{{ step.step }}</span>{{ step.message }}</span>
                  <span class="step-time">{{ step.elapsed_ms or 0 }} ms</span>
                  {% if step.detail %}
                    <pre class="step-detail">{{ step.detail }}</pre>
                  {% endif %}
                </li>
              {% endfor %}
            </ul>
          {% endif %}

          <div class="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Sell/Buy</th>
                  <th class="number">Quantity</th>
                  <th class="number">Market Rate</th>
                  <th class="number">Calculated Value</th>
                  <th>OCR Line</th>
                </tr>
              </thead>
              <tbody>
                {% for trade in document.trades %}
                  <tr>
                    <td class="{{ trade.direction|lower }}">{{ trade.direction }}</td>
                    <td class="number">{{ trade.quantity }}</td>
                    <td class="number">{{ "%.4f"|format(trade.rate) }}</td>
                    <td class="number">{{ "%.4f"|format(trade.calculated) }}</td>
                    <td>{{ trade.source_line or "" }}</td>
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
  <script>
    const maxFiles = {{ max_files }};
    const form = document.getElementById("upload-form");
    const fileInput = document.getElementById("images");
    const passwordInput = document.getElementById("pdf-password");
    const progress = document.getElementById("progress");
    const resultsSection = document.getElementById("client-results");
    const documentsEl = document.getElementById("client-documents");
    const buyTotalEl = document.getElementById("client-buy-total");
    const sellTotalEl = document.getElementById("client-sell-total");
    const netTotalEl = document.getElementById("client-net-total");

    function formatNumber(value) {
      return Number(value || 0).toFixed(4);
    }

    function escapeHtml(value) {
      return String(value || "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
    }

    function statusIcon(status) {
      switch (status) {
        case "ok": return "&#10003;";
        case "warn": return "!";
        case "error": return "x";
        default: return "&middot;";
      }
    }

    function renderStepList(steps) {
      if (!steps || !steps.length) return "";
      const items = steps.map((step) => `
        <li class="${escapeHtml(step.status || "info")}">
          <span class="step-icon">${statusIcon(step.status)}</span>
          <span><span class="step-name">${escapeHtml(step.step || "")}</span>${escapeHtml(step.message || "")}</span>
          <span class="step-time">${Number(step.elapsed_ms || 0)} ms</span>
          ${step.detail ? `<pre class="step-detail">${escapeHtml(step.detail)}</pre>` : ""}
        </li>
      `).join("");
      return `<ul class="step-log">${items}</ul>`;
    }

    function renderDocument(doc) {
      const rows = doc.trades.map((trade) => `
        <tr>
          <td class="${String(trade.direction).toLowerCase()}">${escapeHtml(trade.direction)}</td>
          <td class="number">${escapeHtml(trade.quantity)}</td>
          <td class="number">${formatNumber(trade.rate)}</td>
          <td class="number">${formatNumber(trade.calculated)}</td>
          <td>${escapeHtml(trade.source_line || "")}</td>
        </tr>
      `).join("");

      const wrapper = document.createElement("div");
      wrapper.innerHTML = `
        <h3 class="doc-title">${escapeHtml(doc.name)}</h3>
        <div class="summary-grid">
          <div class="metric">
            <span>BUY</span>
            <strong class="buy">${formatNumber(doc.buy_total)}</strong>
          </div>
          <div class="metric">
            <span>SELL</span>
            <strong class="sell">${formatNumber(doc.sell_total)}</strong>
          </div>
          <div class="metric">
            <span>Trades</span>
            <strong>${escapeHtml(doc.count)}</strong>
          </div>
        </div>
        ${renderStepList(doc.steps)}
        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Sell/Buy</th>
                <th class="number">Quantity</th>
                <th class="number">Market Rate</th>
                <th class="number">Calculated Value</th>
                <th>OCR Line</th>
              </tr>
            </thead>
            <tbody>${rows}</tbody>
          </table>
        </div>
      `;
      documentsEl.appendChild(wrapper);
    }

    function renderDiagnostic(fileName, diagnostics) {
      const wrapper = document.createElement("section");
      wrapper.className = "debug";
      const details = diagnostics.map((item) => `
        <p>${escapeHtml(item.message)}</p>
        ${renderStepList(item.steps)}
        ${item.text ? `<pre>${escapeHtml(item.text)}</pre>` : ""}
      `).join("");
      wrapper.innerHTML = `<h3>${escapeHtml(fileName)}</h3>${details || "<p>No rows found.</p>"}`;
      documentsEl.appendChild(wrapper);
    }

    form.addEventListener("submit", async (event) => {
      event.preventDefault();

      const files = Array.from(fileInput.files || []);
      if (!files.length) {
        return;
      }

      if (files.length > maxFiles) {
        progress.textContent = `Please upload ${maxFiles} images or fewer at a time.`;
        progress.classList.remove("hidden");
        return;
      }

      let buyTotal = 0;
      let sellTotal = 0;
      documentsEl.innerHTML = "";
      resultsSection.classList.remove("hidden");
      progress.classList.remove("hidden");
      form.querySelector("button").disabled = true;

      try {
        for (let index = 0; index < files.length; index += 1) {
          const file = files[index];
          progress.textContent = `Processing ${index + 1} of ${files.length}: ${file.name}`;

          const formData = new FormData();
          formData.append("image", file);
          formData.append("pdf_password", passwordInput.value || "");

          const response = await fetch("/api/process-image", {
            method: "POST",
            body: formData,
          });
          const payload = await response.json();

          if (!response.ok || payload.error) {
            renderDiagnostic(file.name, payload.diagnostics || [{ message: payload.error || "Processing failed.", text: "" }]);
            continue;
          }

          if (payload.results && payload.results.documents.length) {
            const document = payload.results.documents[0];
            buyTotal += Number(document.buy_total || 0);
            sellTotal += Number(document.sell_total || 0);
            renderDocument(document);
            buyTotalEl.textContent = formatNumber(buyTotal);
            sellTotalEl.textContent = formatNumber(sellTotal);
            netTotalEl.textContent = formatNumber(buyTotal - sellTotal);
          } else {
            renderDiagnostic(file.name, payload.diagnostics || []);
          }
        }
        progress.textContent = "Done";
      } catch (error) {
        progress.textContent = "Processing failed. Try fewer or smaller images.";
        renderDiagnostic("Request error", [{ message: String(error), text: "" }]);
      } finally {
        form.querySelector("button").disabled = false;
      }
    });
  </script>
</body>
</html>
"""


def is_allowed_file(filename):
    return Path(filename).suffix.lower() in ALLOWED_EXTENSIONS


def is_pdf_file(filename):
    return Path(filename).suffix.lower() in PDF_EXTENSIONS


def render_pdf_to_images(pdf_path, output_dir, password="", pdf_steps=None):
    image_paths = []
    document = fitz.open(pdf_path)

    try:
        if document.needs_pass:
            if not password:
                raise ValueError("This PDF is password protected. Enter the PDF password.")
            if not document.authenticate(password):
                raise ValueError("Incorrect PDF password.")

        if document.page_count > MAX_PDF_PAGES:
            raise ValueError(f"PDF has {document.page_count} pages. Upload {MAX_PDF_PAGES} pages or fewer at a time.")

        # PyMuPDF default is 72 dpi; compute zoom so the rendered raster is ~PDF_RENDER_DPI dpi.
        zoom = max(1.0, PDF_RENDER_DPI / 72.0)
        matrix = fitz.Matrix(zoom, zoom)
        if pdf_steps is not None:
            pdf_steps.append({
                "step": "pdf-render",
                "status": "info",
                "message": f"Rendering {document.page_count} page(s) at ~{PDF_RENDER_DPI} dpi (zoom={zoom:.2f})",
                "detail": "",
            })
        for page_index in range(document.page_count):
            page = document.load_page(page_index)
            pixmap = page.get_pixmap(matrix=matrix, alpha=False)
            image_path = output_dir / f"{pdf_path.stem}_page_{page_index + 1}.png"
            pixmap.save(image_path)
            image_paths.append(image_path)
            if pdf_steps is not None:
                pdf_steps.append({
                    "step": "pdf-render",
                    "status": "ok",
                    "message": f"Page {page_index + 1}/{document.page_count} -> {image_path.name} ({pixmap.width}x{pixmap.height})",
                    "detail": "",
                })
    finally:
        document.close()

    return image_paths


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
                "steps": extractor.steps_by_doc.get(doc_name, []),
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
        trades, steps = extractor.extract_with_steps(image_path, echo=True)
        extractor.steps_by_doc[doc_name] = steps

        if not trades:
            # Find the most informative step for the diagnostic message
            failure = next((s for s in reversed(steps) if s["status"] in ("error", "warn")), None)
            message = failure["message"] if failure else "No trading data could be extracted from this file."
            detail_text = failure.get("detail", "") if failure else ""
            diagnostics.append(
                {
                    "name": doc_name,
                    "message": message,
                    "text": detail_text,
                    "steps": steps,
                }
            )
            continue

        extractor.documents[doc_name] = trades
        extractor.trading_data.extend(trades)

    return extractor, diagnostics


@app.route("/health")
def health():
    try:
        tesseract_version = str(pytesseract.get_tesseract_version())
    except Exception as exc:
        tesseract_version = f"unavailable: {exc}"

    return {
        "status": "ok",
        "tesseract_version": tesseract_version,
    }


@app.route("/api/process-image", methods=["POST"])
def process_image_api():
    uploaded_file = request.files.get("image")
    pdf_password = request.form.get("pdf_password", "")

    if not uploaded_file or not uploaded_file.filename:
        return jsonify({"error": "Please choose a file.", "diagnostics": []}), 400

    if not is_allowed_file(uploaded_file.filename):
        return jsonify(
            {
                "error": "Unsupported file type.",
                "diagnostics": [
                    {
                        "name": uploaded_file.filename,
                        "message": "Supported formats are PDF, JPG, PNG, JPEG, and TIFF.",
                        "text": "",
                    }
                ],
            }
        ), 400

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            original_name = secure_filename(uploaded_file.filename) or "image.png"
            uploaded_path = temp_path / original_name
            uploaded_file.save(uploaded_path)

            pdf_steps = []
            if is_pdf_file(original_name):
                try:
                    image_paths = render_pdf_to_images(uploaded_path, temp_path, pdf_password, pdf_steps=pdf_steps)
                except ValueError as exc:
                    return jsonify(
                        {
                            "error": str(exc),
                            "diagnostics": [
                                {
                                    "name": original_name,
                                    "message": str(exc),
                                    "text": "",
                                    "steps": pdf_steps + [{
                                        "step": "pdf-render",
                                        "status": "error",
                                        "message": str(exc),
                                        "detail": "",
                                    }],
                                }
                            ],
                        }
                    ), 422
            else:
                image_paths = [uploaded_path]

            output_capture = StringIO()
            with redirect_stdout(output_capture), redirect_stderr(output_capture):
                extractor, diagnostics = process_uploaded_images(image_paths)

            # Prepend PDF rendering steps onto the first document's step log so the UI shows
            # the full pipeline for that file.
            if pdf_steps:
                for diag in diagnostics:
                    diag["steps"] = pdf_steps + diag.get("steps", [])
                for doc_name in list(extractor.steps_by_doc.keys()):
                    extractor.steps_by_doc[doc_name] = pdf_steps + extractor.steps_by_doc[doc_name]

            if not extractor.trading_data:
                captured_output = output_capture.getvalue().strip()
                if captured_output:
                    diagnostics.append(
                        {
                            "name": "OCR processing log",
                            "message": "Internal messages from image processing.",
                            "text": captured_output[-3000:],
                            "steps": [],
                        }
                    )
                return jsonify({"error": "No trading data could be extracted.", "diagnostics": diagnostics}), 422

            return jsonify({"results": build_results(extractor), "diagnostics": diagnostics})
    except Exception:
        error = traceback.format_exc()
        print(error, flush=True)
        return jsonify(
            {
                "error": "Image processing failed.",
                "diagnostics": [{"name": uploaded_file.filename, "message": error, "text": ""}],
            }
        ), 500


@app.route("/", methods=["GET", "POST"])
def index():
    try:
        if request.method == "GET":
            return render_template_string(PAGE, max_files=MAX_FILES_PER_REQUEST)

        files = request.files.getlist("images")
        files = [file for file in files if file and file.filename]

        if not files:
            return render_template_string(PAGE, error="Please choose at least one image.", max_files=MAX_FILES_PER_REQUEST)

        if len(files) > MAX_FILES_PER_REQUEST:
            return render_template_string(
                PAGE,
                error=f"Please upload {MAX_FILES_PER_REQUEST} images or fewer at a time.",
                max_files=MAX_FILES_PER_REQUEST,
            )

        invalid_files = [file.filename for file in files if not is_allowed_file(file.filename)]
        if invalid_files:
            return render_template_string(
                PAGE,
                error=f"Unsupported file type: {', '.join(invalid_files)}",
                max_files=MAX_FILES_PER_REQUEST,
            )

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            image_paths = []
            pdf_steps_by_file = {}

            pdf_password = request.form.get("pdf_password", "")

            for index, uploaded_file in enumerate(files, start=1):
                original_name = secure_filename(uploaded_file.filename)
                if not original_name:
                    original_name = f"image_{index}.png"
                uploaded_path = temp_path / f"{index}_{original_name}"
                uploaded_file.save(uploaded_path)

                if is_pdf_file(original_name):
                    pdf_steps = []
                    try:
                        rendered = render_pdf_to_images(uploaded_path, temp_path, pdf_password, pdf_steps=pdf_steps)
                        image_paths.extend(rendered)
                        for rendered_path in rendered:
                            pdf_steps_by_file[Path(rendered_path).stem] = pdf_steps
                    except ValueError as exc:
                        return render_template_string(
                            PAGE,
                            error=str(exc),
                            diagnostics=[
                                {
                                    "name": original_name,
                                    "message": str(exc),
                                    "text": "",
                                    "steps": pdf_steps + [{
                                        "step": "pdf-render",
                                        "status": "error",
                                        "message": str(exc),
                                        "detail": "",
                                    }],
                                }
                            ],
                            max_files=MAX_FILES_PER_REQUEST,
                        )
                else:
                    image_paths.append(uploaded_path)

            output_capture = StringIO()
            extractor = None
            diagnostics = []

            with redirect_stdout(output_capture), redirect_stderr(output_capture):
                extractor, diagnostics = process_uploaded_images(image_paths)

            # Prepend any PDF render steps onto matching documents
            if pdf_steps_by_file:
                for diag in diagnostics:
                    extra = pdf_steps_by_file.get(diag.get("name"))
                    if extra:
                        diag["steps"] = extra + diag.get("steps", [])
                for doc_name in list(extractor.steps_by_doc.keys()):
                    extra = pdf_steps_by_file.get(doc_name)
                    if extra:
                        extractor.steps_by_doc[doc_name] = extra + extractor.steps_by_doc[doc_name]

            if not extractor.trading_data:
                captured_output = output_capture.getvalue().strip()
                if captured_output:
                    diagnostics.append(
                        {
                            "name": "OCR processing log",
                            "message": "Internal messages from image processing.",
                            "text": captured_output[-3000:],
                            "steps": [],
                        }
                    )

                return render_template_string(
                    PAGE,
                    error="No trading data could be extracted. Try a clearer image.",
                    diagnostics=diagnostics,
                    max_files=MAX_FILES_PER_REQUEST,
                )

            results = build_results(extractor)

        return render_template_string(PAGE, results=results, diagnostics=diagnostics, max_files=MAX_FILES_PER_REQUEST)
    except Exception:
        error = traceback.format_exc()
        print(error, flush=True)
        return render_template_string(PAGE, error=error, max_files=MAX_FILES_PER_REQUEST), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=False)
