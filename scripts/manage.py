#!/usr/bin/env python3
"""
Paper management web GUI for flomue.com.

Usage:
    pip install flask pymupdf pillow python-dotenv
    python scripts/manage.py

Opens http://localhost:5000
"""

import json
import os
import re
import shutil
import subprocess
import sys
import threading
import webbrowser

from flask import Flask, Response, jsonify, request, send_from_directory

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.env'), override=True)
except ImportError:
    pass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from parse_bib import parse_bibtex
from generate_tldrs import (
    abstract_hash, generate_tldr, load_cache, patch_md_frontmatter, save_cache,
)

SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
BIB_PATH    = os.path.join(SCRIPT_DIR,  "bib.bib")
PDF_DIR     = os.path.join(PROJECT_DIR, "static", "pdf")
PREVIEW_DIR = os.path.join(PROJECT_DIR, "assets", "publication_preview")
PUBS_JSON   = os.path.join(PROJECT_DIR, "data", "publications.json")
CACHE_PATH  = os.path.join(PROJECT_DIR, "data", "tldrs_cache.json")
CONTENT_DIR = os.path.join(PROJECT_DIR, "content", "publication")

app = Flask(__name__)


# ── helpers ───────────────────────────────────────────────────────────────────

def parse_file_field(raw):
    """Extract the first accessible PDF path from a BibTeX file field."""
    if not raw:
        return None
    # Unescape BibTeX path encoding: \\ → \ and \: → :
    field = raw.replace("\\\\", "\\").replace("\\:", ":")
    for part in field.split(";"):
        part = part.strip()
        # Zotero ":path:TYPE" format
        if part.startswith(":"):
            sub = part[1:].rsplit(":", 1)
            if len(sub) == 2 and sub[1].upper() == "PDF" and os.path.isfile(sub[0]):
                return sub[0]
        if part.lower().endswith(".pdf") and os.path.isfile(part):
            return part
    return None


def load_papers():
    """Return list of paper dicts with status info."""
    entries = parse_bibtex(BIB_PATH)
    cache   = load_cache(CACHE_PATH)
    pubs    = {}
    if os.path.isfile(PUBS_JSON):
        for p in json.load(open(PUBS_JSON, encoding="utf-8")):
            pubs[p["key"]] = p

    out = []
    for e in entries:
        key      = e.get("key", "")
        abstract = e.get("abstract", "").strip()
        h        = abstract_hash(abstract) if abstract else None
        tldr     = cache.get(h, {}) if h else {}
        pub      = pubs.get(key, {})

        has_preview = any(
            os.path.isfile(os.path.join(PREVIEW_DIR, f"{key}{x}"))
            for x in (".jpg", ".jpeg", ".png", ".gif", ".webp")
        )
        out.append({
            "key":         key,
            "title":       e.get("title", key),
            "year":        e.get("year", ""),
            "venue_short": pub.get("venue_short", ""),
            "abstract":    abstract,
            "file_raw":    e.get("file", ""),
            "has_pdf":     os.path.isfile(os.path.join(PDF_DIR, f"{key}.pdf")),
            "source_pdf":  parse_file_field(e.get("file", "")),
            "has_preview": has_preview,
            "has_tldr":    bool(tldr.get("did")),
            "tldr":        tldr,
        })
    return out


# ── routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def dashboard():
    return Response(DASHBOARD_HTML, mimetype="text/html")


@app.route("/paper/<key>")
def paper_page(key):
    return Response(PAPER_HTML.replace("__KEY__", key), mimetype="text/html")


@app.route("/api/papers")
def api_papers():
    return jsonify(load_papers())


@app.route("/api/<key>/info")
def api_info(key):
    for p in load_papers():
        if p["key"] == key:
            return jsonify(p)
    return jsonify({"error": "not found"}), 404


@app.route("/api/<key>/copy-pdf", methods=["POST"])
def api_copy_pdf(key):
    entries = parse_bibtex(BIB_PATH)
    e = next((x for x in entries if x["key"] == key), None)
    if not e:
        return jsonify({"error": "Key not found in bib"}), 404
    src = parse_file_field(e.get("file", ""))
    if not src:
        return jsonify({"error": "No accessible PDF found in the file field"}), 400
    os.makedirs(PDF_DIR, exist_ok=True)
    shutil.copy2(src, os.path.join(PDF_DIR, f"{key}.pdf"))
    return jsonify({"ok": True})


@app.route("/api/<key>/render")
def api_render(key):
    try:
        import fitz
    except ImportError:
        return "pymupdf not installed — run: pip install pymupdf", 500

    pdf = os.path.join(PDF_DIR, f"{key}.pdf")
    if not os.path.isfile(pdf):
        return "PDF not copied yet", 404

    page_num = int(request.args.get("page", 0))
    doc      = fitz.open(pdf)
    total    = len(doc)
    page_num = max(0, min(page_num, total - 1))
    pix      = doc[page_num].get_pixmap(matrix=fitz.Matrix(200 / 72, 200 / 72))

    resp = Response(pix.tobytes("png"), mimetype="image/png")
    resp.headers.update({
        "X-Page-Count":  str(total),
        "X-Page-Width":  str(pix.width),
        "X-Page-Height": str(pix.height),
        "Cache-Control": "no-store",
        "Access-Control-Expose-Headers": "X-Page-Count,X-Page-Width,X-Page-Height",
    })
    return resp


@app.route("/api/check-openai")
def api_check_openai():
    return jsonify({"available": bool(os.environ.get("OPENAI_API_KEY"))})


@app.route("/api/<key>/preview-image")
def api_preview_image(key):
    for ext in (".jpg", ".jpeg", ".png", ".gif", ".webp"):
        if os.path.isfile(os.path.join(PREVIEW_DIR, f"{key}{ext}")):
            return send_from_directory(PREVIEW_DIR, f"{key}{ext}")
    return "No preview", 404


@app.route("/api/<key>/save-preview", methods=["POST"])
def api_save_preview(key):
    try:
        import fitz
        from PIL import Image
    except ImportError:
        return jsonify({"error": "pip install pymupdf pillow"}), 500

    d = request.json
    page_num = int(d.get("page", 0))
    x, y, w, h = int(d["x"]), int(d["y"]), int(d["w"]), int(d["h"])
    if w <= 0 or h <= 0:
        return jsonify({"error": "Invalid crop dimensions"}), 400

    pdf = os.path.join(PDF_DIR, f"{key}.pdf")
    if not os.path.isfile(pdf):
        return jsonify({"error": "PDF not found"}), 404

    doc = fitz.open(pdf)
    pix = doc[page_num].get_pixmap(matrix=fitz.Matrix(200 / 72, 200 / 72))
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    os.makedirs(PREVIEW_DIR, exist_ok=True)
    img.crop((x, y, x + w, y + h)).save(
        os.path.join(PREVIEW_DIR, f"{key}.jpg"), "JPEG", quality=92
    )
    return jsonify({"ok": True})


@app.route("/api/<key>/generate-tldr", methods=["POST"])
def api_generate_tldr(key):
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        return jsonify({"error": "OPENAI_API_KEY not set in environment"}), 400
    try:
        from openai import OpenAI
    except ImportError:
        return jsonify({"error": "pip install openai"}), 500

    entries = parse_bibtex(BIB_PATH)
    e = next((x for x in entries if x["key"] == key), None)
    if not e:
        return jsonify({"error": "Key not found"}), 404

    abstract = e.get("abstract", "").strip()
    if not abstract:
        return jsonify({"error": "No abstract in bib entry"}), 400

    content = f"Abstract:\n{abstract}"
    pdf = os.path.join(PDF_DIR, f"{key}.pdf")
    if os.path.isfile(pdf):
        try:
            import pypdf
            text = re.sub(
                r"[\ud800-\udfff]", "",
                "\n".join(p.extract_text() or "" for p in pypdf.PdfReader(pdf).pages).strip(),
            )
            if text:
                content = f"Title: {e.get('title', '')}\n\nFull paper text:\n{text[:100000]}"
        except Exception:
            pass

    tldr  = generate_tldr(OpenAI(api_key=api_key), content)
    h     = abstract_hash(abstract)
    cache = load_cache(CACHE_PATH)
    cache[h] = tldr
    save_cache(CACHE_PATH, cache)
    return jsonify(tldr)


@app.route("/api/<key>/save-tldr", methods=["POST"])
def api_save_tldr(key):
    d    = request.json
    tldr = {k: d.get(k, "").strip() for k in ("did", "found", "takeaway")}

    entries = parse_bibtex(BIB_PATH)
    e = next((x for x in entries if x["key"] == key), None)
    if not e:
        return jsonify({"error": "Key not found"}), 404

    abstract = e.get("abstract", "").strip()
    if not abstract:
        return jsonify({"error": "No abstract to key cache on"}), 400

    h     = abstract_hash(abstract)
    cache = load_cache(CACHE_PATH)
    cache[h] = tldr
    save_cache(CACHE_PATH, cache)

    md = os.path.join(CONTENT_DIR, f"{key}.md")
    if os.path.isfile(md):
        patch_md_frontmatter(md, tldr)
    return jsonify({"ok": True})


@app.route("/api/run-pipeline", methods=["POST"])
def api_run_pipeline():
    def stream():
        proc = subprocess.Popen(
            [sys.executable, os.path.join(SCRIPT_DIR, "generate_tldrs.py")],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, encoding="utf-8", errors="replace",
            cwd=PROJECT_DIR,
        )
        for line in proc.stdout:
            yield f"data: {json.dumps(line.rstrip())}\n\n"
        proc.wait()
        yield f"data: {json.dumps('__DONE__')}\n\n"

    return Response(stream(), mimetype="text/event-stream")


# ── HTML templates ────────────────────────────────────────────────────────────

DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Paper Manager</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:system-ui,-apple-system,sans-serif;background:#f5f5f7;color:#1d1d1f;min-height:100vh}
.container{max-width:1100px;margin:0 auto;padding:28px 20px}
h1{font-size:1.6rem;font-weight:700;letter-spacing:-.02em}
.subtitle{color:#888;font-size:.875rem;margin-top:4px;margin-bottom:28px}
.toolbar{display:flex;align-items:center;gap:12px;flex-wrap:wrap;margin-bottom:16px}
button{cursor:pointer;border:none;border-radius:7px;padding:8px 18px;font-size:.875rem;font-weight:600;transition:.15s}
button:hover{filter:brightness(.9)}
button:disabled{opacity:.5;cursor:default}
.btn-primary{background:#4f46e5;color:#fff}
label.check{font-size:.875rem;display:flex;align-items:center;gap:6px;cursor:pointer;color:#555}
.card{background:#fff;border-radius:12px;box-shadow:0 1px 4px rgba(0,0,0,.08);overflow:hidden}
table{width:100%;border-collapse:collapse}
th,td{padding:10px 16px;text-align:left;font-size:.875rem}
th{background:#fafafa;font-weight:600;color:#666;border-bottom:1px solid #e8e8ed}
tr:not(:last-child) td{border-bottom:1px solid #f0f0f5}
tr:hover td{background:#fafafe}
.title-cell a{color:#4f46e5;text-decoration:none;font-weight:500}
.title-cell a:hover{text-decoration:underline}
.key-label{color:#aaa;font-size:.72rem;font-family:monospace;display:block;margin-top:2px}
.ctr{text-align:center}
.badge{display:inline-flex;align-items:center;justify-content:center;width:22px;height:22px;border-radius:50%;font-size:.72rem;font-weight:700}
.ok{background:#d1fae5;color:#065f46}
.miss{background:#fee2e2;color:#991b1b}
#log-wrap{margin-top:18px;display:none}
#log{background:#111;color:#8efa8e;font-family:monospace;font-size:.76rem;padding:14px 16px;border-radius:8px;height:180px;overflow-y:auto;white-space:pre-wrap}
.spin{display:inline-block;width:13px;height:13px;border:2px solid rgba(255,255,255,.4);border-top-color:#fff;border-radius:50%;animation:sp .65s linear infinite;vertical-align:middle;margin-right:5px}
@keyframes sp{to{transform:rotate(360deg)}}
.empty{text-align:center;padding:40px;color:#aaa;font-size:.875rem}
.stat{color:#888;font-size:.8rem}
</style>
</head>
<body>
<div class="container">
  <h1>&#x1F4C4; Paper Manager</h1>
  <p class="subtitle">Manage publications for flomue.com &mdash; <span id="stat" class="stat"></span></p>

  <div class="toolbar">
    <button class="btn-primary" id="btn-pipe" onclick="runPipeline()">&#x25B6; Run Full Pipeline</button>
    <label class="check"><input type="checkbox" id="chk-incomplete" onchange="render()"> Show only incomplete</label>
  </div>

  <div id="log-wrap"><div id="log"></div></div>

  <div class="card" style="margin-top:16px">
    <table>
      <thead><tr>
        <th style="width:45%">Title</th>
        <th>Year</th>
        <th>Venue</th>
        <th class="ctr">PDF</th>
        <th class="ctr">Preview</th>
        <th class="ctr">TL;DR</th>
      </tr></thead>
      <tbody id="tbody"><tr><td colspan="6" class="empty">Loading&hellip;</td></tr></tbody>
    </table>
  </div>
</div>

<script>
let all = [];

function esc(s){ return (s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;') }
function badge(ok){ return `<span class="badge ${ok?'ok':'miss'}">${ok?'&#x2713;':'&#x2717;'}</span>` }

async function load(){
  const r = await fetch('/api/papers');
  all = await r.json();
  render();
}

function render(){
  const onlyBad = document.getElementById('chk-incomplete').checked;
  const rows = onlyBad ? all.filter(p=>!p.has_pdf||!p.has_preview||!p.has_tldr) : all;
  const incomplete = all.filter(p=>!p.has_pdf||!p.has_preview||!p.has_tldr).length;
  document.getElementById('stat').textContent =
    `${all.length} papers \u2022 ${incomplete} incomplete`;
  document.getElementById('tbody').innerHTML = rows.length ? rows.map(p=>`
    <tr>
      <td class="title-cell">
        <a href="/paper/${p.key}">${esc(p.title)}</a>
        <span class="key-label">${esc(p.key)}</span>
      </td>
      <td>${p.year||''}</td>
      <td>${p.venue_short||''}</td>
      <td class="ctr">${badge(p.has_pdf)}</td>
      <td class="ctr">${badge(p.has_preview)}</td>
      <td class="ctr">${badge(p.has_tldr)}</td>
    </tr>`).join('') :
    '<tr><td colspan="6" class="empty">No papers match the filter.</td></tr>';
}

async function runPipeline(){
  const btn = document.getElementById('btn-pipe');
  const logWrap = document.getElementById('log-wrap');
  const log = document.getElementById('log');
  btn.disabled = true;
  btn.innerHTML = '<span class="spin"></span>Running&hellip;';
  logWrap.style.display = 'block';
  log.textContent = '';

  const resp = await fetch('/api/run-pipeline', {method:'POST'});
  const reader = resp.body.getReader();
  const dec = new TextDecoder();
  let buf = '';
  while(true){
    const {done,value} = await reader.read();
    if(done) break;
    buf += dec.decode(value,{stream:true});
    const lines = buf.split('\\n');
    buf = lines.pop();
    for(const line of lines){
      if(!line.startsWith('data: ')) continue;
      const msg = JSON.parse(line.slice(6));
      if(msg==='__DONE__'){ log.textContent += '\\n\\u2713 Done.\\n'; await load(); }
      else { log.textContent += msg+'\\n'; log.scrollTop=log.scrollHeight; }
    }
  }
  btn.disabled = false;
  btn.innerHTML = '&#x25B6; Run Full Pipeline';
}

load();
</script>
</body>
</html>"""


PAPER_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>__KEY__</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:system-ui,-apple-system,sans-serif;background:#f5f5f7;color:#1d1d1f}
.container{max-width:900px;margin:0 auto;padding:24px 20px}
.back{display:inline-flex;align-items:center;gap:5px;color:#4f46e5;font-size:.875rem;text-decoration:none;margin-bottom:20px}
.back:hover{text-decoration:underline}
h1{font-size:1.4rem;font-weight:700;letter-spacing:-.02em;line-height:1.3;margin-bottom:6px}
.meta{color:#888;font-size:.8rem;margin-bottom:24px}
.section{background:#fff;border-radius:12px;box-shadow:0 1px 4px rgba(0,0,0,.08);margin-bottom:16px;overflow:hidden}
.sec-head{display:flex;align-items:center;justify-content:space-between;padding:14px 18px;cursor:pointer;user-select:none}
.sec-head:hover{background:#fafafe}
.sec-title{font-weight:600;font-size:.95rem;display:flex;align-items:center;gap:8px}
.sec-body{padding:16px 18px;border-top:1px solid #f0f0f5;display:none}
.sec-body.open{display:block}
.badge{display:inline-flex;align-items:center;justify-content:center;width:22px;height:22px;border-radius:50%;font-size:.72rem;font-weight:700}
.ok{background:#d1fae5;color:#065f46}
.miss{background:#fee2e2;color:#991b1b}
.chevron{color:#aaa;font-size:.8rem;transition:.2s}
.chevron.open{transform:rotate(180deg)}
button{cursor:pointer;border:none;border-radius:7px;padding:7px 16px;font-size:.8rem;font-weight:600;transition:.15s}
button:hover{filter:brightness(.9)}
button:disabled{opacity:.45;cursor:default}
.btn-primary{background:#4f46e5;color:#fff}
.btn-outline{background:#fff;color:#4f46e5;border:1.5px solid #4f46e5}
.btn-danger{background:#fee2e2;color:#991b1b}
.row{display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin-bottom:10px}
.path{font-family:monospace;font-size:.75rem;background:#f5f5f7;padding:4px 8px;border-radius:5px;color:#555;word-break:break-all;flex:1}
.status-msg{font-size:.8rem;color:#555}
.ok-msg{color:#065f46}
.err-msg{color:#991b1b}
label.field-label{display:block;font-size:.75rem;font-weight:600;color:#888;text-transform:uppercase;letter-spacing:.05em;margin-bottom:4px;margin-top:12px}
label.field-label:first-child{margin-top:0}
textarea{width:100%;border:1.5px solid #e0e0e8;border-radius:7px;padding:8px 10px;font-size:.875rem;font-family:inherit;resize:vertical;line-height:1.5}
textarea:focus{outline:none;border-color:#4f46e5}
.tldr-actions{display:flex;gap:8px;margin-top:12px;align-items:center;flex-wrap:wrap}
.warn{background:#fffbeb;color:#92400e;border:1px solid #fde68a;border-radius:7px;padding:8px 12px;font-size:.8rem;margin-bottom:12px;display:none}
/* crop tool */
#crop-wrap{position:relative;display:inline-block;cursor:crosshair;margin-top:12px;user-select:none}
#pdf-img{display:block;max-width:100%;height:auto;border-radius:6px}
#crop-canvas{position:absolute;top:0;left:0;width:100%;height:100%;border-radius:6px}
.page-nav{display:flex;align-items:center;gap:8px;margin-bottom:10px}
.page-nav button{padding:5px 12px}
#page-info{font-size:.82rem;color:#666}
#crop-hint{font-size:.78rem;color:#888;margin-top:6px}
.preview-img{max-width:220px;border-radius:8px;margin-top:10px;border:1px solid #e0e0e8}
.spin{display:inline-block;width:13px;height:13px;border:2px solid rgba(79,70,229,.3);border-top-color:#4f46e5;border-radius:50%;animation:sp .65s linear infinite;vertical-align:middle;margin-right:4px}
@keyframes sp{to{transform:rotate(360deg)}}
</style>
</head>
<body>
<div class="container">
  <a class="back" href="/">&#x2190; Dashboard</a>
  <div id="header"><h1>Loading&hellip;</h1></div>

  <!-- PDF -->
  <div class="section">
    <div class="sec-head" onclick="toggle('pdf')">
      <div class="sec-title"><span id="pdf-badge"></span>1 &mdash; PDF</div>
      <span class="chevron" id="pdf-chev">&#x25BC;</span>
    </div>
    <div class="sec-body open" id="pdf-body">
      <div class="row">
        <span class="path" id="pdf-src">&#x2014;</span>
        <button class="btn-primary" id="btn-copy" onclick="copyPdf()" disabled>Copy to site</button>
      </div>
      <div id="pdf-msg" class="status-msg"></div>
    </div>
  </div>

  <!-- Preview -->
  <div class="section">
    <div class="sec-head" onclick="toggle('prev')">
      <div class="sec-title"><span id="prev-badge"></span>2 &mdash; Preview Image</div>
      <span class="chevron" id="prev-chev">&#x25BC;</span>
    </div>
    <div class="sec-body open" id="prev-body">
      <div id="prev-current"></div>
      <div class="page-nav" id="page-nav" style="display:none">
        <button class="btn-outline" onclick="changePage(-1)">&#x25C4;</button>
        <span id="page-info">Page 1</span>
        <button class="btn-outline" onclick="changePage(1)">&#x25BA;</button>
        <button class="btn-outline" onclick="renderPage()">&#x21BA; Re-render</button>
      </div>
      <div id="crop-wrap" style="display:none">
        <img id="pdf-img">
        <canvas id="crop-canvas"></canvas>
      </div>
      <div id="crop-hint" class="ok-msg" style="display:none">Click and drag on the page to select a crop area</div>
      <div id="crop-actions" style="display:none; margin-top:10px">
        <div class="row">
          <button class="btn-primary" onclick="saveCrop()">&#x1F4BE; Save as preview</button>
          <span id="crop-msg" class="status-msg"></span>
        </div>
      </div>
      <div id="prev-msg" class="status-msg" style="margin-top:8px"></div>
    </div>
  </div>

  <!-- TL;DR -->
  <div class="section">
    <div class="sec-head" onclick="toggle('tldr')">
      <div class="sec-title"><span id="tldr-badge"></span>3 &mdash; TL;DR</div>
      <span class="chevron" id="tldr-chev">&#x25BC;</span>
    </div>
    <div class="sec-body open" id="tldr-body">
      <div class="warn" id="no-key-warn">&#x26A0; OPENAI_API_KEY not set &mdash; AI generation unavailable. You can still edit and save manually.</div>
      <label class="field-label">Did (what was built / studied)</label>
      <textarea id="ta-did" rows="2" placeholder="We built / designed / conducted&hellip;"></textarea>
      <label class="field-label">Found (key result)</label>
      <textarea id="ta-found" rows="2" placeholder="We found / show / demonstrate&hellip;"></textarea>
      <label class="field-label">Takeaway (contribution / implication)</label>
      <textarea id="ta-takeaway" rows="2" placeholder="We contribute&hellip;"></textarea>
      <div class="tldr-actions">
        <button class="btn-outline" id="btn-gen" onclick="generateTldr()">&#x2728; Generate with AI</button>
        <button class="btn-primary" onclick="saveTldr()">&#x1F4BE; Save</button>
        <span id="tldr-msg" class="status-msg"></span>
      </div>
    </div>
  </div>
</div>

<script>
const KEY = '__KEY__';
let currentPage = 0, pageCount = 1;
let startX, startY, endX, endY, isDragging = false, hasCrop = false;

// ── section toggle ────────────────────────────────────────────────────────────
function toggle(id){
  const body = document.getElementById(id+'-body');
  const chev = document.getElementById(id+'-chev');
  const open = body.classList.toggle('open');
  chev.classList.toggle('open', open);
}

// ── init ──────────────────────────────────────────────────────────────────────
async function init(){
  const r = await fetch(`/api/${KEY}/info`);
  const p = await r.json();

  document.getElementById('header').innerHTML =
    `<h1>${esc(p.title)}</h1><p class="meta">${p.year||''} ${p.venue_short ? '&bull; '+p.venue_short : ''} &bull; <code style="font-size:.75em">${p.key}</code></p>`;

  // PDF
  setBadge('pdf-badge', p.has_pdf);
  if(p.source_pdf){
    document.getElementById('pdf-src').textContent = p.source_pdf;
    document.getElementById('btn-copy').disabled = p.has_pdf;
    if(p.has_pdf) msg('pdf-msg','PDF already copied to site.','ok');
  } else {
    document.getElementById('pdf-src').textContent = 'No file field found in bib entry';
    msg('pdf-msg','Cannot auto-copy — set a file path in Zotero.','err');
  }

  // Preview
  setBadge('prev-badge', p.has_preview);
  if(p.has_preview){
    document.getElementById('prev-current').innerHTML =
      `<p class="status-msg ok-msg">&#x2713; Preview exists:</p><img class="preview-img" src="/api/${KEY}/preview-image?t=${Date.now()}">`;
  }
  if(p.has_pdf){
    document.getElementById('page-nav').style.display = 'flex';
    renderPage();
  } else {
    msg('prev-msg','Copy the PDF first to use the crop tool.','');
  }

  // TL;DR
  setBadge('tldr-badge', p.has_tldr);
  if(p.tldr && p.tldr.did){
    document.getElementById('ta-did').value      = p.tldr.did      || '';
    document.getElementById('ta-found').value    = p.tldr.found    || '';
    document.getElementById('ta-takeaway').value = p.tldr.takeaway || '';
  }
  // Check OpenAI key availability
  checkApiKey();
}

async function checkApiKey(){
  const r = await fetch('/api/check-openai');
  const d = await r.json();
  if(!d.available){
    document.getElementById('no-key-warn').style.display = 'block';
    document.getElementById('btn-gen').disabled = true;
  }
}

// ── PDF copy ──────────────────────────────────────────────────────────────────
async function copyPdf(){
  const btn = document.getElementById('btn-copy');
  btn.disabled = true; btn.innerHTML = '<span class="spin"></span>Copying&hellip;';
  const r = await fetch(`/api/${KEY}/copy-pdf`,{method:'POST'});
  const d = await r.json();
  if(d.ok){
    msg('pdf-msg','&#x2713; Copied successfully.','ok');
    setBadge('pdf-badge', true);
    document.getElementById('page-nav').style.display = 'flex';
    renderPage();
  } else {
    msg('pdf-msg','Error: '+d.error,'err');
    btn.disabled = false; btn.innerHTML = 'Copy to site';
  }
}

// ── PDF render ────────────────────────────────────────────────────────────────
async function renderPage(){
  const wrap = document.getElementById('crop-wrap');
  const img  = document.getElementById('pdf-img');
  const canvas = document.getElementById('crop-canvas');
  wrap.style.display = 'none';
  msg('prev-msg','<span class="spin"></span>Rendering&hellip;','');

  const r = await fetch(`/api/${KEY}/render?page=${currentPage}`);
  if(!r.ok){ msg('prev-msg','Render failed: '+r.status,'err'); return; }

  pageCount = parseInt(r.headers.get('X-Page-Count')||'1');
  const blob = await r.blob();
  img.onload = () => {
    // size canvas to match img element
    canvas.width  = img.naturalWidth;
    canvas.height = img.naturalHeight;
    canvas.style.display = 'block';
    setupCrop();
  };
  img.src = URL.createObjectURL(blob);
  wrap.style.display = 'inline-block';
  document.getElementById('crop-hint').style.display = 'block';
  document.getElementById('page-info').textContent = `Page ${currentPage+1} / ${pageCount}`;
  msg('prev-msg','','');
}

function changePage(delta){
  currentPage = Math.max(0, Math.min(pageCount-1, currentPage + delta));
  hasCrop = false;
  document.getElementById('crop-actions').style.display = 'none';
  renderPage();
}

// ── crop tool ─────────────────────────────────────────────────────────────────
function setupCrop(){
  const canvas = document.getElementById('crop-canvas');
  const ctx    = canvas.getContext('2d');

  canvas.onmousedown = e => {
    const rc = canvas.getBoundingClientRect();
    const sx = canvas.width  / rc.width;
    const sy = canvas.height / rc.height;
    startX = (e.clientX - rc.left) * sx;
    startY = (e.clientY - rc.top)  * sy;
    endX = startX; endY = startY;
    isDragging = true;
  };

  canvas.onmousemove = e => {
    if(!isDragging) return;
    const rc = canvas.getBoundingClientRect();
    const sx = canvas.width  / rc.width;
    const sy = canvas.height / rc.height;
    endX = (e.clientX - rc.left) * sx;
    endY = (e.clientY - rc.top)  * sy;
    drawOverlay(ctx);
  };

  canvas.onmouseup = () => {
    if(!isDragging) return;
    isDragging = false;
    const w = Math.abs(endX-startX), h = Math.abs(endY-startY);
    if(w > 5 && h > 5){
      hasCrop = true;
      document.getElementById('crop-actions').style.display = 'block';
    }
  };
}

function drawOverlay(ctx){
  const W = ctx.canvas.width, H = ctx.canvas.height;
  const x = Math.min(startX,endX), y = Math.min(startY,endY);
  const w = Math.abs(endX-startX), h = Math.abs(endY-startY);
  ctx.clearRect(0,0,W,H);
  ctx.fillStyle = 'rgba(0,0,0,0.45)';
  ctx.fillRect(0,0,W,H);
  ctx.clearRect(x,y,w,h);
  ctx.strokeStyle = '#4f46e5';
  ctx.lineWidth = 2;
  ctx.strokeRect(x,y,w,h);
  // corner handles
  ctx.fillStyle = '#4f46e5';
  [[x,y],[x+w,y],[x,y+h],[x+w,y+h]].forEach(([cx,cy])=>{
    ctx.beginPath(); ctx.arc(cx,cy,4,0,Math.PI*2); ctx.fill();
  });
}

async function saveCrop(){
  if(!hasCrop){ msg('crop-msg','Draw a selection first.','err'); return; }
  const btn = document.querySelector('#crop-actions button');
  btn.disabled = true; btn.innerHTML = '<span class="spin"></span>Saving&hellip;';

  const x = Math.round(Math.min(startX,endX));
  const y = Math.round(Math.min(startY,endY));
  const w = Math.round(Math.abs(endX-startX));
  const h = Math.round(Math.abs(endY-startY));

  const r = await fetch(`/api/${KEY}/save-preview`,{
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({page:currentPage, x, y, w, h})
  });
  const d = await r.json();
  btn.disabled = false; btn.innerHTML = '&#x1F4BE; Save as preview';
  if(d.ok){
    msg('crop-msg','&#x2713; Saved!','ok');
    setBadge('prev-badge', true);
    document.getElementById('prev-current').innerHTML =
      `<p class="status-msg ok-msg">&#x2713; Preview saved:</p><img class="preview-img" src="/api/${KEY}/preview-image?t=${Date.now()}">`;
  } else {
    msg('crop-msg','Error: '+d.error,'err');
  }
}

// ── TL;DR ─────────────────────────────────────────────────────────────────────
async function generateTldr(){
  const btn = document.getElementById('btn-gen');
  btn.disabled = true; btn.innerHTML = '<span class="spin"></span>Generating&hellip;';
  msg('tldr-msg','','');

  const r = await fetch(`/api/${KEY}/generate-tldr`,{method:'POST'});
  const d = await r.json();
  btn.disabled = false; btn.innerHTML = '&#x2728; Generate with AI';

  if(d.error){ msg('tldr-msg','Error: '+d.error,'err'); return; }
  document.getElementById('ta-did').value      = d.did      || '';
  document.getElementById('ta-found').value    = d.found    || '';
  document.getElementById('ta-takeaway').value = d.takeaway || '';
  msg('tldr-msg','Generated \u2014 review and save.','ok');
}

async function saveTldr(){
  msg('tldr-msg','','');
  const body = {
    did:      document.getElementById('ta-did').value,
    found:    document.getElementById('ta-found').value,
    takeaway: document.getElementById('ta-takeaway').value,
  };
  const r = await fetch(`/api/${KEY}/save-tldr`,{
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify(body)
  });
  const d = await r.json();
  if(d.ok){ msg('tldr-msg','&#x2713; Saved to cache + .md file.','ok'); setBadge('tldr-badge',true); }
  else     { msg('tldr-msg','Error: '+d.error,'err'); }
}

// ── utils ─────────────────────────────────────────────────────────────────────
function esc(s){ return (s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;') }
function setBadge(id, ok){
  document.getElementById(id).className = 'badge '+(ok?'ok':'miss');
  document.getElementById(id).innerHTML = ok?'&#x2713;':'&#x2717;';
}
function msg(id, text, type){
  const el = document.getElementById(id);
  el.innerHTML = text;
  el.className = 'status-msg'+(type==='ok'?' ok-msg':type==='err'?' err-msg':'');
}

init();
</script>
</body>
</html>"""


if __name__ == "__main__":
    threading.Timer(0.8, lambda: webbrowser.open("http://localhost:5000")).start()
    app.run(debug=False, port=5000, threaded=True)
