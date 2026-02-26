from flask import Flask, request, render_template_string
import fitz  # PyMuPDF

app = Flask(__name__)

HTML_TEMPLATE = """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <title>PDF Character Counter</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
      :root {
        font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        color-scheme: light dark;
      }

      * {
        box-sizing: border-box;
      }

      body {
        margin: 0;
        min-height: 100vh;
        display: flex;
        align-items: center;
        justify-content: center;
        background: radial-gradient(circle at top, #1f2937 0, #020617 55%, #000 100%);
        color: #e5e7eb;
      }

      .app-shell {
        width: 100%;
        max-width: 720px;
        padding: 24px;
      }

      .card {
        background: rgba(15, 23, 42, 0.92);
        border-radius: 18px;
        padding: 24px 24px 20px;
        box-shadow: 0 18px 40px rgba(0,0,0,0.45);
        border: 1px solid rgba(148, 163, 184, 0.25);
        backdrop-filter: blur(18px);
      }

      h1 {
        margin: 0 0 4px;
        font-size: 1.5rem;
        letter-spacing: 0.01em;
      }

      .subtitle {
        margin: 0 0 20px;
        font-size: 0.9rem;
        color: #9ca3af;
      }

      form {
        margin: 0;
      }

      .drop-zone {
        position: relative;
        border-radius: 14px;
        padding: 22px 18px;
        border: 1.5px dashed rgba(148, 163, 184, 0.75);
        background: radial-gradient(circle at top left, rgba(59,130,246,0.2), transparent 55%),
                    radial-gradient(circle at bottom right, rgba(236,72,153,0.18), transparent 55%),
                    rgba(15,23,42,0.8);
        display: flex;
        align-items: center;
        gap: 16px;
        cursor: pointer;
        transition: border-color 0.18s ease, background 0.18s ease, transform 0.1s ease;
      }

      .drop-zone.highlight {
        border-color: rgba(96, 165, 250, 1);
        box-shadow: 0 0 0 1px rgba(59, 130, 246, 0.9);
        transform: translateY(-1px);
      }

      .drop-icon {
        width: 42px;
        height: 42px;
        border-radius: 999px;
        display: flex;
        align-items: center;
        justify-content: center;
        background: radial-gradient(circle at 30% 0, #60a5fa, #2563eb);
        box-shadow: 0 10px 25px rgba(37, 99, 235, 0.55);
        flex-shrink: 0;
      }

      .drop-icon svg {
        width: 22px;
        height: 22px;
        fill: white;
      }

      .drop-text-main {
        font-size: 0.95rem;
        font-weight: 500;
      }

      .drop-text-sub {
        font-size: 0.8rem;
        color: #9ca3af;
        margin-top: 2px;
      }

      .file-pill {
        margin-top: 10px;
        display: inline-flex;
        align-items: center;
        gap: 8px;
        font-size: 0.8rem;
        padding: 6px 10px;
        border-radius: 999px;
        background: rgba(15, 23, 42, 0.9);
        border: 1px solid rgba(148, 163, 184, 0.5);
        color: #e5e7eb;
        max-width: 100%;
        white-space: nowrap;
        text-overflow: ellipsis;
        overflow: hidden;
      }

      .file-pill span {
        overflow: hidden;
        text-overflow: ellipsis;
      }

      .button-row {
        margin-top: 20px;
        display: flex;
        justify-content: flex-end;
      }

      button[type="submit"] {
        border: none;
        border-radius: 999px;
        padding: 9px 18px;
        font-size: 0.9rem;
        font-weight: 500;
        cursor: pointer;
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: linear-gradient(135deg, #4f46e5, #2563eb);
        color: white;
        box-shadow: 0 12px 25px rgba(37, 99, 235, 0.55);
        transition: transform 0.08s ease, box-shadow 0.08s ease, filter 0.12s ease;
      }

      button[type="submit"]:hover {
        transform: translateY(-1px);
        box-shadow: 0 18px 35px rgba(37, 99, 235, 0.7);
        filter: brightness(1.05);
      }

      button[type="submit"]:active {
        transform: translateY(0);
        box-shadow: 0 8px 20px rgba(37, 99, 235, 0.7);
      }

      button[type="submit"] svg {
        width: 14px;
        height: 14px;
        fill: currentColor;
      }

      .result {
        margin-top: 22px;
        padding-top: 14px;
        border-top: 1px solid rgba(31, 41, 55, 0.9);
        font-size: 0.92rem;
      }

      .result-label {
        color: #9ca3af;
        font-size: 0.78rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-bottom: 4px;
      }

      .result-value {
        font-size: 1.1rem;
        font-variant-numeric: tabular-nums;
      }

      .result-value.ok {
        color: #a5b4fc;
      }

      .result-value.error {
        color: #fca5a5;
      }

      .helper {
        margin-top: 10px;
        font-size: 0.78rem;
        color: #6b7280;
      }

      input[type="file"] {
        display: none;
      }

      @media (max-width: 600px) {
        .card {
          padding: 20px 18px 18px;
        }

        .drop-zone {
          padding: 18px 14px;
        }
      }
    </style>
  </head>
  <body>
    <div class="app-shell">
      <div class="card">
        <h1>PDF Character Counter</h1>
        <p class="subtitle">Counts characters without spaces and skips likely image titles/captions.</p>

        <form method="post" enctype="multipart/form-data" id="upload-form">
          <label for="file-input" class="drop-zone" id="drop-zone">
            <div class="drop-icon">
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <path d="M12 3a1 1 0 0 1 .78.37l3.75 4.5a1 1 0 1 1-1.56 1.26L13 7.34V16a1 1 0 1 1-2 0V7.34L9.03 9.13a1 1 0 0 1-1.56-1.26l3.75-4.5A1 1 0 0 1 12 3Zm-7 9a1 1 0 0 1 1 1v4.25C6 18.22 6.78 19 7.75 19h8.5c.97 0 1.75-.78 1.75-1.75V13a1 1 0 1 1 2 0v4.25A3.75 3.75 0 0 1 16.25 21h-8.5A3.75 3.75 0 0 1 4 17.25V13a1 1 0 0 1 1-1Z" />
              </svg>
            </div>
            <div>
              <div class="drop-text-main">Drag &amp; drop your PDF here</div>
              <div class="drop-text-sub">or click to choose a file from your computer</div>
              <div class="helper">Image titles are ignored using a heuristic based on layout around images.</div>
              <div id="file-pill" class="file-pill" style="display:none;">
                <svg viewBox="0 0 24 24" aria-hidden="true" style="width:14px;height:14px;opacity:0.85;">
                  <path fill="currentColor" d="M8 4a3 3 0 0 0-3 3v10a3 3 0 0 0 3 3h8a3 3 0 0 0 3-3V9.414A2 2 0 0 0 18.414 8L15 4.586A2 2 0 0 0 13.586 4H8Zm0 2h5.586L18 10.414V17a1 1 0 0 1-1 1H8a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1Z" />
                </svg>
                <span id="file-name"></span>
              </div>
            </div>
          </label>

          <input type="file" name="pdf" id="file-input" accept="application/pdf" required>

          <div class="button-row">
            <button type="submit">
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <path d="M4.21 4.22a1 1 0 0 1 1.02-.24l14 5a1 1 0 0 1 0 1.88l-14 5A1 1 0 0 1 4 16v-3.38a1 1 0 0 1 .76-.97L11 11l-6.24-.65A1 1 0 0 1 4 9.38V5a1 1 0 0 1 .21-.78Z" />
              </svg>
              Count characters
            </button>
          </div>
        </form>

        {% if result is not none %}
        <div class="result">
          <div class="result-label">Result</div>
          {% set is_error = result is string and result.startswith('Error') %}
          <div class="result-value {{ 'error' if is_error else 'ok' }}">
            {% if is_error %}
              {{ result }}
            {% else %}
              Characters (no spaces, no image titles): {{ result }}
            {% endif %}
          </div>
        </div>
        {% endif %}
      </div>
    </div>

    <script>
      (function() {
        const dropZone = document.getElementById('drop-zone');
        const fileInput = document.getElementById('file-input');
        const filePill = document.getElementById('file-pill');
        const fileNameEl = document.getElementById('file-name');

        function showFileName(file) {
          if (!file) return;
          fileNameEl.textContent = file.name;
          filePill.style.display = 'inline-flex';
        }

        fileInput.addEventListener('change', function(e) {
          const file = e.target.files[0];
          if (file) {
            showFileName(file);
          }
        });

        ['dragenter', 'dragover'].forEach(eventName => {
          dropZone.addEventListener(eventName, function(e) {
            e.preventDefault();
            e.stopPropagation();
            dropZone.classList.add('highlight');
          });
        });

        ['dragleave', 'drop'].forEach(eventName => {
          dropZone.addEventListener(eventName, function(e) {
            e.preventDefault();
            e.stopPropagation();
            dropZone.classList.remove('highlight');
          });
        });

        dropZone.addEventListener('drop', function(e) {
          const dt = e.dataTransfer;
          const files = dt.files;
          if (files && files.length > 0) {
            const file = files[0];
            if (file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf')) {
              // Assign dropped file to the hidden file input so the form submission works
              const dataTransfer = new DataTransfer();
              dataTransfer.items.add(file);
              fileInput.files = dataTransfer.files;
              showFileName(file);
            } else {
              alert('Please drop a PDF file.');
            }
          }
        });
      })();
    </script>
  </body>
</html>
"""

def bboxes_overlap(b1, b2, min_overlap_ratio=0.1):
    """
    Check if two bounding boxes overlap by at least a certain ratio.
    b = (x0, y0, x1, y1)
    """
    x0 = max(b1[0], b2[0])
    y0 = max(b1[1], b2[1])
    x1 = min(b1[2], b2[2])
    y1 = min(b1[3], b2[3])

    if x1 <= x0 or y1 <= y0:
        return False

    inter_area = (x1 - x0) * (y1 - y0)
    area1 = (b1[2] - b1[0]) * (b1[3] - b1[1])
    area2 = (b2[2] - b2[0]) * (b2[3] - b2[1])

    # overlap relative to smaller box
    overlap_ratio = inter_area / max(1e-9, min(area1, area2))
    return overlap_ratio >= min_overlap_ratio


def count_pdf_chars_excluding_image_titles(pdf_stream):
    """
    Count characters in a PDF, excluding spaces and (heuristically) text blocks
    that look like image titles/captions.
    """
    doc = fitz.open(stream=pdf_stream, filetype="pdf")
    total_chars = 0

    for page in doc:
        data = page.get_text("dict")

        image_blocks = [b for b in data["blocks"] if b["type"] == 1]
        text_blocks = [b for b in data["blocks"] if b["type"] == 0]

        # Build approximate caption regions: just below each image.
        caption_regions = []
        CAPTION_HEIGHT = 30  # adjust if needed

        for ib in image_blocks:
            x0, y0, x1, y1 = ib["bbox"]
            # region just under the image
            caption_regions.append((x0, y1, x1, y1 + CAPTION_HEIGHT))

        for tb in text_blocks:
            tbbox = tb["bbox"]

            # Skip this text block if it overlaps any caption region
            if any(bboxes_overlap(tbbox, cr) for cr in caption_regions):
                continue

            # Concatenate all text spans in the block
            block_text = ""
            for line in tb.get("lines", []):
                for span in line.get("spans", []):
                    block_text += span.get("text", "")

            # Remove spaces and newlines
            cleaned = block_text.replace(" ", "").replace("\n", "")
            total_chars += len(cleaned)

    doc.close()
    return total_chars


@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    if request.method == "POST":
        if "pdf" not in request.files:
            result = "No file uploaded"
        else:
            file = request.files["pdf"]
            if file.filename == "":
                result = "No selected file"
            else:
                pdf_bytes = file.read()
                try:
                    result = count_pdf_chars_excluding_image_titles(pdf_bytes)
                except Exception as e:
                    result = f"Error processing PDF: {e}"

    return render_template_string(HTML_TEMPLATE, result=result)


if __name__ == "__main__":
    app.run(debug=True)