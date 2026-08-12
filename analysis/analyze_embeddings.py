#!/usr/bin/env python3
"""Reproduce the revised sentence-embedding analysis.

The canonical corpus contains 196 candidate records: 125 retained outputs and
71 curator-accepted graph records. Non-taxonomy conditions are loaded from run
JSON; taxonomy conditions are loaded from their SQLite graphs because one
accepted B record is absent from the top-level run
JSON.  The full calculation uses L2-normalized all-MiniLM-L6-v2 vectors.

For each solution i in condition c:

  within_i = max cosine to another solution in c
  between_i = mean_d(max cosine to a solution in other condition d)

The reported within and between values are means over solutions.  These are
descriptive properties of generated text, not estimates of creativity or
external novelty.

Run:
  python3 analysis/analyze_embeddings.py
  python3 analysis/analyze_embeddings.py --from-cache

Full mode needs sentence-transformers and the pinned model revision.  The
offline cache mode uses persisted taxonomy vectors and is therefore restricted
to B, E, and H; its between-condition result is not comparable to the full
eight-condition result.
"""

import json
import sqlite3
import sys
from pathlib import Path

import numpy as np


BASE = Path(__file__).resolve().parent.parent
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
MODEL_REVISION = "1110a243fdf4706b3f48f1d95db1a4f5529b4d41"
MODEL_WEIGHTS_SHA256 = (
    "53aa51172d142c89d9012cce15ae4d6cc0ca6895895114379cacb4fab128d9db"
)

CONDITIONS = [
    ("A", "semantic_tabu", "tabu_*.json"),
    ("B", "taxonomy", None),
    ("C", "random_seed", "seed_*.json"),
    ("D", "seed_tabu", "seed_tabu_*.json"),
    ("E", "taxonomy_seed", None),
    ("F", "strange_worlds", "worlds_*.json"),
    ("G", "strange_worlds_tabu", "worlds_tabu_*.json"),
    ("H", "taxonomy_worlds", None),
]
TAXONOMY_DIRS = {"B": "taxonomy", "E": "taxonomy_seed", "H": "taxonomy_worlds"}

REVISED_VALUES = {
    "A": (0.572923, 0.526854, 1.08744),
    "B": (0.585403, 0.521190, 1.12320),
    "C": (0.575248, 0.537472, 1.07028),
    "D": (0.656331, 0.568998, 1.15349),
    "E": (0.565637, 0.483714, 1.16936),
    "F": (0.523732, 0.498634, 1.05033),
    "G": (0.495540, 0.485554, 1.02057),
    "H": (0.532109, 0.484197, 1.09895),
}
REVISED_OVERALL = (0.563459, 0.513544, 1.09720)


def load_run_records(directory, pattern):
    """Load solution objects from a condition whose run files are valid JSON."""
    records = []
    for path in sorted((BASE / directory).glob(pattern)):
        if "bank" in path.name:
            continue
        payload = json.loads(path.read_text())
        solution = payload.get("solution") or {}
        if solution.get("core_mechanism"):
            records.append(solution)
    return records


def load_taxonomy_records(directory):
    """Load accepted solution objects from the graph, the canonical tax source."""
    con = sqlite3.connect(BASE / directory / "taxonomy.db")
    rows = con.execute(
        "SELECT metadata FROM nodes WHERE node_type = 'SOLUTION' ORDER BY rowid"
    ).fetchall()
    con.close()
    records = []
    for (metadata,) in rows:
        solution = json.loads(metadata).get("full_solution") or {}
        if solution.get("core_mechanism"):
            records.append(solution)
    return records


def canonical_texts():
    result = {}
    for letter, directory, pattern in CONDITIONS:
        records = (
            load_taxonomy_records(directory)
            if pattern is None
            else load_run_records(directory, pattern)
        )
        result[letter] = [record["core_mechanism"].strip() for record in records]
    return result


def normalized(rows):
    matrix = np.asarray(rows, dtype=np.float32)
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    if np.any(norms == 0):
        raise ValueError("zero-length embedding encountered")
    return matrix / norms


def calculate(by_condition):
    """Return corpus and per-condition within/between descriptive statistics."""
    per_condition = {}
    all_within = []
    all_between = []

    for letter, vectors in by_condition.items():
        within = vectors @ vectors.T
        np.fill_diagonal(within, -np.inf)
        within_best = within.max(axis=1)

        cross_best = []
        for other_letter, other_vectors in by_condition.items():
            if other_letter == letter:
                continue
            cross_best.append((vectors @ other_vectors.T).max(axis=1))
        between_mean = np.vstack(cross_best).mean(axis=0)

        w = float(within_best.mean())
        b = float(between_mean.mean())
        per_condition[letter] = (w, b, w / b)
        all_within.extend(within_best.tolist())
        all_between.extend(between_mean.tolist())

    overall_w = float(np.mean(all_within))
    overall_b = float(np.mean(all_between))
    return (overall_w, overall_b, overall_w / overall_b), per_condition


def print_report(overall, per_condition, partial=False):
    scope = "B/E/H cache-only diagnostic" if partial else "canonical 196-record corpus"
    print(f"\nScope: {scope}")
    print("condition  n   within   between   ratio")
    for letter in sorted(per_condition):
        w, b, ratio = per_condition[letter]
        print(f"{letter:>9} {len(CURRENT_TEXTS[letter]):>3}  {w:>7.3f}   {b:>7.3f}   {ratio:>5.2f}x")
    print(f"{'overall':>9} {sum(len(v) for v in CURRENT_TEXTS.values()):>3}  "
          f"{overall[0]:>7.3f}   {overall[1]:>7.3f}   {overall[2]:>5.2f}x")
    if partial:
        print("\nThe cache-only between value ranges over B/E/H, not all eight conditions.")


def assert_revised_values(overall, per_condition):
    np.testing.assert_allclose(overall, REVISED_OVERALL, atol=1e-5)
    for letter, expected in REVISED_VALUES.items():
        np.testing.assert_allclose(per_condition[letter], expected, atol=1e-5)


def run_full():
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        print(f"sentence-transformers is required for full mode: {exc}")
        return 1

    model = SentenceTransformer(MODEL_NAME, revision=MODEL_REVISION)
    by_condition = {}
    for letter, texts in CURRENT_TEXTS.items():
        embeddings = model.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        by_condition[letter] = np.asarray(embeddings, dtype=np.float32)
        print(f"{letter}: {len(texts)} core mechanisms")

    overall, per_condition = calculate(by_condition)
    print_report(overall, per_condition)
    assert_revised_values(overall, per_condition)
    print(f"\nPinned model revision: {MODEL_REVISION}")
    print(f"Model weights SHA-256: {MODEL_WEIGHTS_SHA256}")
    print("Revised values reproduced within 1e-5.")
    return 0


def run_from_cache():
    global CURRENT_TEXTS
    by_condition = {}
    cache_texts = {}
    for letter, directory in TAXONOMY_DIRS.items():
        con = sqlite3.connect(BASE / directory / "taxonomy.db")
        cached = {
            text: np.frombuffer(blob, dtype=np.float32)
            for text, blob in con.execute("SELECT text, embedding FROM embedding_cache")
        }
        con.close()
        texts = CURRENT_TEXTS[letter]
        missing = [text for text in texts if text not in cached]
        if missing:
            raise RuntimeError(f"{letter}: {len(missing)} canonical texts absent from cache")
        by_condition[letter] = normalized([cached[text] for text in texts])
        cache_texts[letter] = texts
        print(f"{letter}: {len(texts)} canonical mechanisms recovered from cache")

    full_texts = CURRENT_TEXTS
    CURRENT_TEXTS = cache_texts
    try:
        print_report(*calculate(by_condition), partial=True)
    finally:
        CURRENT_TEXTS = full_texts
    return 0


CURRENT_TEXTS = canonical_texts()

if __name__ == "__main__":
    counts = {letter: len(texts) for letter, texts in CURRENT_TEXTS.items()}
    if counts != {"A": 25, "B": 23, "C": 25, "D": 25,
                  "E": 25, "F": 25, "G": 25, "H": 23}:
        raise SystemExit(f"unexpected canonical counts: {counts}")
    sys.exit(run_from_cache() if "--from-cache" in sys.argv else run_full())
