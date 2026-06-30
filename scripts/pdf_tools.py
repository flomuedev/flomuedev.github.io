#!/usr/bin/env python3
"""
PDF optimisation helpers for the paper manager.

Goal: keep every canonical PDF under Google Scholar's 5 MB crawl limit while
keeping the text layer selectable/searchable (so Scholar can index it).

Two strategies, tried in order by ``shrink_pdf``:

1. Image recompression (lossless-ish, default) — downsample and re-encode the
   raster images embedded in the PDF (photos, screenshots, figure bitmaps).
   The text and vector content are left untouched, so the result stays crisp
   and fully searchable. This resolves the common case of photo-heavy papers.

2. Page rasterisation (aggressive, opt-in) — for papers whose bulk is *vector*
   graphics (huge plots / shading) that image recompression cannot touch, each
   page is rendered to an image and the original text is re-inserted as an
   invisible overlay. The figures lose vector crispness but the file shrinks
   dramatically and the text stays selectable + searchable.

Originals are backed up under ``.pdf_originals/`` before any change, so a
shrink can always be reverted.

Requires: pymupdf (fitz), pikepdf, pillow.
"""

import io
import os
import shutil

SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
BACKUP_DIR  = os.path.join(PROJECT_DIR, ".pdf_originals")

# Google Scholar refuses to index PDFs >= 5 MB. Aim a bit under to leave margin.
SIZE_LIMIT  = 5 * 1024 * 1024
TARGET_SIZE = int(4.7 * 1024 * 1024)

# Image recompression escalation: (max long-edge px, JPEG quality).
_IMG_PASSES = [(2200, 82), (1800, 75), (1500, 65), (1200, 52), (1000, 45)]
# Rasterisation escalation: (DPI, JPEG quality).
_RASTER_PASSES = [(150, 72), (130, 65), (110, 58)]


# ── inspection ──────────────────────────────────────────────────────────────

def is_searchable(path, sample_pages=4, min_chars=100):
    """True if the PDF has an extractable text layer (not a pure scan)."""
    import fitz
    try:
        doc = fitz.open(path)
    except Exception:
        return False
    try:
        n = min(len(doc), sample_pages)
        text = "".join(doc[i].get_text() for i in range(n))
        return len(text.strip()) >= min_chars
    finally:
        doc.close()


def pdf_health(path):
    """Return {exists, size, size_mb, over_limit, searchable, pages}."""
    if not path or not os.path.isfile(path):
        return {"exists": False}
    import fitz
    size = os.path.getsize(path)
    pages = None
    try:
        doc = fitz.open(path)
        pages = len(doc)
        doc.close()
    except Exception:
        pass
    return {
        "exists":     True,
        "size":       size,
        "size_mb":    round(size / (1024 * 1024), 2),
        "over_limit": size >= SIZE_LIMIT,
        "searchable": is_searchable(path),
        "pages":      pages,
        "has_backup": os.path.isfile(os.path.join(BACKUP_DIR, os.path.basename(path))),
    }


# ── backup / revert ─────────────────────────────────────────────────────────

def backup_path(path):
    return os.path.join(BACKUP_DIR, os.path.basename(path))


def ensure_backup(path):
    """Copy the original aside once, so a shrink can be reverted later."""
    os.makedirs(BACKUP_DIR, exist_ok=True)
    bak = backup_path(path)
    if not os.path.isfile(bak):
        shutil.copy2(path, bak)
    return bak


def revert(path):
    """Restore the backed-up original. Returns True if a backup existed."""
    bak = backup_path(path)
    if os.path.isfile(bak):
        shutil.copy2(bak, path)
        return True
    return False


# ── validation ──────────────────────────────────────────────────────────────

def _valid_output(orig_path, new_path, expect_text):
    """A shrink result is only acceptable if it opens, keeps the same page
    count, and (when the original had text) still carries a text layer."""
    import fitz
    try:
        a = fitz.open(orig_path)
        b = fitz.open(new_path)
    except Exception:
        return False
    try:
        if len(b) != len(a):
            return False
        if expect_text:
            text = "".join(b[i].get_text() for i in range(min(len(b), 5)))
            if len(text.strip()) < 50:
                return False
        return True
    finally:
        a.close()
        b.close()


# ── strategy 1: image recompression ─────────────────────────────────────────

def _iter_image_xobjects(pdf):
    """Yield every image XObject in the document, including those nested inside
    Form XObjects (pikepdf ``page.images`` only sees top-level page images)."""
    from pikepdf import Name
    for obj in pdf.objects:
        try:
            if obj.get("/Subtype") == Name("/Image") and obj.get("/Type") in (Name("/XObject"), None):
                yield obj
        except Exception:
            continue


def _recompress_images(pdf, max_dim, quality):
    """Downsample + JPEG-recompress large embedded images in place.
    Returns the number of images changed."""
    from pikepdf import PdfImage, Name
    from PIL import Image

    changed = 0
    for raw in list(_iter_image_xobjects(pdf)):
        try:
            if raw.get("/ImageMask"):       # 1-bit stencil mask — leave alone
                continue
        except Exception:
            continue
        try:
            pil = PdfImage(raw).as_pil_image()
        except Exception:
            continue

        w, h = pil.size
        # Not worth touching small images that are already within budget.
        if (w * h) < 200_000 and max(w, h) <= max_dim:
            continue

        scale = min(1.0, float(max_dim) / max(w, h))
        try:
            if scale < 1.0:
                pil = pil.resize((max(1, int(w * scale)), max(1, int(h * scale))),
                                 Image.LANCZOS)
            gray = pil.mode in ("L", "LA") or raw.get("/ColorSpace") == Name("/DeviceGray")
            pil = pil.convert("L") if gray else pil.convert("RGB")
            buf = io.BytesIO()
            pil.save(buf, format="JPEG", quality=quality, optimize=True, progressive=True)
            data = buf.getvalue()
        except Exception:
            continue

        try:
            current = len(raw.read_raw_bytes())
        except Exception:
            current = None
        if current is not None and len(data) >= current:
            continue  # our re-encode is bigger — keep the original stream

        smask = raw.get("/SMask")           # preserve transparency reference
        raw.write(data, filter=Name("/DCTDecode"))
        raw.ColorSpace = Name("/DeviceGray") if gray else Name("/DeviceRGB")
        raw.BitsPerComponent = 8
        if smask is not None:
            raw.SMask = smask
        for k in ("/DecodeParms", "/Decode"):
            if k in raw:
                del raw[k]
        changed += 1
    return changed


def _save_images(src, out, max_dim, quality):
    import pikepdf
    with pikepdf.open(src) as pdf:
        _recompress_images(pdf, max_dim, quality)
        pdf.remove_unreferenced_resources()
        pdf.save(out, compress_streams=True, recompress_flate=True,
                 object_stream_mode=pikepdf.ObjectStreamMode.generate)


def _save_lossless(src, out):
    import pikepdf
    with pikepdf.open(src) as pdf:
        pdf.remove_unreferenced_resources()
        pdf.save(out, compress_streams=True, recompress_flate=True,
                 object_stream_mode=pikepdf.ObjectStreamMode.generate)


# ── strategy 2: rasterise pages, keep invisible text ────────────────────────

def _save_raster(src, out, dpi, quality):
    """Render every page to a JPEG and re-insert the original text as an
    invisible (render_mode 3) overlay so the result stays searchable."""
    import fitz
    from PIL import Image

    doc = fitz.open(src)
    new = fitz.open()
    try:
        for page in doc:
            pix = page.get_pixmap(dpi=dpi)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=quality, optimize=True)

            np = new.new_page(width=page.rect.width, height=page.rect.height)
            np.insert_image(page.rect, stream=buf.getvalue())

            tw = fitz.TextWriter(page.rect)
            wrote = False
            for x0, y0, x1, y1, word, *_ in page.get_text("words"):
                fs = max(2.0, (y1 - y0) * 0.85)
                try:
                    tw.append(fitz.Point(x0, y1 - (y1 - y0) * 0.18), word, fontsize=fs)
                    wrote = True
                except Exception:
                    pass
            if wrote:
                try:
                    tw.write_text(np, render_mode=3)
                except Exception:
                    pass
        new.save(out, garbage=4, deflate=True)
    finally:
        new.close()
        doc.close()


# ── orchestration ───────────────────────────────────────────────────────────

def shrink_pdf(path, target=TARGET_SIZE, limit=SIZE_LIMIT, allow_raster=False):
    """Shrink ``path`` in place toward ``target`` bytes.

    Tries lossless cleanup, then image recompression, then (only if
    ``allow_raster``) page rasterisation. Keeps the smallest *valid* result and
    never enlarges the file. The original is backed up first.

    Returns a result dict describing what happened.
    """
    before = os.path.getsize(path)
    expect_text = is_searchable(path)
    ensure_backup(path)
    src = backup_path(path)             # always shrink from the pristine original

    tmp  = path + ".shrink.tmp"
    best = path + ".shrink.best"
    state = {"size": before, "method": "none", "file": None}

    def consider(method):
        if not os.path.isfile(tmp):
            return
        size = os.path.getsize(tmp)
        if size < state["size"] and _valid_output(src, tmp, expect_text):
            shutil.move(tmp, best)
            state.update(size=size, method=method, file=best)
        elif os.path.isfile(tmp):
            os.remove(tmp)

    def reached():
        return state["file"] is not None and state["size"] <= target

    # 1. lossless stream cleanup
    try:
        _save_lossless(src, tmp)
        consider("lossless")
    except Exception:
        pass

    # 2. image recompression, escalating
    if not reached():
        for max_dim, q in _IMG_PASSES:
            try:
                _save_images(src, tmp, max_dim, q)
                consider(f"images@{max_dim}px/q{q}")
            except Exception:
                pass
            if reached():
                break

    # 3. rasterisation (opt-in), escalating
    if allow_raster and not reached():
        for dpi, q in _RASTER_PASSES:
            try:
                _save_raster(src, tmp, dpi, q)
                consider(f"raster@{dpi}dpi/q{q}")
            except Exception:
                pass
            if reached():
                break

    if os.path.isfile(tmp):
        os.remove(tmp)

    changed = False
    if state["file"] and state["size"] < before:
        shutil.move(state["file"], path)
        changed = True
    elif os.path.isfile(best):
        os.remove(best)

    after = os.path.getsize(path)
    return {
        "ok":               True,
        "changed":          changed,
        "before":           before,
        "after":            after,
        "before_mb":        round(before / (1024 * 1024), 2),
        "after_mb":         round(after / (1024 * 1024), 2),
        "method":           state["method"],
        "under_limit":      after < limit,
        "reached_target":   after <= target,
        "searchable_before": expect_text,
        "searchable_after": is_searchable(path),
        "rasterized":       state["method"].startswith("raster"),
    }
