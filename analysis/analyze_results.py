#!/usr/bin/env python3
"""Audit the released result corpus without running a model.

The taxonomy databases are canonical for B, E, and H because asynchronous
capture left one accepted B solution out of the top-level run JSON.  This
script reports planned slots, canonical records, non-empty top-level solutions,
strictly parseable run files, and exact-string uniqueness.  It deliberately
does not infer creativity, quality, or a transfer type from condition labels.
"""

import json
import re
import sqlite3
from pathlib import Path


BASE = Path(__file__).resolve().parent.parent
CONDITIONS = [
    ("A", "Semantic Tabu", "semantic_tabu", "tabu_*.json", False),
    ("B", "Graph", "taxonomy", "taxonomy_*.json", True),
    ("C", "Random seed", "random_seed", "seed_*.json", False),
    ("D", "Seed + Tabu", "seed_tabu", "seed_tabu_*.json", False),
    ("E", "Seed + graph", "taxonomy_seed", "taxonomy_seed_*.json", True),
    ("F", "Orthogonal", "strange_worlds", "worlds_*.json", False),
    ("G", "Orthogonal + Tabu", "strange_worlds_tabu", "worlds_tabu_*.json", False),
    ("H", "Orthogonal + graph", "taxonomy_worlds", "taxonomy_worlds_*.json", True),
]


def run_files(directory, pattern):
    return sorted(path for path in (BASE / directory).glob(pattern) if "bank" not in path.name)


def strict_payloads(paths):
    payloads = []
    for path in paths:
        try:
            payloads.append((path, json.loads(path.read_text())))
        except json.JSONDecodeError:
            pass
    return payloads


def has_nonempty_top_level_solution(path):
    """Detect the serialized top-level solution even when reasoning broke JSON."""
    raw = path.read_text(errors="replace")
    return bool(re.search(r'(?m)^  "solution": \{\s*\n\s*"label"\s*:', raw))


def graph_solutions(directory):
    con = sqlite3.connect(BASE / directory / "taxonomy.db")
    rows = con.execute(
        "SELECT metadata FROM nodes WHERE node_type = 'SOLUTION' ORDER BY rowid"
    ).fetchall()
    con.close()
    return [json.loads(metadata)["full_solution"] for (metadata,) in rows]


def canonical_solutions(directory, pattern, taxonomy):
    if taxonomy:
        return graph_solutions(directory)
    result = []
    for _, payload in strict_payloads(run_files(directory, pattern)):
        solution = payload.get("solution") or {}
        if solution:
            result.append(solution)
    return result


def inspect_condition(letter, name, directory, pattern, taxonomy):
    paths = run_files(directory, pattern)
    valid = strict_payloads(paths)
    nonempty = sum(has_nonempty_top_level_solution(path) for path in paths)
    solutions = canonical_solutions(directory, pattern, taxonomy)
    return {
        "letter": letter,
        "name": name,
        "slots": len(paths),
        "canonical": len(solutions),
        "top_level": nonempty,
        "strict": len(valid),
        "solutions": solutions,
    }


def same_seed(rows, seed="theatrical"):
    print(f"\nSame released seed ({seed!r}); labels only")
    for row in rows:
        if row["letter"] not in "CDEFGH":
            continue
        _, _, directory, pattern, _ = next(c for c in CONDITIONS if c[0] == row["letter"])
        match = None
        for _, payload in strict_payloads(run_files(directory, pattern)):
            if payload.get("seed") == seed and payload.get("solution"):
                match = payload["solution"]
                break
        label = match.get("label") if match else "[not recoverable from strict run JSON]"
        print(f"  {row['letter']}: {label}")


def main():
    rows = [inspect_condition(*condition) for condition in CONDITIONS]

    print("Released artifact reconciliation")
    print("condition  slots  canonical  top-level  strict JSON")
    for row in rows:
        print(
            f"{row['letter']:>9} {row['slots']:>6} {row['canonical']:>9} "
            f"{row['top_level']:>10} {row['strict']:>12}"
        )
    totals = tuple(sum(row[key] for row in rows) for key in ("slots", "canonical", "top_level", "strict"))
    print(f"{'total':>9} {totals[0]:>6} {totals[1]:>9} {totals[2]:>10} {totals[3]:>12}")

    expected = (200, 196, 195, 168)
    if totals != expected:
        raise SystemExit(f"unexpected reconciliation {totals}; expected {expected}")

    all_solutions = [solution for row in rows for solution in row["solutions"]]
    labels = [solution["label"].strip() for solution in all_solutions]
    mechanisms = [solution["core_mechanism"].strip() for solution in all_solutions]
    print("\nExact-string checks")
    print(f"  labels:          {len(set(labels))}/{len(labels)} unique")
    print(f"  core mechanisms: {len(set(mechanisms))}/{len(mechanisms)} unique")
    if len(set(labels)) != 196 or len(set(mechanisms)) != 196:
        raise SystemExit("canonical exact-string uniqueness changed")

    same_seed(rows)
    print("\nThese checks establish artifact counts and string properties only.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
