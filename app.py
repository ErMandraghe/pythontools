from flask import Flask, render_template, request, jsonify, make_response
import pypdf
import re
import io
import unicodedata
import logging
import traceback

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB


def clean_text(text):
    if not text:
        return ""

    bullet_chars = [
        '●','○','◉','◎','◯','⬤','•','·',
        '■','□','▪','▫','▸','▹','►','▻',
        '✓','✔','✗','✘','→','⟶','➔','➜',
        '◆','◇','▲','△','▼','▽','‣','⁃',
    ]
    for ch in bullet_chars:
        text = text.replace(ch, '')

    emoji_pattern = re.compile(
        "[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF"
        "\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF"
        "\U00002702-\U000027B0\U000024C2-\U0001F251"
        "\U0001F900-\U0001F9FF\U00002600-\U000026FF]+",
        flags=re.UNICODE
    )
    text = emoji_pattern.sub('', text)

    out = []
    for ch in text:
        cat = unicodedata.category(ch)
        if cat.startswith(('L', 'N', 'P', 'Z')) or ch in ('\n', '\t', ' '):
            out.append(ch)
        elif ch in ('.', ',', ':', ';', '?', '!', '(', ')', '[', ']',
                    '-', '+', '=', '/', '%', "'", '"', '@', '#', '&', '*'):
            out.append(ch)
    text = ''.join(out)

    text = re.sub(r'\n{3,}', '\n\n', text)
    lines = text.split('\n')
    filtered = []
    for line in lines:
        stripped = line.strip()
        if re.search(r'[a-zA-Z0-9\u00C0-\u024F]', stripped):
            filtered.append(line)
        elif stripped == '':
            filtered.append('')
    text = '\n'.join(filtered)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def extract_pdf_text(pdf_bytes):
    result = []
    try:
        reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
        total = len(reader.pages)
        logger.info(f"PDF has {total} pages")

        for i, page in enumerate(reader.pages):
            try:
                raw = page.extract_text()
                if raw:
                    cleaned = clean_text(raw)
                    if cleaned:
                        result.append(f"--- Page {i+1} of {total} ---\n{cleaned}")
            except Exception as e:
                logger.warning(f"Page {i+1} skipped: {e}")

    except pypdf.errors.PdfReadError as e:
        raise ValueError(f"Could not read PDF: {str(e)}")
    except Exception as e:
        logger.error(f"Failed to open PDF: {traceback.format_exc()}")
        raise ValueError(f"Could not process PDF: {str(e)}")

    return '\n\n'.join(result)


# ── Routes ─────────────────────────────────────────────────

@app.route('/health')
def health():
    return jsonify({'status': 'ok'}), 200

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/extractor')
def extractor():
    return render_template('extractor.html')

@app.route('/whatisit')
def whatisit():
    return render_template('whatisit.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')


@app.route('/extract', methods=['POST'])
def extract():
    logger.info("POST /extract received")

    if 'pdf_file' not in request.files:
        return jsonify({'error': 'No file received. Please select a PDF and try again.'}), 400

    f = request.files['pdf_file']

    if not f or not f.filename or f.filename.strip() == '':
        return jsonify({'error': 'No file selected.'}), 400

    if not f.filename.lower().endswith('.pdf'):
        return jsonify({'error': 'Only PDF files are supported (.pdf).'}), 400

    try:
        pdf_bytes = f.read()
        logger.info(f"File received: {f.filename} — {len(pdf_bytes):,} bytes")

        if len(pdf_bytes) == 0:
            return jsonify({'error': 'The uploaded file is empty.'}), 400

        text = extract_pdf_text(pdf_bytes)

        if not text.strip():
            return jsonify({
                'error': 'No text found. This PDF is likely scanned or image-based. '
                         'Text extraction only works on digital PDFs.'
            }), 400

        output = io.BytesIO()
        output.write(text.encode('utf-8'))
        output.seek(0)

        safe_name = re.sub(r'[^\w\-.]', '_', f.filename.rsplit('.', 1)[0])
        download_name = safe_name + '_extracted.txt'
        logger.info(f"Sending: {download_name}")

        response = make_response(output.read())
        response.headers['Content-Type'] = 'text/plain; charset=utf-8'
        response.headers['Content-Disposition'] = f'attachment; filename="{download_name}"'
        response.headers['X-Filename'] = download_name
        return response

    except ValueError as e:
        return jsonify({'error': str(e)}), 400

    except Exception as e:
        logger.error(f"Unexpected error: {traceback.format_exc()}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500


@app.errorhandler(413)
def too_large(e):
    return jsonify({'error': 'File too large — maximum is 100 MB.'}), 413


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)
