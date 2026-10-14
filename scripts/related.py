"""Related-publication ranking for paper pages.

Similarity comes from OpenAI text embeddings of each paper's title, keywords
and abstract. The vectors are cached in data/embeddings_cache.json (committed,
keyed by a hash of the embedded text), so parse_bib.py can rank papers in CI
without an API key. Papers that have no cached embedding yet fall back to
TF-IDF similarity over the same text.

Fill the cache with:  python scripts/generate_embeddings.py
"""
import collections
import hashlib
import json
import math
import os
import re

MODEL = "text-embedding-3-small"
DIMENSIONS = 256

RELATED_COUNT = 3
# Entry types that are never suggested: edited proceedings, the dissertation, patents
EXCLUDED_TYPES = {"book", "patent"}
# Below these similarities a paper is not considered related at all
MIN_SIMILARITY = {"embedding": 0.5, "tfidf": 0.08}
# Small nudge towards papers with shared co-authors (same project / team)
COAUTHOR_BONUS = 0.03
# Maximal marginal relevance: 1.0 = pure similarity, lower = more varied picks
MMR_LAMBDA = 0.75

# Keywords that describe the bib file's bookkeeping, not the paper's topic
_NOISE_KEYWORDS = {"xr", "mobile", "embodied", "ai", "notion", "softwarecampus",
                   "human factors", "computer science - human-computer interaction"}


# ── embedding text & cache ────────────────────────────────────────────────────

def embedding_text(pub):
    """The text a paper is represented by (title, topical keywords, abstract)."""
    keywords = [k.strip() for k in (pub.get("keywords") or "").split(",")
                if k.strip() and k.strip().lower() not in _NOISE_KEYWORDS]
    parts = [f"Title: {pub.get('title', '').strip()}"]
    if keywords:
        parts.append("Keywords: " + ", ".join(keywords))
    abstract = (pub.get("abstract") or "").strip()
    if abstract:
        parts.append(f"Abstract: {abstract}")
    return "\n".join(parts)


def text_hash(text):
    return hashlib.sha256(f"{MODEL}:{DIMENSIONS}:{text}".encode("utf-8")).hexdigest()


def load_cache(path):
    if os.path.isfile(path):
        data = json.load(open(path, encoding="utf-8"))
        if isinstance(data, dict):
            return data.get("entries", {})
    return {}


def save_cache(path, entries):
    with open(path, "w", encoding="utf-8") as f:
        f.write('{\n  "version": 1,\n')
        f.write(f'  "model": "{MODEL}",\n  "dimensions": {DIMENSIONS},\n')
        f.write('  "entries": {\n')
        # One vector per line keeps git diffs readable
        lines = [f'    "{h}": {json.dumps([round(x, 5) for x in v])}'
                 for h, v in sorted(entries.items())]
        f.write(",\n".join(lines))
        f.write("\n  }\n}\n")


def embed(client, texts):
    """Embed a list of texts with one API call; returns unit-length vectors."""
    response = client.embeddings.create(model=MODEL, input=texts, dimensions=DIMENSIONS)
    return [_normalize(item.embedding) for item in sorted(response.data, key=lambda d: d.index)]


# ── similarity ────────────────────────────────────────────────────────────────

def _normalize(vec):
    norm = math.sqrt(sum(x * x for x in vec)) or 1.0
    return [x / norm for x in vec]


def _dot(a, b):
    return sum(x * y for x, y in zip(a, b))


_STOP = set("""a an the and or of to in on for with by from at as is are was were be been
this that these those we our us it its their they can could may might which while when
where how what than then into over under between across through about via using use used
based study studies paper results show shows found participants user users new also both
two three one more most such not no do does did have has had per each other vs""".split())


def _tfidf_vectors(texts):
    """Sparse, unit-length TF-IDF vectors (unigrams + bigrams) for a dict of texts."""
    docs = {}
    for key, text in texts.items():
        words = [w for w in re.findall(r"[a-z][a-z0-9\-]+", text.lower())
                 if w not in _STOP and len(w) > 2]
        docs[key] = collections.Counter(words + [a + "_" + b for a, b in zip(words, words[1:])])
    df = collections.Counter(t for counts in docs.values() for t in counts)
    n = len(docs)
    vectors = {}
    for key, counts in docs.items():
        vec = {t: (1 + math.log(c)) * math.log(n / df[t]) for t, c in counts.items() if df[t] > 1}
        norm = math.sqrt(sum(x * x for x in vec.values())) or 1.0
        vectors[key] = {t: x / norm for t, x in vec.items()}
    return vectors


def _sparse_dot(a, b):
    if len(a) > len(b):
        a, b = b, a
    return sum(x * b.get(t, 0.0) for t, x in a.items())


def _coauthors(pub, owner):
    return {a.strip() for a in (pub.get("authors") or "").split(",")
            if a.strip() and a.strip() != owner}


def compute_related(publications, cache, owner, overrides=None, groups=None):
    """Return {key: [related keys]} for every publication.

    overrides: optional {key: {"pin": [...], "block": [...]}} — pinned keys come
    first (in order), blocked keys are never suggested for that paper.
    groups: optional list of key lists, each one work published in several
    versions (see data/projects.yml). A paper never lists its own versions, and
    each other work fills at most one slot.
    """
    overrides = overrides or {}
    group_of = group_index(groups or [])
    by_key = {p["key"]: p for p in publications}
    texts = {p["key"]: embedding_text(p) for p in publications}
    emb = {k: cache[text_hash(t)] for k, t in texts.items() if text_hash(t) in cache}
    tfidf = _tfidf_vectors(texts)
    authors = {p["key"]: _coauthors(p, owner) for p in publications}
    candidates = [p["key"] for p in publications if p.get("type") not in EXCLUDED_TYPES]

    def similarity(a, b, mode):
        return _dot(emb[a], emb[b]) if mode == "embedding" else _sparse_dot(tfidf[a], tfidf[b])

    related = {}
    for key in by_key:
        # Rank with embeddings when this paper has one, otherwise with TF-IDF;
        # the two score scales are not comparable, so never mix them.
        mode = "embedding" if key in emb else "tfidf"
        rule = overrides.get(key) or {}
        blocked = set(rule.get("block") or []) | group_of.get(key, set())
        pool = [c for c in candidates
                if c != key and c not in blocked and (mode == "tfidf" or c in emb)]

        scores = {}
        for c in pool:
            s = similarity(key, c, mode)
            if s < MIN_SIMILARITY[mode]:
                continue
            if authors[key] & authors[c]:
                s += COAUTHOR_BONUS
            scores[c] = s

        picked = [k for k in (rule.get("pin") or []) if k in by_key and k != key]
        remaining = [c for c in scores if c not in picked]
        while len(picked) < RELATED_COUNT and remaining:
            # Maximal marginal relevance: similar to this paper, but not a
            # near-copy of a paper that is already picked
            def mmr(c):
                redundancy = max((similarity(c, p, mode) for p in picked
                                  if mode == "tfidf" or p in emb), default=0.0)
                return MMR_LAMBDA * scores[c] - (1 - MMR_LAMBDA) * redundancy
            best = max(remaining, key=lambda c: (mmr(c), by_key[c].get("year", 0)))
            picked.append(best)
            # Other versions of the picked work are no longer candidates
            remaining = [c for c in remaining if c != best and c not in group_of.get(best, ())]
        related[key] = picked[:RELATED_COUNT]
    return related


# ── versions of the same work ─────────────────────────────────────────────────

# A suggested pair must share at least this share of the smaller author list ...
VERSION_AUTHOR_OVERLAP = 0.5
# ... and either the same title prefix or near-identical text
VERSION_SIMILARITY = 0.9


def group_index(groups):
    """{key: set of the other keys in its group} for a list of key lists."""
    index = {}
    for group in groups:
        for key in group:
            index[key] = set(group) - {key}
    return index


def title_prefix(title):
    """The project name a title starts with: 'ShadAR', "Let's Frets", ..."""
    match = re.match(r"\s*([^:!?]{2,60}?)\s*[:!?]", title or "")
    return match.group(1).lower() if match else ""


def suggest_versions(publications, cache, groups=None, dismissed=None):
    """Pairs of papers that look like versions of the same work but are not
    grouped or dismissed yet. Returns [(key_a, key_b, reason)], newest first."""
    grouped = group_index(groups or [])
    dismissed = {frozenset(pair) for pair in (dismissed or []) if len(pair) == 2}
    emb = {}
    for p in publications:
        h = text_hash(embedding_text(p))
        if h in cache:
            emb[p["key"]] = cache[h]
    authors = {p["key"]: {a.strip() for a in (p.get("authors") or "").split(",") if a.strip()}
               for p in publications}

    suggestions = []
    for i, a in enumerate(publications):
        for b in publications[i + 1:]:
            ka, kb = a["key"], b["key"]
            if kb in grouped.get(ka, ()) or frozenset((ka, kb)) in dismissed:
                continue
            shared = authors[ka] & authors[kb]
            smaller = min(len(authors[ka]), len(authors[kb])) or 1
            if len(shared) / smaller < VERSION_AUTHOR_OVERLAP:
                continue
            prefix = title_prefix(a.get("title"))
            if prefix and prefix == title_prefix(b.get("title")):
                suggestions.append((ka, kb, f'same title prefix "{prefix}"'))
            elif ka in emb and kb in emb and _dot(emb[ka], emb[kb]) >= VERSION_SIMILARITY:
                suggestions.append((ka, kb, f"similarity {_dot(emb[ka], emb[kb]):.2f}"))
    return suggestions
