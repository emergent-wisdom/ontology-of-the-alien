# Deterministic analysis

These scripts audit the released artifacts and reproduce the descriptive
statistics in the August 2026 revision. They do not call a generative model.

| Script | Purpose | Network/model requirement |
|---|---|---|
| `analyze_results.py` | Reconciles 200 planned slots, 196 canonical records (125 retained outputs plus 71 curator-accepted graph records), 195 non-empty top-level run solutions, 168 strictly valid run JSON files, and exact-string uniqueness. | Offline; Python standard library |
| `analyze_world_diversity.py` | Audits the 25 world/Solver pairs, named world rules, a transparent post-hoc world grouping, and word-TF-IDF shared-source signatures in C/F/G. | Offline; Python standard library |
| `analyze_topology.py` | Recomputes mechanism counts, roots, maximum depth, branching, and total nodes from the three taxonomy databases. | Offline; Python standard library |
| `analyze_embeddings.py` | Recomputes normalized sentence-embedding similarities over the canonical 196-record corpus. | Full mode requires `sentence-transformers` and the pinned encoder weights; `--from-cache` is an offline B/E/H diagnostic |
| `trace_coding.md` | Defines and records the post-hoc interpretive coding of world-premise relief, Semantic-Tabu history uptake, and graph-control events. | No runtime requirement; the codes are judgments, not automatic measurements |

```bash
python3 analysis/analyze_results.py
python3 analysis/analyze_world_diversity.py
python3 analysis/analyze_topology.py
python3 analysis/analyze_embeddings.py
python3 analysis/analyze_embeddings.py --from-cache
```

## Canonical corpus

Conditions A, C, D, F, and G are read from their run JSON. Conditions B, E,
and H are read from `taxonomy.db`, which is authoritative for accepted graph
records. This mixed-source reconstruction is necessary because B run 12 is
marked accepted but its top-level `solution` object is empty; the corresponding
`Distributed Micro-Retirement Accounting` record exists in the graph database.

Thirty-two taxonomy run files contain malformed JSON in their captured
`reasoning` strings. The analysis does not silently repair those historical
files.

## Embedding definition

The full embedding analysis pins
`sentence-transformers/all-MiniLM-L6-v2` at revision
`1110a243fdf4706b3f48f1d95db1a4f5529b4d41` and L2-normalizes the vectors.
For solution \(i\) in condition \(c\), it computes the closest other solution
within \(c\). For every other condition \(d\), it separately computes the
closest solution in \(d\), then averages those seven maxima. Corpus means are
0.563 within condition and 0.514 between conditions (ratio 1.10).

The persisted database vectors cover only B, E, and H. Consequently,
`--from-cache` is a diagnostic over those three conditions and cannot reproduce
the full eight-condition between-condition statistic. These similarities are
descriptive text properties, not measures of creativity, quality, or external
novelty.
