# The Ontology of the Alien: Escaping the Median Trap in LLM Ideation

**Paper:** [`paper/ontology_of_the_alien.pdf`](paper/ontology_of_the_alien.pdf)

Large Language Models asked to "be creative" produce solutions that converge on a small number of archetypes — the **Median Trap**. This repository contains the experiment code and full dataset (196 solutions across 8 conditions) for a systematic comparison of methods that escape it.

We test three novel architectures against baselines:
- **Semantic Tabu** — accumulating constraints that block previously used mechanisms
- **Solution Taxonomy (Studio Model)** — a dual-agent system where an Explorer proposes and a Taxonomist curates an evolving ontology graph
- **Orthogonal Insight Protocol** — constructing coherent alternative physics, solving the problem within them, and extracting mechanisms back to reality

> **Prior work:** This paper extends [Algorithmic Creativity via Strange Worlds](https://doi.org/10.5281/zenodo.17905401) (Westerberg, 2025), which introduced the Orthogonal Insight Protocol and tested it against a single baseline.

## The Problem

All eight conditions tackle the same hard problem:

> "How do we build a retirement system for people who don't know how much they will earn next month, where 'consistency' is impossible?"

## Conditions

| Condition | Inspiration | Novelty Mechanism |
|-----------|-------------|-------------------|
| A: Semantic Tabu | None | Tabu list |
| B: Solution Taxonomy | None | Graph |
| C: Random Seed | Seed word | None |
| D: Seed + Tabu | Seed word | Tabu list |
| E: Seed + Taxonomy | Seed word | Graph |
| F: Orthogonal | Alien physics | None |
| G: Orthogonal + Tabu | Alien physics | Tabu list |
| H: Orthogonal + Taxonomy | Alien physics | Graph |

25 runs per condition. Conditions B and H had 23 solutions accepted into their taxonomy graphs (2 rejected each as structurally redundant), yielding 196 distinct solutions.

## Key Findings

- The **Studio Model** (Conditions B, E, H) exhibited emergent metacognition: active commissioning of research, structural coaching, and ontological accommodation (restructuring categories when data defied classification).
- The system independently derived advanced economic concepts including **antifragility**, **metric dissolution**, and **flow rights** as alternatives to accumulation.
- Different architectures produce different **solution space topologies**: Tabu forces vertical depth, Seeds create lateral branching, and Orthogonal Insight extracts epistemological stances.

## Repository Structure

```
paper/                  LaTeX source and compiled PDF
src/taxonomy_graph/     Graph data structure and embedding service
agents/                 Agent prompts (explorer.md, taxonomist.md) and orchestration
run_experiment.py       Main entry point
analysis/               Result analysis scripts
seeds.json              25 seed words used for Conditions C-H
schema.json             Solution output schema
```

**Data directories** (25 JSON files each):

| Directory | Condition |
|-----------|-----------|
| `semantic_tabu/` | A |
| `taxonomy/` | B |
| `random_seed/` | C |
| `seed_tabu/` | D |
| `taxonomy_seed/` | E |
| `strange_worlds/` | F |
| `strange_worlds_tabu/` | G |
| `taxonomy_worlds/` | H |

Each JSON file contains the full agent output (world-building text, solver reasoning, extracted solution) for reproducibility.

## Usage

Requires **Claude Opus 4.5** and a valid Anthropic API key.

```bash
pip install -r requirements.txt
python run_experiment.py --condition [A-H]
```

## License

MIT License
