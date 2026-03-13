#!/usr/bin/env python3
"""Generate structured TL;DR summaries for publications using OpenAI.

  python scripts/generate_tldrs.py           # generate for all uncached papers
  python scripts/generate_tldrs.py KEY       # regenerate for one specific paper

Requires: pip install openai pypdf
Set OPENAI_API_KEY environment variable.
"""
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys

MODEL = "gpt-4o-mini"
PROMPT = """Generate a structured TL;DR for this HCI research paper with exactly three parts.
Return ONLY a JSON object with these three keys:
- "did": one sentence describing what was built, designed, or studied — written in first person plural ("We built...", "We conducted...", "We designed...")
- "found": one sentence about the key result or finding — written in first person plural ("We found...", "We show...", "We demonstrate...")
- "takeaway": one sentence about the practical implication or contribution

Do not use generic phrases like "This paper presents". Be specific. Always use "we" as the subject for "did" and "found".
Do not introduce abbreviations — always write terms out in full (e.g. "Extended Reality" not "XR", "Augmented Reality" not "AR", "Human-Computer Interaction" not "HCI").

{paper_content}"""


def abstract_hash(abstract):
    return hashlib.sha256(abstract.strip().encode("utf-8")).hexdigest()


def load_cache(path):
    if os.path.isfile(path):
        data = json.load(open(path, encoding="utf-8"))
        return data.get("entries", {}) if isinstance(data, dict) else {}
    return {}


def save_cache(path, entries):
    json.dump(
        {"version": 1, "entries": entries},
        open(path, "w", encoding="utf-8"),
        indent=2,
        ensure_ascii=False,
        sort_keys=True,
    )


def extract_pdf_text(pdf_path):
    """Extract text from PDF, returning empty string on failure."""
    try:
        import pypdf
        reader = pypdf.PdfReader(pdf_path)
        pages = [page.extract_text() or "" for page in reader.pages]
        text = "\n".join(pages).strip()
        # pypdf can produce lone UTF-16 surrogates (e.g. \ud835 for math symbols);
        # strip them so the text can be safely JSON-serialized as UTF-8.
        text = re.sub(r'[\ud800-\udfff]', '', text)
        return text
    except Exception as e:
        print(f"  WARNING: could not extract PDF text ({e})")
        return ""


def build_paper_content(pub, pdf_dir):
    """Assemble paper content: use full PDF if available, fall back to abstract."""
    abstract = pub.get("abstract", "").strip()
    pdf_file = pub.get("pdf", "")
    if pdf_file:
        pdf_path = os.path.join(pdf_dir, pdf_file)
        if os.path.isfile(pdf_path):
            pdf_text = extract_pdf_text(pdf_path)
            if pdf_text:
                title = pub.get("title", "")
                full = f"Title: {title}\n\nFull paper text:\n{pdf_text[:100000]}"
                return full, True
    return f"Abstract:\n{abstract}", False


def generate_tldr(client, paper_content):
    response = client.chat.completions.create(
        model=MODEL,
        response_format={"type": "json_object"},
        messages=[{"role": "user", "content": PROMPT.format(paper_content=paper_content)}],
        max_tokens=300,
    )
    result = json.loads(response.choices[0].message.content)
    return {
        "did": result.get("did", "").strip(),
        "found": result.get("found", "").strip(),
        "takeaway": result.get("takeaway", "").strip(),
    }


def patch_md_frontmatter(md_path, tldr):
    """Insert/replace tldr_did, tldr_found, tldr_takeaway in TOML frontmatter."""
    if not os.path.isfile(md_path):
        return
    content = open(md_path, encoding="utf-8").read()
    parts = content.split("+++", 2)
    if len(parts) != 3:
        print(f"  WARNING: unexpected frontmatter in {md_path}")
        return
    toml_body, md_body = parts[1], parts[2]

    for field, value in [
        ("tldr_did", tldr["did"]),
        ("tldr_found", tldr["found"]),
        ("tldr_takeaway", tldr["takeaway"]),
    ]:
        escaped = value.replace("\\", "\\\\").replace('"', '\\"')
        new_line = f'{field} = "{escaped}"'
        if re.search(rf"^{field}\s*=", toml_body, re.MULTILINE):
            toml_body = re.sub(
                rf"^{field}\s*=.*$", new_line, toml_body, flags=re.MULTILINE
            )
        else:
            toml_body = toml_body.rstrip("\n") + "\n" + new_line + "\n"

    open(md_path, "w", encoding="utf-8").write("+++" + toml_body + "+++" + md_body)


def main():
    parser = argparse.ArgumentParser(
        description="Generate TL;DR summaries for publications using OpenAI."
    )
    parser.add_argument(
        "key", nargs="?", metavar="KEY",
        help="Paper key to regenerate (omit to process all uncached papers)"
    )
    parser.add_argument(
        "--years", metavar="YEARS",
        help="Comma-separated years to filter (e.g. 2025,2026)"
    )
    parser.add_argument(
        "--force-all", action="store_true",
        help="Regenerate TL;DRs for all papers, ignoring the cache"
    )
    args = parser.parse_args()

    project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    pubs_path = os.path.join(project_dir, "data", "publications.json")
    cache_path = os.path.join(project_dir, "data", "tldrs_cache.json")
    content_dir = os.path.join(project_dir, "content", "publication")
    pdf_dir = os.path.join(project_dir, "static", "pdf")

    # Always re-parse bib.bib first so publications.json and .md files are fresh
    print("Running parse_bib.py...")
    parse_bib = os.path.join(os.path.dirname(os.path.abspath(__file__)), "parse_bib.py")
    subprocess.run([sys.executable, parse_bib], check=True)

    publications = json.load(open(pubs_path, encoding="utf-8"))
    cache = load_cache(cache_path)
    print(f"Loaded {len(publications)} publications, cache has {len(cache)} entries")

    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        sys.exit("Error: OPENAI_API_KEY environment variable not set")
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
    except ImportError:
        sys.exit("Error: run 'pip install openai pypdf' first")

    # Year filter
    year_filter = None
    if args.years:
        year_filter = {int(y.strip()) for y in args.years.split(",")}
        print(f"Filtering to years: {sorted(year_filter)}")

    # If a key is given, only process that one paper
    target_key = args.key
    if target_key and not any(p.get("key") == target_key for p in publications):
        sys.exit(f"Error: paper key '{target_key}' not found in publications.json")

    generated = from_cache = skipped = 0
    for pub in publications:
        abstract = pub.get("abstract", "").strip()
        key = pub.get("key", "")

        # Skip papers outside year filter or not targeted
        if year_filter and pub.get("year") not in year_filter and not target_key:
            h = abstract_hash(abstract) if abstract else None
            if h and h in cache:
                tldr = cache[h]
                pub["tldr_did"] = tldr.get("did", "")
                pub["tldr_found"] = tldr.get("found", "")
                pub["tldr_takeaway"] = tldr.get("takeaway", "")
            continue

        if target_key and key != target_key:
            # Still carry over existing tldr fields from cache so JSON stays complete
            h = abstract_hash(abstract) if abstract else None
            if h and h in cache:
                tldr = cache[h]
                pub["tldr_did"] = tldr.get("did", "")
                pub["tldr_found"] = tldr.get("found", "")
                pub["tldr_takeaway"] = tldr.get("takeaway", "")
            continue

        if not abstract:
            pub["tldr_did"] = pub["tldr_found"] = pub["tldr_takeaway"] = ""
            skipped += 1
            continue

        h = abstract_hash(abstract)
        # Force regeneration when a specific key is targeted or --force-all is set
        use_cache = h in cache and not target_key and not args.force_all

        if use_cache:
            tldr = cache[h]
            pub["tldr_did"] = tldr.get("did", "")
            pub["tldr_found"] = tldr.get("found", "")
            pub["tldr_takeaway"] = tldr.get("takeaway", "")
            from_cache += 1
        else:
            paper_content, used_pdf = build_paper_content(pub, pdf_dir)
            src = "PDF" if used_pdf else "abstract"
            try:
                tldr = generate_tldr(client, paper_content)
                cache[h] = tldr
                pub["tldr_did"] = tldr["did"]
                pub["tldr_found"] = tldr["found"]
                pub["tldr_takeaway"] = tldr["takeaway"]
                generated += 1
                print(f"  Generated [{src}]: {key}")
                print(f"    Did:      {tldr['did'][:90]}")
                print(f"    Found:    {tldr['found'][:90]}")
                print(f"    Takeaway: {tldr['takeaway'][:90]}")
            except Exception as e:
                print(f"  ERROR for {key}: {e}")
                pub["tldr_did"] = pub["tldr_found"] = pub["tldr_takeaway"] = ""

    print(
        f"\nTL;DRs: {from_cache} from cache, {generated} newly generated, "
        f"{skipped} skipped (no abstract)"
    )

    save_cache(cache_path, cache)
    json.dump(
        publications,
        open(pubs_path, "w", encoding="utf-8"),
        indent=2,
        ensure_ascii=False,
    )
    print(f"Saved cache -> {cache_path}")
    print(f"Updated publications.json with tldr fields")

    patched = 0
    for pub in publications:
        if not pub.get("key"):
            continue
        if target_key and pub["key"] != target_key:
            continue
        if year_filter and pub.get("year") not in year_filter and not target_key:
            continue
        md_path = os.path.join(content_dir, f"{pub['key']}.md")
        patch_md_frontmatter(
            md_path,
            {
                "did": pub.get("tldr_did", ""),
                "found": pub.get("tldr_found", ""),
                "takeaway": pub.get("tldr_takeaway", ""),
            },
        )
        patched += 1
    print(f"Patched {patched} markdown frontmatter file(s)")
    print("\nReview data/tldrs_cache.json, then commit when satisfied.")


if __name__ == "__main__":
    main()
