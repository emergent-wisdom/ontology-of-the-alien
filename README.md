# The Ontology of the Alien: World-Diversity Search and Evolving Solution Ontologies

[![Paper](https://img.shields.io/badge/Paper-PDF-red)](paper/ontology_of_the_alien.pdf)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.21910466.svg)](https://doi.org/10.5281/zenodo.21910466)
[![Code: MIT](https://img.shields.io/badge/Code-MIT-green)](LICENSE)
[![Paper and data: CC BY 4.0](https://img.shields.io/badge/Paper%20%26%20data-CC%20BY%204.0-blue)](LICENSE-DATA)

This repository accompanies the revised paper released on August 15, 2026 and archived at [doi:10.5281/zenodo.21910466](https://doi.org/10.5281/zenodo.21910466). The revision does not introduce a new model or software version: the experimental code and generated candidate corpus are unchanged, and no new generative runs were conducted.

This repository contains two complementary search operators for open-ended problems. Previously released **world-diversity search** changes the premises before solution generation: target-independent Builders construct textual worlds with altered causal rules, purpose-blind Solvers address the same target under each rule set, and compilers translate the resulting mechanisms into a common target-domain schema. “Purpose-blind” means that the Solver knows the target problem but not why its world was constructed or that its answer will later be transferred.

This paper introduces **ontology-governed intervention search**. Complete candidate interventions accumulate in a persistent typed ontology that serves as search-control state: a Taxonomist judges mechanism equivalence, accepts or redirects proposals, revises categories, and returns the changed map to fresh Explorers. Together, the two operators instantiate the fan-out and fold-back kernel of a proposed **expansion-before-optimization** pipeline. World-level coverage control, diversity-preserving selection, and real-world validation remain future work.

The released study used one retirement-design problem across eight workflows. It generated 25 world/Solver pairs, reused each pair across the three counterfactual workflows, and recovered 196 canonical candidate records from 200 planned positions. The graph conditions contain 71 curator-accepted records. These are path-dependent search traces, not 196 independent experimental replicates.

For a quick evidence tour, start with the [25 world/Solver pairs](worlds/), the [trace-coding ledger](analysis/trace_coding.md), and the [offline analysis guide](analysis/README.md).

The earlier world-diversity protocol was published as [Algorithmic Creativity via Strange Worlds](https://doi.org/10.5281/zenodo.17905401) (Westerberg, 2025). The present paper contributes the ontology-governed controller and studies how source-frame displacement and population state interact.

## Study Design

All eight conditions address the same problem:

> “How do we build a retirement system for people who don't know how much they will earn next month, where ‘consistency’ is impossible?”

| Condition | Source frame | Population state |
|---|---|---|
| A: Semantic Tabu | Target alone | Tabu archive |
| B: Solution Taxonomy | Target alone | Curated ontology |
| C: Random Inspiration | Random word | None |
| D: Seed + Tabu | Random word | Tabu archive |
| E: Seed + Taxonomy | Random word | Curated ontology |
| F: Orthogonal | Counterfactual causal world + in-world solve | None |
| G: Orthogonal + Tabu | Counterfactual causal world + in-world solve | Tabu archive |
| H: Orthogonal + Taxonomy | Counterfactual causal world + in-world solve | Curated ontology |

There are 25 planned positions per condition. A, C, D, F, and G contribute 125 retained outputs; the graph databases contain 23, 25, and 23 curator-accepted records for B, E, and H. Together they form the 196-record canonical corpus. Four planned graph positions produced no canonical admission; the traces do not establish why.

## What the Artifacts Show

- All 196 canonical labels and core-mechanism strings are unique under exact-string comparison. This does not establish functional or external novelty.
- A corrected, normalized sentence-embedding analysis gives mean best-match similarity 0.563 within condition and 0.514 across conditions (ratio 1.10).
- The runner produced 25 nonidentical world files and 25 nonidentical Solver files. Their 125 named world rules have 123 distinct normalized titles; neither result establishes semantic or causal independence.
- An unblinded, post-hoc [trace census](analysis/trace_coding.md) coded target-bottleneck relief as clear in 17 world branches and partial in eight. All 25 Solvers added multi-component downstream architecture; on a separate final-outcome-fiat check, 14 branches passed, eight were borderline, and three failed.
- All 72 history-bearing Tabu calls restated earlier mechanisms and declared exclusions. Semantic avoidance itself was not independently evaluated.
- Across traces for 75 planned graph positions, seven complete rejection–redirection–mechanism-change chains ended in admission. Forty of 46 non-leaf category-title stems appeared in a later Explorer capture. These observations document persistent search state and selective redirection, not a causal improvement in novelty, quality, or usefulness.
- The three final curator-authored graphs differ in mechanism count, roots, depth, and branching.
- F and G candidates compiled from the same upstream world-and-Solver pair were 2.83 times more similar under a transparent word-TF-IDF diagnostic than mismatched-source pairs. This is a shared-source lexical signature, not a creativity or utility measure.
- Solution quality, usefulness, cross-domain generalization, and real-world outcomes were not evaluated.

## Browse the Release

| Artifact | Contents |
|---|---|
| [paper/](paper/) | LaTeX source and compiled paper |
| [worlds/](worlds/) | 25 source-world texts and their 25 in-world Solver outputs |
| [analysis/](analysis/) | Audit scripts, analysis notes, and the trace-coding ledger |
| [src/taxonomy_graph/](src/taxonomy_graph/) | Typed graph store and embedding service |
| [agents/](agents/) | Explorer and Taxonomist prompts and historical orchestration scripts |
| [run_experiment.py](run_experiment.py) | Historical eight-workflow runner |
| [seeds.json](seeds.json) | Reference copy of the 25 seed words; the runner hard-codes the same list |
| [schema.json](schema.json) | Historical pre-run schema sketch; not authoritative for the stored records |

Each condition directory contains 25 run-capture JSON files:

| Condition | Released directory | Additional persistent state |
|---|---|---|
| A | [semantic_tabu/](semantic_tabu/) | `bank.json` |
| B | [taxonomy/](taxonomy/) | `taxonomy.db` |
| C | [random_seed/](random_seed/) | — |
| D | [seed_tabu/](seed_tabu/) | `bank.json` |
| E | [taxonomy_seed/](taxonomy_seed/) | `taxonomy.db` |
| F | [strange_worlds/](strange_worlds/) | — |
| G | [strange_worlds_tabu/](strange_worlds_tabu/) | `bank.json` |
| H | [taxonomy_worlds/](taxonomy_worlds/) | `taxonomy.db` |

For B, E, and H, the databases are authoritative for curator-accepted candidates. The JSON files are bounded run captures rather than immutable transcripts: 32 graph-condition captures contain malformed model-generated JSON inside their `reasoning` fields, and one accepted B candidate appears only in the database. The [analysis guide](analysis/README.md) explains the canonical reconstruction.

## Reproduce the Released Analyses

The principal artifact checks are offline, use only the Python standard library, and make no generative-model calls:

```bash
python3 analysis/analyze_results.py
python3 analysis/analyze_world_diversity.py
python3 analysis/analyze_topology.py
```

The full sentence-embedding analysis uses the encoder revision pinned in the script:

```bash
python3 -m pip install -r requirements.txt
python3 analysis/analyze_embeddings.py
```

The full embedding command may download the pinned encoder weights. `python3 analysis/analyze_embeddings.py --from-cache` is offline, but covers only B, E, and H and therefore does not reproduce the reported eight-condition statistic.

## Historical Runner

The committed release already contains all 200 run captures, so `python3 run_experiment.py` reports the experiment complete and exits. The runner is preserved as historical research code, not as an exact-reproduction command. Direct workflows use the mutable model alias `opus` through `claude-code-sdk`; graph workflows invoke the locally installed Claude Code CLI without an explicit model flag. The original resolved model checkpoint, CLI and SDK versions, and decoding configuration cannot be reconstructed exactly.

A new run additionally requires Anthropic authentication, the Claude Code CLI, `claude-code-sdk`, `tmux`, `script`, and macOS `sandbox-exec`; see [requirements-generation.txt](requirements-generation.txt). The graph path invokes the CLI with `--dangerously-skip-permissions` inside the repository sandbox, so inspect the runner and sandbox policy before use.

The runner has no condition or output-root flag. Do not delete selected captures and resume inside the released directories: retained final `bank.json` and `taxonomy.db` state could condition an earlier missing position on later search history. Generate new data only from isolated, clean state after adapting the output paths. Any resulting corpus is a new experiment rather than a reproduction of this release.

## Standalone World-Diversity Tool

The **Orthogonal Insight Engine** is available separately at [emergent-wisdom/orthogonal-insight-engine](https://github.com/emergent-wisdom/orthogonal-insight-engine).

## Licensing

The source code and operational prompts are licensed under the [MIT License](LICENSE). The paper, repository documentation, released datasets, and generated artifacts are licensed under [Creative Commons Attribution 4.0 International](LICENSE-DATA). The [license map](LICENSES.md) defines the path-level boundary; [third-party notices](THIRD_PARTY_NOTICES.md) preserve the separate license for the vendored LaTeX style.
