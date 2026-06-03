# Analysis scripts

Reproducers for the quantitative claims in `paper/ontology_of_the_alien.tex`.

| Script | Reproduces | Runs offline? |
|---|---|---|
| `analyze_topology.py` | The graph-topology table (§3.4, `tab:graph-stats`): mechanisms, roots, max depth, branching, total nodes — computed from the `nodes`/`edges` tables in each `<condition>/taxonomy.db`. Self-asserts the published values. | Yes |
| `analyze_embeddings.py` | The sentence-embedding distinctness analysis (§3.1): per-mechanism best-match cosine within vs between conditions with `all-MiniLM-L6-v2`. | Full mode needs the model; `--from-cache` runs offline |
| `analyze_results.py` | Original label-uniqueness / tabu-progression tables. | Yes |

```bash
python3 analysis/analyze_topology.py                 # prints + asserts the topology table
python3 analysis/analyze_embeddings.py               # full §3.1 (needs sentence-transformers + model)
python3 analysis/analyze_embeddings.py --from-cache  # offline partial check, taxonomy conditions only
```

**Reproducibility caveat for §3.1.** Only the three taxonomy conditions (B, E, H)
persist embeddings on disk (in `taxonomy.db`). The five non-taxonomy conditions
(A, C, D, F, G) do not, so the full eight-condition *between*-similarity (0.512)
and the per-condition ratios require re-running `all-MiniLM-L6-v2` over every
`solution.core_mechanism` (full mode). The offline `--from-cache` check recovers
the per-solution core mechanisms for B/E/H from the cached vectors and reproduces
the *within*-condition magnitude (0.561 vs the paper's 0.566); its
between-condition figure is restricted to {B, E, H} and is **not** comparable to
the paper's full-universe 0.512.
