#!/usr/bin/env python3
"""
Reproduce the graph-topology table (tab:graph-stats, Section 3.4) of
"The Ontology of the Alien" directly from the committed taxonomy graphs.

Each taxonomy condition persists its typed knowledge graph in <dir>/taxonomy.db:
    nodes(id, node_type, text, metadata, embedding)
    edges(id, source_id, target_id, edge_type, metadata)
node_type in {SOLUTION, MECHANISM, OUTCOME, PRINCIPLE, CRITICISM, JUSTIFICATION, NOVELTY}
edge_type PARENT_OF connects source = parent -> target = child
(direction verified against src/taxonomy_graph/graph_store.py create_child/set_parent).

Topology metrics are computed over the MECHANISM PARENT_OF forest:
    roots      = MECHANISM nodes with no MECHANISM parent
    max_depth  = edge count of the longest root->leaf path (root = depth 0)
    branching  = (MECHANISM->MECHANISM PARENT_OF edges) / (non-leaf MECHANISM nodes)
    total      = all seven node kinds

The script recomputes the table and asserts the values published in the paper.

Run:  python3 analysis/analyze_topology.py
"""
import sqlite3
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent

# directory -> (paper condition letter, published row)
CONDITIONS = {
    "taxonomy":        ("B", dict(mechanisms=35, roots=10, max_depth=2, branching=1.92, total=167)),
    "taxonomy_seed":   ("E", dict(mechanisms=49, roots=5,  max_depth=3, branching=2.00, total=197)),
    "taxonomy_worlds": ("H", dict(mechanisms=34, roots=10, max_depth=2, branching=2.18, total=169)),
}


def compute(db_path):
    con = sqlite3.connect(db_path)
    node_type = {i: t for i, t in con.execute("SELECT id, node_type FROM nodes")}
    mech = {i for i, t in node_type.items() if t == "MECHANISM"}
    children = {}   # parent -> [children], restricted to MECHANISM -> MECHANISM
    parent = {}     # child -> parent
    for s, t, et in con.execute("SELECT source_id, target_id, edge_type FROM edges"):
        if et == "PARENT_OF" and s in mech and t in mech:
            children.setdefault(s, []).append(t)
            parent[t] = s
    con.close()

    roots = [m for m in mech if m not in parent]

    def longest_path(root):
        best, stack, seen = 0, [(root, 0)], set()
        while stack:
            node, d = stack.pop()
            if node in seen:      # forest is acyclic; guard anyway
                continue
            seen.add(node)
            best = max(best, d)
            for c in children.get(node, []):
                stack.append((c, d + 1))
        return best

    max_depth = max((longest_path(r) for r in roots), default=0)
    non_leaf = [n for n in mech if children.get(n)]
    child_edges = sum(len(v) for v in children.values())
    branching = child_edges / len(non_leaf) if non_leaf else 0.0
    return dict(mechanisms=len(mech), roots=len(roots), max_depth=max_depth,
                branching=branching, total=len(node_type))


def main():
    ok = True
    print(f"{'Cond':<5}{'mechanisms':>11}{'roots':>7}{'max_depth':>10}{'branching':>11}{'total':>7}")
    for d, (letter, pub) in CONDITIONS.items():
        got = compute(BASE / d / "taxonomy.db")
        print(f"{letter:<5}{got['mechanisms']:>11}{got['roots']:>7}"
              f"{got['max_depth']:>10}{got['branching']:>11.2f}{got['total']:>7}")
        for k in ("mechanisms", "roots", "max_depth", "total"):
            if got[k] != pub[k]:
                print(f"   MISMATCH {letter}.{k}: computed {got[k]} != paper {pub[k]}")
                ok = False
        if round(got["branching"], 2) != pub["branching"]:
            print(f"   MISMATCH {letter}.branching: computed {got['branching']:.2f} != paper {pub['branching']}")
            ok = False
    print("\nAll topology values match the paper (tab:graph-stats)." if ok
          else "\nTOPOLOGY MISMATCH -- see above.")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
