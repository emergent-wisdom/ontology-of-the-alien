#!/usr/bin/env python3
"""CLI for SolutionTaxonomy graph operations."""

import argparse
import json
import sys
from pathlib import Path

from .graph_store import GraphStore, NodeType


def cmd_add_solution(args):
    """Add a solution from JSON file."""
    store = GraphStore(args.db)

    if args.file == '-':
        solution = json.load(sys.stdin)
    else:
        with open(args.file) as f:
            solution = json.load(f)

    if 'solution' in solution:
        solution = solution['solution']

    result = store.add_solution(solution)

    print(f"Added solution: {result['solution_id'][:8]}...")
    print(f"  Label: {solution.get('label', 'unnamed')}")

    mech = result['mechanism']
    if mech['id']:
        if mech.get('is_new'):
            print(f"  Mechanism: NEW - {mech['id'][:8]}...")
        else:
            print(f"  Mechanism: LINKED to existing (sim={mech.get('similarity', 0):.2f})")
            print(f"    Existing: {mech.get('existing_text', '')[:60]}...")

    new_outcomes = sum(1 for o in result['outcomes'] if o['is_new'])
    linked_outcomes = len(result['outcomes']) - new_outcomes
    print(f"  Outcomes: {new_outcomes} new, {linked_outcomes} linked to existing")


def cmd_stats(args):
    """Show graph statistics."""
    store = GraphStore(args.db)
    stats = store.stats()

    print("Graph Statistics:")
    print(f"  Total nodes: {stats['nodes']}")
    print(f"  Total edges: {stats['edges']}")
    print(f"  Solutions:   {stats['solutions']}")
    print(f"  Mechanisms:  {stats['mechanisms']}")
    print(f"  Outcomes:    {stats['outcomes']}")
    print(f"  Signals:     {stats['signals']}")


def cmd_gaps(args):
    """Find unexplored regions in the solution space."""
    store = GraphStore(args.db)
    gaps = store.find_gaps()

    print(f"=== Gap Analysis ({gaps['summary']['total_solutions']} solutions) ===\n")

    print(f"Underused Mechanisms ({len(gaps['underused_mechanisms'])}):")
    for gap in gaps['underused_mechanisms'][:args.limit]:
        print(f"  [{gap['solution_count']} solutions] {gap['text'][:70]}...")

    print(f"\nOrphan Outcomes ({len(gaps['orphan_outcomes'])}):")
    for gap in gaps['orphan_outcomes'][:args.limit]:
        print(f"  {gap['text'][:70]}...")

    print(f"\nUnseen Mechanism-Outcome Combos ({len(gaps['unseen_combos'])}):")
    for combo in gaps['unseen_combos'][:args.limit]:
        print(f"  '{combo['mechanism_text'][:35]}...' + '{combo['outcome_text'][:35]}...'")


def cmd_find_similar(args):
    """Find nodes similar to query text."""
    store = GraphStore(args.db)

    node_type = NodeType(args.type.upper())
    query_embedding = store.embedding_service.get_embedding(args.query)

    candidates = []
    for node_id, data in store.get_nodes_by_type(node_type):
        if data.get('embedding') is not None:
            candidates.append((node_id, data['embedding']))

    results = store.embedding_service.find_similar(
        query_embedding, candidates, threshold=args.threshold, top_k=args.limit
    )

    print(f"Similar {args.type}s to: '{args.query[:50]}...'")
    print(f"(threshold={args.threshold})\n")

    if not results:
        print("No similar nodes found above threshold.")
        return

    for node_id, sim in results:
        text = store.graph.nodes[node_id]['text']
        count = store.get_solution_count_for_node(node_id)
        print(f"  [{sim:.3f}] ({count} solutions) {text[:70]}...")


def cmd_check_novelty(args):
    """Check if a solution is novel before adding."""
    store = GraphStore(args.db)

    if args.file == '-':
        solution = json.load(sys.stdin)
    else:
        with open(args.file) as f:
            solution = json.load(f)

    if 'solution' in solution:
        solution = solution['solution']

    result = store.check_novelty(solution)

    print(f"Novelty Check for: {solution.get('label', 'unnamed')}")
    print(f"Is Novel: {result['is_novel']}\n")

    if result['mechanism_overlap']:
        overlap = result['mechanism_overlap']
        print(f"Mechanism Overlap ({overlap['similarity']:.2%} similar):")
        print(f"  New:      {solution.get('core_mechanism', '')[:60]}...")
        print(f"  Existing: {overlap['existing_text'][:60]}...")

    if result['outcome_overlap']:
        print(f"\nOutcome Overlaps:")
        for overlap in result['outcome_overlap']:
            print(f"  [{overlap['similarity']:.2%}] {overlap['new_text'][:40]}...")
            print(f"           -> {overlap['existing_text'][:40]}...")

    if result['suggestions']:
        print("\nSuggestions for morphing:")
        for sug in result['suggestions']:
            print(f"  - {sug}")


def cmd_prompt_state(args):
    """Generate graph state text for LLM prompts."""
    store = GraphStore(args.db)
    print(store.get_graph_state_for_prompt())


def cmd_list_nodes(args):
    """List all nodes of a type."""
    store = GraphStore(args.db)
    node_type = NodeType(args.type.upper())

    nodes = store.get_nodes_by_type(node_type)
    print(f"{args.type.upper()} nodes ({len(nodes)}):\n")

    for node_id, data in nodes[:args.limit]:
        count = store.get_solution_count_for_node(node_id)
        print(f"  [{node_id[:8]}] ({count} sols) {data['text'][:60]}...")


def cmd_merge(args):
    """Merge two nodes."""
    store = GraphStore(args.db)

    keep_text = store.graph.nodes.get(args.keep, {}).get('text', '')[:40]
    remove_text = store.graph.nodes.get(args.remove, {}).get('text', '')[:40]

    print(f"Merging:")
    print(f"  Keep:   [{args.keep[:8]}] {keep_text}...")
    print(f"  Remove: [{args.remove[:8]}] {remove_text}...")

    success = store.merge_nodes(args.keep, args.remove)
    if success:
        print("Merge successful.")
    else:
        print("Merge failed - check node IDs.")


def cmd_import_batch(args):
    """Import multiple solutions from a directory."""
    store = GraphStore(args.db)

    path = Path(args.path)
    if path.is_file():
        files = [path]
    else:
        files = sorted(path.glob('*.json'))

    added = 0
    skipped = 0

    for f in files:
        try:
            with open(f) as fh:
                data = json.load(fh)

            if 'solution' in data:
                solution = data['solution']
            else:
                solution = data

            if not solution.get('label'):
                skipped += 1
                continue

            novelty = store.check_novelty(solution)
            if not novelty['is_novel'] and not args.force:
                print(f"SKIP (not novel): {f.name} - {solution.get('label', '')[:40]}")
                skipped += 1
                continue

            result = store.add_solution(solution)
            new_flag = "NEW" if result['mechanism'].get('is_new') else "LINK"
            print(f"ADD [{new_flag}]: {f.name} - {solution.get('label', '')[:40]}")
            added += 1

        except Exception as e:
            print(f"ERROR: {f.name} - {e}")
            skipped += 1

    print(f"\nImported {added} solutions, skipped {skipped}")


def main():
    parser = argparse.ArgumentParser(description='SolutionTaxonomy Graph CLI')
    parser.add_argument('--db', default='taxonomy.db', help='Database path')
    subparsers = parser.add_subparsers(dest='command', required=True)

    p_add = subparsers.add_parser('add', help='Add a solution from JSON')
    p_add.add_argument('file', help='JSON file path (or - for stdin)')
    p_add.set_defaults(func=cmd_add_solution)

    p_stats = subparsers.add_parser('stats', help='Show graph statistics')
    p_stats.set_defaults(func=cmd_stats)

    p_gaps = subparsers.add_parser('gaps', help='Find unexplored gaps')
    p_gaps.add_argument('--limit', type=int, default=5, help='Max items per category')
    p_gaps.set_defaults(func=cmd_gaps)

    p_similar = subparsers.add_parser('find-similar', help='Find similar nodes')
    p_similar.add_argument('type', choices=['mechanism', 'outcome', 'signal'])
    p_similar.add_argument('query', help='Text to search for')
    p_similar.add_argument('--threshold', type=float, default=0.7)
    p_similar.add_argument('--limit', type=int, default=5)
    p_similar.set_defaults(func=cmd_find_similar)

    p_check = subparsers.add_parser('check', help='Check solution novelty')
    p_check.add_argument('file', help='JSON file path (or - for stdin)')
    p_check.set_defaults(func=cmd_check_novelty)

    p_prompt = subparsers.add_parser('prompt-state', help='Get graph state for LLM prompt')
    p_prompt.set_defaults(func=cmd_prompt_state)

    p_list = subparsers.add_parser('list', help='List nodes of a type')
    p_list.add_argument('type', choices=['solution', 'mechanism', 'outcome', 'signal'])
    p_list.add_argument('--limit', type=int, default=20)
    p_list.set_defaults(func=cmd_list_nodes)

    p_merge = subparsers.add_parser('merge', help='Merge two nodes')
    p_merge.add_argument('keep', help='Node ID to keep')
    p_merge.add_argument('remove', help='Node ID to remove')
    p_merge.set_defaults(func=cmd_merge)

    p_import = subparsers.add_parser('import', help='Batch import solutions')
    p_import.add_argument('path', help='Directory or file path')
    p_import.add_argument('--force', action='store_true', help='Import even if not novel')
    p_import.set_defaults(func=cmd_import_batch)

    args = parser.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
