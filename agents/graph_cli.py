#!/usr/bin/env python3
"""
Graph CLI for the Taxonomist agent.

Usage:
    python graph_cli.py state                    # Show current graph state
    python graph_cli.py tree <type>              # Show hierarchy tree (MECHANISM, OUTCOME, etc.)
    python graph_cli.py add <json_file>          # Add a solution from JSON file
    python graph_cli.py add-inline '<json>'      # Add a solution from inline JSON
    python graph_cli.py restructure <json_file>  # Execute restructure transaction
    python graph_cli.py merge <keep_id> <remove_id>       # Merge two nodes
    python graph_cli.py create-child <parent_id> "text"   # Create child node under parent
    python graph_cli.py set-parent <child_id> <parent_id> # Set node's parent
"""

import sys
import os
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.taxonomy_graph.graph_store import GraphStore, NodeType

DEFAULT_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        'taxonomy', 'taxonomy.db')

# Allow override via environment variable
DB_PATH = os.environ.get('TAXONOMY_DB', DEFAULT_DB_PATH)

def get_store():
    return GraphStore(DB_PATH)

def cmd_state():
    """Show current graph state."""
    store = get_store()
    print(store.get_graph_state_for_prompt())
    print()
    stats = store.stats()
    print(f"Total: {stats['solutions']} solutions, {stats['nodes']} nodes, {stats['edges']} edges")

def cmd_add(solution_json, field_mappings=None):
    """Add a solution."""
    store = get_store()
    result = store.add_solution(solution_json, field_mappings)
    if result.get('success'):
        print(f"SUCCESS: Added solution {result['solution_id']}")
        print(f"  Created: {list(result.get('created', {}).keys())}")
        print(f"  Linked: {list(result.get('linked', {}).keys())}")
    else:
        print(f"ERROR: {result.get('error')}")
    return result

def cmd_restructure(operations):
    """Execute restructure transaction."""
    store = get_store()
    result = store.execute_transaction(operations)
    if result.get('success'):
        print(f"SUCCESS: Restructured graph")
        print(f"  New node IDs: {result.get('temp_id_map', {})}")
    else:
        print(f"ERROR: {result.get('error')}")
    return result

def cmd_merge(keep_id, remove_id):
    """Merge two nodes."""
    store = get_store()
    success = store.merge_nodes(keep_id, remove_id)
    if success:
        print(f"SUCCESS: Merged {remove_id} into {keep_id}")
    else:
        print(f"ERROR: Could not merge nodes")
    return success

def cmd_tree(node_type_str):
    """Show hierarchy tree for a node type."""
    store = get_store()
    try:
        node_type = NodeType(node_type_str.upper())
    except ValueError:
        print(f"ERROR: Unknown node type '{node_type_str}'")
        print(f"Valid types: {[t.value for t in NodeType]}")
        return

    tree = store.get_hierarchy_tree(node_type)
    print(f"\n{node_type.name} HIERARCHY:")
    print(tree if tree else "  (no nodes)")
    print()

def cmd_create_child(parent_id, text):
    """Create a child node under a parent."""
    store = get_store()
    # Allow short IDs - find full ID
    full_parent_id = resolve_node_id(store, parent_id)
    if not full_parent_id:
        print(f"ERROR: Node not found: {parent_id}")
        return None

    try:
        child_id = store.create_child(full_parent_id, text)
        print(f"SUCCESS: Created child {child_id[:8]} under parent {full_parent_id[:8]}")
        return child_id
    except ValueError as e:
        print(f"ERROR: {e}")
        return None

def cmd_set_parent(child_id, parent_id):
    """Set or change a node's parent."""
    store = get_store()
    full_child_id = resolve_node_id(store, child_id)
    full_parent_id = resolve_node_id(store, parent_id)

    if not full_child_id:
        print(f"ERROR: Child node not found: {child_id}")
        return False
    if not full_parent_id:
        print(f"ERROR: Parent node not found: {parent_id}")
        return False

    try:
        store.set_parent(full_child_id, full_parent_id)
        print(f"SUCCESS: Set {full_child_id[:8]} as child of {full_parent_id[:8]}")
        return True
    except ValueError as e:
        print(f"ERROR: {e}")
        return False

def resolve_node_id(store, short_id):
    """Resolve a short ID (first 8 chars) to full UUID."""
    for node_id in store.graph.nodes():
        if node_id.startswith(short_id) or node_id == short_id:
            return node_id
    return None

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == 'state':
        cmd_state()

    elif cmd == 'add':
        if len(sys.argv) < 3:
            print("Usage: graph_cli.py add <json_file>")
            sys.exit(1)
        with open(sys.argv[2]) as f:
            solution = json.load(f)
        cmd_add(solution)

    elif cmd == 'add-inline':
        if len(sys.argv) < 3:
            print("Usage: graph_cli.py add-inline '<json>'")
            sys.exit(1)
        solution = json.loads(sys.argv[2])
        cmd_add(solution)

    elif cmd == 'restructure':
        if len(sys.argv) < 3:
            print("Usage: graph_cli.py restructure <json_file>")
            sys.exit(1)
        with open(sys.argv[2]) as f:
            ops = json.load(f)
        cmd_restructure(ops)

    elif cmd == 'merge':
        if len(sys.argv) < 4:
            print("Usage: graph_cli.py merge <keep_id> <remove_id>")
            sys.exit(1)
        cmd_merge(sys.argv[2], sys.argv[3])

    elif cmd == 'tree':
        if len(sys.argv) < 3:
            print("Usage: graph_cli.py tree <type>")
            print("Types: MECHANISM, OUTCOME, PRINCIPLE, CRITICISM, JUSTIFICATION, NOVELTY")
            sys.exit(1)
        cmd_tree(sys.argv[2])

    elif cmd == 'create-child':
        if len(sys.argv) < 4:
            print("Usage: graph_cli.py create-child <parent_id> \"text\"")
            sys.exit(1)
        cmd_create_child(sys.argv[2], sys.argv[3])

    elif cmd == 'set-parent':
        if len(sys.argv) < 4:
            print("Usage: graph_cli.py set-parent <child_id> <parent_id>")
            sys.exit(1)
        cmd_set_parent(sys.argv[2], sys.argv[3])

    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)
        sys.exit(1)

if __name__ == '__main__':
    main()
