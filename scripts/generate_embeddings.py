#!/usr/bin/env python3
"""Embed publications with OpenAI so parse_bib.py can rank related papers.

  python scripts/generate_embeddings.py           # embed papers missing from the cache
  python scripts/generate_embeddings.py --force   # re-embed every paper

Requires: pip install openai
Set OPENAI_API_KEY environment variable.
"""
import argparse
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import related


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--force", action="store_true", help="Re-embed all papers, ignoring the cache")
    args = parser.parse_args()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(script_dir)
    pubs_path = os.path.join(project_dir, "data", "publications.json")
    cache_path = os.path.join(project_dir, "data", "embeddings_cache.json")
    parse_bib = os.path.join(script_dir, "parse_bib.py")

    # Re-parse first so the texts match the current bib.bib
    print("Running parse_bib.py...")
    subprocess.run([sys.executable, parse_bib], check=True)

    publications = json.load(open(pubs_path, encoding="utf-8"))
    cache = {} if args.force else related.load_cache(cache_path)

    # Only keep vectors for texts that still exist, so the cache doesn't grow forever
    texts = {}
    for pub in publications:
        text = related.embedding_text(pub)
        texts[related.text_hash(text)] = (pub["key"], text)
    stale = set(cache) - set(texts)
    for h in stale:
        del cache[h]

    missing = [(h, key, text) for h, (key, text) in texts.items() if h not in cache]
    print(f"{len(publications)} publications, {len(cache)} cached embeddings, "
          f"{len(missing)} to embed, {len(stale)} stale removed")

    if missing:
        api_key = os.environ.get("OPENAI_API_KEY", "")
        if not api_key:
            sys.exit("Error: OPENAI_API_KEY environment variable not set")
        try:
            from openai import OpenAI
        except ImportError:
            sys.exit("Error: run 'pip install openai' first")
        client = OpenAI(api_key=api_key)
        vectors = related.embed(client, [text for _, _, text in missing])
        for (h, key, _), vec in zip(missing, vectors):
            cache[h] = vec
            print(f"  Embedded: {key}")

    if missing or stale:
        related.save_cache(cache_path, cache)
        print(f"Saved cache -> {cache_path}")
        # Re-run so publications.json picks up the new related lists
        print("Running parse_bib.py...")
        subprocess.run([sys.executable, parse_bib], check=True)
    else:
        print("Nothing to do.")


if __name__ == "__main__":
    try:
        from dotenv import load_dotenv
        load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env"), override=True)
    except ImportError:
        pass
    main()
