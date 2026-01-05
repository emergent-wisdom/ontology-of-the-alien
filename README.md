# The Ontology of the Alien: Escaping the Median Trap

This repository contains the code and data for the experiment **"The Ontology of the Alien: Escaping the Median Trap via Adversarial Ontology Building and Isomorphic Translation"**.

## Overview

Large Language Models asked to "be creative" tend to produce solutions that converge on a small number of archetypes—the **Median Trap**. This project systematically compares eight methods for inducing structural diversity in LLM-generated solutions, demonstrating that adversarial topology and world-building can induce emergent metacognition and genuine novelty.

The experiment focuses on a single hard problem:
> "How do we build a retirement system for people who don't know how much they will earn next month, where 'consistency' is impossible?"

## Conditions

We implemented and compared eight experimental conditions, organized by inspiration source and novelty enforcement mechanism:

| Condition | Inspiration | Novelty Mechanism | Description |
|-----------|-------------|-------------------|-------------|
| **A: Semantic Tabu** | None | Tabu List | Maintains an accumulating list of mechanism-level features to avoid. |
| **B: Solution Taxonomy** | None | Graph | Uses graph-based novelty enforcement where solutions must fill gaps in an evolving ontology. |
| **C: Random Seed** | Seed Word | None | Operationalizes de Bono's lateral thinking (Random Entry). |
| **D: Seed + Tabu** | Seed Word | Tabu List | Combines seed inspiration with mechanism avoidance. |
| **E: Seed + Taxonomy** | Seed Word | Graph | Combines seed inspiration with graph-based novelty enforcement. |
| **F: Strange Worlds** | Alien Physics | None | Constructs coherent alternative physics, solves the problem there, then extracts the mechanism. |
| **G: Worlds + Tabu** | Alien Physics | Tabu List | Adds mechanism avoidance to the extraction phase. |
| **H: Worlds + Taxonomy** | Alien Physics | Graph | Adds graph-based novelty enforcement to the extraction phase. |

## The Studio Model

For the taxonomy conditions (B, E, H), we utilized a dual-agent **"Studio Model"** architecture:

1.  **The Explorer (Ephemeral):** Spawns fresh for each run. Goal: Pure novelty. Proposes solutions.
2.  **The Taxonomist (Persistent):** Maintains the long-term ontology graph. Goal: Coherence. Can Accept, Reject, or Restructure the graph.

This architecture demonstrated emergent behaviors such as **Active Commissioning** (requesting specific research), **Structural Coaching** (teaching the difference between surface and deep novelty), and **Ontological Accommodation** (restructuring categories to fit new concepts).

## Repository Structure

- **`src/`**: Core logic for the taxonomy graph, embedding service, and prompt generation.
- **`agents/`**: Agent definitions (`explorer.md`, `taxonomist.md`) and orchestration scripts.
- **`run_experiment.py`**: Main entry point for running the experiment.
- **`analysis/`**: Scripts for analyzing the resulting solution graphs.
- **Data Directories:**
    - `semantic_tabu/`: Condition A results
    - `taxonomy/`: Condition B results
    - `random_seed/`: Condition C results
    - `seed_tabu/`: Condition D results
    - `taxonomy_seed/`: Condition E results
    - `strange_worlds/`: Condition F results
    - `strange_worlds_tabu/`: Condition G results
    - `taxonomy_worlds/`: Condition H results
    - `worlds/`: Intermediate world-building outputs

## Usage

The system is designed to run with **Claude Opus 4.5**.

To run the experiment, use the `run_experiment.py` script. (Ensure you have the necessary API keys configured).

```bash
python run_experiment.py --condition [A-H]
```

## License

MIT License
