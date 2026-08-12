#!/usr/bin/env python3
"""Audit the released many-world artifacts without calling a model.

The script reports exact-file distinctness, extracts the five named world rules from
each world, and measures whether the shared upstream world-and-Solver pair
leaves a lexical signature in the independently compiled F and
Tabu-conditioned G candidates.
It also compares direct random-word condition C with world-mediated condition
F under the same seed.

The TF-IDF calculation is intentionally small and dependency-free. Candidate
text consists of label, design principles, core mechanism, and operation.
Vectors use lower-cased word tokens of length >= 2, smoothed inverse document
frequency, raw term counts, and L2 normalization. Same-seed cosine is compared
with every mismatched-seed cross-condition pair. These are textual diagnostics,
not measures of causal distinctness, creativity, portability, or usefulness.
"""

import hashlib
import json
import math
import re
from collections import Counter
from pathlib import Path


BASE = Path(__file__).resolve().parent.parent
FIELDS = ("label", "design_principles", "core_mechanism", "how_it_works")
TOKEN_RE = re.compile(r"(?u)\b\w\w+\b")
NUMBERED_LAW_RE = re.compile(r"^\*\*\d+\.\s+(.*?)\*\*$")
NAMED_LAW_RE = re.compile(
    r"^(?:###|\*\*)\s*(?:First|Second|Third|Fourth|Fifth) Law:\s*(.*?)(?:\*\*)?$"
)
HEADING_LAW_RE = re.compile(r"^###\s+\d+\.\s+(.*?)$")

# A transparent post-hoc author grouping used only to summarize the breadth of
# the released source worlds. It is not claimed to be a discovered taxonomy.
WORLD_FAMILIES = {
    "material transformation, persistence, or enclosure": {
        "limelike", "unwilted", "cinerator", "nephropyosis", "remilitarize", "pidan", "theca"
    },
    "flow, exchange, or gradients": {
        "pilaued", "displacement", "palouser", "bromobenzyl", "chalaco", "phosis"
    },
    "relational or topological causation": {"fimbrillate", "coralline", "paranucleic"},
    "motion geometry as an existence condition": {"arcual", "whizgig", "entempest"},
    "symbolic, social, or mental states as physical causes": {
        "unimpatient", "theatrical", "critique", "gnomically", "phraseman", "desperacy"
    },
}


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def seed_from_world_path(path):
    return path.parent.name.split("_", 1)[1]


def extract_law_titles(path):
    """Extract the first five numbered/named world rules from one released world."""
    titles = []
    in_law_section = False
    for line in path.read_text().splitlines():
        if line.startswith("## "):
            if in_law_section:
                break
            heading = line[3:].lower()
            if re.search(r"\blaws\b", heading):
                in_law_section = True
            continue
        if not in_law_section:
            continue
        match = HEADING_LAW_RE.match(line) or NUMBERED_LAW_RE.match(line) or NAMED_LAW_RE.match(line)
        if match:
            title = match.group(1).strip()
            titles.append(re.sub(r"^(?:The\s+)?Law of\s+", "", title, flags=re.IGNORECASE))
    return titles


def normalized_title(title):
    return re.sub(r"[^a-z0-9]+", " ", title.lower()).strip()


def load_condition(directory, pattern):
    records = {}
    for path in sorted((BASE / directory).glob(pattern)):
        payload = json.loads(path.read_text())
        records[payload["seed"]] = payload["solution"]
    return records


def candidate_text(record):
    return " ".join(str(record.get(field, "")) for field in FIELDS)


def tfidf_vectors(by_condition):
    references = []
    documents = []
    for condition, records in by_condition.items():
        for seed, record in records.items():
            references.append((condition, seed))
            documents.append(TOKEN_RE.findall(candidate_text(record).lower()))

    document_frequency = Counter()
    for document in documents:
        document_frequency.update(set(document))

    count = len(documents)
    inverse_frequency = {
        token: math.log((1 + count) / (1 + frequency)) + 1
        for token, frequency in document_frequency.items()
    }

    vectors = {}
    for reference, document in zip(references, documents):
        frequencies = Counter(document)
        vector = {
            token: frequency * inverse_frequency[token]
            for token, frequency in frequencies.items()
        }
        norm = math.sqrt(sum(value * value for value in vector.values()))
        vectors[reference] = {token: value / norm for token, value in vector.items()}
    return vectors


def cosine(left, right):
    if len(left) > len(right):
        left, right = right, left
    return sum(value * right.get(token, 0.0) for token, value in left.items())


def paired_signature(left_name, left, right_name, right):
    vectors = tfidf_vectors({left_name: left, right_name: right})
    shared = sorted(set(left) & set(right))
    same = [
        cosine(vectors[(left_name, seed)], vectors[(right_name, seed)])
        for seed in shared
    ]
    mismatched = [
        cosine(vectors[(left_name, left_seed)], vectors[(right_name, right_seed)])
        for left_seed in left
        for right_seed in right
        if left_seed != right_seed
    ]
    same_mean = sum(same) / len(same)
    mismatched_mean = sum(mismatched) / len(mismatched)
    return len(shared), same_mean, mismatched_mean, same_mean / mismatched_mean


def main():
    world_paths = sorted((BASE / "worlds").glob("*/world.txt"))
    solver_paths = sorted((BASE / "worlds").glob("*/solver.txt"))
    world_hashes = {sha256(path) for path in world_paths}
    solver_hashes = {sha256(path) for path in solver_paths}

    laws = []
    for path in world_paths:
        titles = extract_law_titles(path)
        if len(titles) != 5:
            raise SystemExit(f"{path}: expected five named world rules, found {len(titles)}")
        laws.extend(titles)
    normalized_laws = {normalized_title(title) for title in laws}

    print("Released world artifacts")
    print(f"  world files:  {len(world_paths)}; unique hashes: {len(world_hashes)}")
    print(f"  Solver files: {len(solver_paths)}; unique hashes: {len(solver_hashes)}")
    print(f"  world rules:  {len(laws)}; normalized unique titles: {len(normalized_laws)}")

    if (len(world_paths), len(world_hashes), len(solver_paths), len(solver_hashes)) != (25, 25, 25, 25):
        raise SystemExit("unexpected world/Solver artifact counts")
    if (len(laws), len(normalized_laws)) != (125, 123):
        raise SystemExit("unexpected named-law counts")

    covered = set().union(*WORLD_FAMILIES.values())
    observed = {seed_from_world_path(path) for path in world_paths}
    if covered != observed or sum(map(len, WORLD_FAMILIES.values())) != 25:
        raise SystemExit("author-coded world grouping is incomplete or overlapping")

    print("\nPost-hoc author grouping of primary causal premises")
    for family, seeds in WORLD_FAMILIES.items():
        print(f"  {len(seeds):>2}  {family}: {', '.join(sorted(seeds))}")

    direct_seed = load_condition("random_seed", "seed_*.json")
    open_world = load_condition("strange_worlds", "worlds_*.json")
    tabu_world = load_condition("strange_worlds_tabu", "worlds_tabu_*.json")
    for name, records in (("C", direct_seed), ("F", open_world), ("G", tabu_world)):
        if len(records) != 25:
            raise SystemExit(f"condition {name}: expected 25 records, found {len(records)}")

    print("\nWord-TF-IDF shared-source diagnostics")
    for left_name, left, right_name, right in (
        ("F", open_world, "G", tabu_world),
        ("C", direct_seed, "F", open_world),
    ):
        n, same, mismatched, ratio = paired_signature(left_name, left, right_name, right)
        print(
            f"  {left_name}-{right_name}: n={n}; same-seed={same:.3f}; "
            f"mismatched-seed={mismatched:.3f}; ratio={ratio:.2f}x"
        )

    print("\nThese checks establish file, title, and lexical properties only.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
