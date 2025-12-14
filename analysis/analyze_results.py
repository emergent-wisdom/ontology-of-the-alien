#!/usr/bin/env python3
"""
Comprehensive analysis of Strange Worlds experiment results.
Generates tables and statistics for the paper.
"""

import json
from pathlib import Path
from collections import defaultdict

BASE_DIR = Path(__file__).parent.parent

CONDITIONS = {
    "semantic_tabu": ("tabu_*.json", "A"),
    "strange_worlds": ("worlds_*.json", "B"),
    "strange_worlds_tabu": ("worlds_tabu_*.json", "C"),
    "random_seed": ("seed_*.json", "D"),
    "seed_tabu": ("seed_tabu_*.json", "E"),
}

SEEDS = [
    "limelike", "unwilted", "cinerator", "nephropyosis", "fimbrillate",
    "coralline", "unimpatient", "pilaued", "displacement", "theatrical",
    "palouser", "critique", "bromobenzyl", "gnomically", "remilitarize",
    "arcual", "whizgig", "entempest", "chalaco", "paranucleic",
    "phraseman", "desperacy", "pidan", "phosis", "theca"
]

def load_all_solutions():
    """Load all solutions from all conditions."""
    data = {}
    for condition, (pattern, letter) in CONDITIONS.items():
        condition_dir = BASE_DIR / condition
        data[condition] = []
        for f in sorted(condition_dir.glob(pattern)):
            if "bank" not in f.name:
                with open(f) as fp:
                    data[condition].append(json.load(fp))
    return data

def analyze_uniqueness(data):
    """Check label uniqueness across conditions."""
    print("\n" + "="*60)
    print("SOLUTION UNIQUENESS ANALYSIS")
    print("="*60)

    all_labels = []
    labels_by_condition = {}

    for condition, solutions in data.items():
        labels = [s["solution"]["label"] for s in solutions]
        labels_by_condition[condition] = labels
        all_labels.extend(labels)

    unique_labels = set(all_labels)
    print(f"\nTotal solutions: {len(all_labels)}")
    print(f"Unique labels: {len(unique_labels)}")
    print(f"Label overlap: {len(all_labels) - len(unique_labels)} duplicates")

    # Check for cross-condition duplicates
    cross_duplicates = []
    for i, (c1, labels1) in enumerate(labels_by_condition.items()):
        for c2, labels2 in list(labels_by_condition.items())[i+1:]:
            overlap = set(labels1) & set(labels2)
            if overlap:
                cross_duplicates.append((c1, c2, overlap))

    if cross_duplicates:
        print("\nCross-condition duplicates found:")
        for c1, c2, overlap in cross_duplicates:
            print(f"  {c1} ∩ {c2}: {overlap}")
    else:
        print("\n✓ Zero cross-condition label overlap")

    return labels_by_condition

def analyze_cross_seed(data, seeds_to_check=["theatrical", "chalaco", "coralline", "whizgig"]):
    """Compare solutions for the same seed across conditions."""
    print("\n" + "="*60)
    print("CROSS-SEED COMPARISON")
    print("="*60)

    seeded_conditions = ["strange_worlds", "strange_worlds_tabu", "random_seed", "seed_tabu"]

    for seed in seeds_to_check:
        print(f"\n--- Seed: {seed} ---")
        for condition in seeded_conditions:
            for sol in data[condition]:
                if sol.get("seed") == seed:
                    letter = CONDITIONS[condition][1]
                    label = sol["solution"]["label"]
                    mechanism = sol["solution"]["core_mechanism"][:80] + "..."
                    print(f"  [{letter}] {label}")
                    print(f"      {mechanism}")
                    break

def extract_all_labels(data):
    """Print all labels by condition."""
    print("\n" + "="*60)
    print("ALL SOLUTION LABELS BY CONDITION")
    print("="*60)

    for condition, solutions in data.items():
        letter = CONDITIONS[condition][1]
        print(f"\n--- {condition} ({letter}) ---")
        for i, sol in enumerate(solutions, 1):
            print(f"  {i:2}. {sol['solution']['label']}")

def analyze_tabu_progression(data):
    """Show how tabu lists grow."""
    print("\n" + "="*60)
    print("TABU ENGAGEMENT PROGRESSION")
    print("="*60)

    for condition in ["semantic_tabu", "seed_tabu"]:
        print(f"\n--- {condition} ---")
        for sol in data[condition]:
            run = sol["run"]
            reasoning = sol.get("reasoning", "")

            # Count "AVOIDING" mentions
            avoiding_count = reasoning.lower().count("avoiding")

            # Check for explicit list
            has_list = "structural approaches" in reasoning.lower()

            if run in [1, 5, 10, 15, 20, 25]:
                print(f"  Run {run:2}: 'avoiding' mentions: {avoiding_count}, explicit list: {has_list}")

def generate_latex_tables(data):
    """Generate LaTeX tables for the paper."""
    print("\n" + "="*60)
    print("LATEX TABLES")
    print("="*60)

    # Cross-seed comparison table
    print("\n% Cross-seed comparison (theatrical)")
    print("\\begin{table}[h]")
    print("\\centering")
    print("\\begin{tabular}{lll}")
    print("\\toprule")
    print("Condition & Solution & Transfer type \\\\")
    print("\\midrule")

    for seed in ["theatrical"]:
        for condition in ["random_seed", "seed_tabu", "strange_worlds", "strange_worlds_tabu"]:
            for sol in data[condition]:
                if sol.get("seed") == seed:
                    letter = CONDITIONS[condition][1]
                    label = sol["solution"]["label"]
                    # Determine transfer type based on condition
                    if condition == "random_seed":
                        transfer = "Vocabulary"
                    elif condition == "seed_tabu":
                        transfer = "Mechanism"
                    elif condition == "strange_worlds":
                        transfer = "Ontology"
                    else:
                        transfer = "Ontology (constrained)"
                    print(f"{letter} ({condition.replace('_', ' ').title()}) & {label} & {transfer} \\\\")
                    break

    print("\\bottomrule")
    print("\\end{tabular}")
    print("\\caption{Same seed produces different transfer types across methods.}")
    print("\\end{table}")

def main():
    print("Loading all solutions...")
    data = load_all_solutions()

    for condition, solutions in data.items():
        print(f"  {condition}: {len(solutions)} solutions")

    analyze_uniqueness(data)
    analyze_cross_seed(data)
    extract_all_labels(data)
    analyze_tabu_progression(data)
    generate_latex_tables(data)

if __name__ == "__main__":
    main()
