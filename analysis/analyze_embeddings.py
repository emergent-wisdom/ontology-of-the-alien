#!/usr/bin/env python3
"""
Reproduce the sentence-embedding distinctness analysis (Section 3.1) of
"The Ontology of the Alien".

Method (as stated in 3.1): every core mechanism is embedded with the
all-MiniLM-L6-v2 sentence-transformer. For each mechanism we take its best-match
cosine similarity WITHIN its own condition (excluding itself) and its best-match
similarity AGAINST the other conditions. We report mean within- vs mean
between-condition similarity, the overall concentration ratio, and the
per-condition within/between ratio.

Two modes:

  (default)     Full reproduction over all eight conditions. Requires
                sentence-transformers + the all-MiniLM-L6-v2 weights. Embeds
                solution.core_mechanism from every run file.

  --from-cache  Offline partial check for the three taxonomy conditions (B, E, H)
                only, using the MECHANISM-node embeddings already stored in
                <dir>/taxonomy.db -- no model load. This corroborates the
                within-condition magnitude but CANNOT reproduce the
                between-condition figure, because the five non-taxonomy
                conditions (A, C, D, F, G) persist no embeddings on disk.

Published values: within 0.566, between 0.512, ratio 1.10x; per-condition
ratios E 1.23, D 1.15, B 1.12, F 1.05, G 1.02.

Run:  python3 analysis/analyze_embeddings.py              # full (needs model)
      python3 analysis/analyze_embeddings.py --from-cache # offline, B/E/H within
"""
import json
import re
import sqlite3
import sys
from pathlib import Path

import numpy as np

BASE = Path(__file__).resolve().parent.parent

# paper condition letter -> experiment directory
CONDITIONS = [
    ("A", "semantic_tabu"),
    ("B", "taxonomy"),
    ("C", "random_seed"),
    ("D", "seed_tabu"),
    ("E", "taxonomy_seed"),
    ("F", "strange_worlds"),
    ("G", "strange_worlds_tabu"),
    ("H", "taxonomy_worlds"),
]
TAXONOMY_DIRS = {"B": "taxonomy", "E": "taxonomy_seed", "H": "taxonomy_worlds"}
PAPER_RATIO = {"E": 1.23, "D": 1.15, "B": 1.12, "F": 1.05, "G": 1.02}


def extract_core_mechanisms(directory):
    """Tolerant load of solution.core_mechanism for each run file (handles the
    run JSONs whose `reasoning` field breaks strict parsing, and the few with an
    empty top-level solution by regex-recovering the field from raw text)."""
    texts = []
    for f in sorted((BASE / directory).glob("*.json")):
        if "bank" in f.name:
            continue
        raw = f.read_text(errors="replace")
        cm = None
        try:
            cm = (json.loads(raw).get("solution") or {}).get("core_mechanism")
        except Exception:
            pass
        if not cm:
            m = re.search(r'"core_mechanism"\s*:\s*"((?:[^"\\]|\\.)*)"', raw)
            if m:
                try:
                    cm = json.loads('"' + m.group(1) + '"')
                except Exception:
                    cm = m.group(1)
        if cm and cm.strip():
            texts.append(cm.strip())
    return texts


def per_mechanism_stats(by_cond):
    """by_cond: {letter: ndarray[n, 384]}. Best-match within (excl self) and
    best-match against all out-of-condition mechanisms, per the paper's method."""
    letters = list(by_cond)
    within_all, between_all = [], []
    per = {}
    for c in letters:
        V = by_cond[c]
        others = (np.vstack([by_cond[o] for o in letters if o != c])
                  if len(letters) > 1 else None)
        w_list, b_list = [], []
        for i in range(len(V)):
            sims = V @ V[i]
            sims[i] = -1.0                      # exclude self
            if len(V) > 1:
                w_list.append(float(sims.max())); within_all.append(float(sims.max()))
            if others is not None and len(others):
                b = float((others @ V[i]).max())
                b_list.append(b); between_all.append(b)
        wm = float(np.mean(w_list)) if w_list else float("nan")
        bm = float(np.mean(b_list)) if b_list else float("nan")
        per[c] = (wm, bm, (wm / bm if bm == bm and bm else float("nan")))
    within = float(np.mean(within_all)) if within_all else float("nan")
    between = float(np.mean(between_all)) if between_all else float("nan")
    return within, between, per


def report(within, between, per, partial=False):
    print(f"\nmean within-condition cosine : {within:.3f}   (paper 0.566)")
    if between == between:
        note = ", restricted to {B,E,H} -- NOT comparable to paper" if partial else " -- full 8 conditions"
        print(f"mean between-condition cosine: {between:.3f}   (paper 0.512{note})")
        print(f"overall concentration ratio : {within / between:.3f}x (paper 1.10x)")
    print("per-condition  within / between / ratio:")
    for c, (w, b, r) in sorted(per.items()):
        pr = f"   (paper {PAPER_RATIO[c]:.2f}x)" if c in PAPER_RATIO else ""
        print(f"   {c}: {w:.3f} / {b:.3f} / {r:.2f}x{pr}")


def run_full():
    try:
        from sentence_transformers import SentenceTransformer
    except Exception as e:
        print(f"[full mode unavailable] cannot import sentence-transformers: {e}\n"
              f"Use --from-cache for the offline partial check, or repair the model env.")
        return 1
    model = SentenceTransformer("all-MiniLM-L6-v2")
    by_cond = {}
    for letter, d in CONDITIONS:
        texts = extract_core_mechanisms(d)
        if not texts:
            print(f"  WARN: no mechanisms for {letter} ({d})")
            continue
        by_cond[letter] = model.encode(texts, convert_to_numpy=True).astype(np.float32)
        print(f"  {letter} ({d}): {len(texts)} core mechanisms")
    report(*per_mechanism_stats(by_cond))
    return 0


def run_from_cache():
    """Offline check using the SAME unit as full mode (per-solution core
    mechanisms), with vectors recovered from the runtime embedding cache rather
    than re-running the model. Only the three taxonomy conditions persist a cache."""
    by_cond = {}
    for letter, d in TAXONOMY_DIRS.items():
        con = sqlite3.connect(BASE / d / "taxonomy.db")
        cache = {text: np.frombuffer(emb, dtype=np.float32)
                 for text, emb in con.execute("SELECT text, embedding FROM embedding_cache")}
        con.close()
        texts = extract_core_mechanisms(d)
        vecs = [cache[t] for t in texts if t in cache]
        by_cond[letter] = np.vstack(vecs)
        print(f"  {letter} ({d}): {len(vecs)}/{len(texts)} core mechanisms recovered from embedding cache")
    print("\n[offline partial check -- taxonomy conditions B/E/H only; between-condition "
          "is over {B,E,H}, not the full 8-condition universe the paper reports]")
    report(*per_mechanism_stats(by_cond), partial=True)
    return 0


if __name__ == "__main__":
    sys.exit(run_from_cache() if "--from-cache" in sys.argv else run_full())
