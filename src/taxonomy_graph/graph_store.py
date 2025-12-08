"""Graph store for SolutionTaxonomy using SQLite + NetworkX."""

import sqlite3
import json
import uuid
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum

import networkx as nx

from .embedding_service import EmbeddingService


class NodeType(str, Enum):
    SOLUTION = 'SOLUTION'
    MECHANISM = 'MECHANISM'         # core_mechanism
    OUTCOME = 'OUTCOME'             # long_term_vision
    PRINCIPLE = 'PRINCIPLE'         # design_principles
    CRITICISM = 'CRITICISM'         # why_it_fails
    JUSTIFICATION = 'JUSTIFICATION' # why_it_works
    NOVELTY = 'NOVELTY'             # what_is_new


class EdgeType(str, Enum):
    USES_MECHANISM = 'USES_MECHANISM'
    PRODUCES_OUTCOME = 'PRODUCES_OUTCOME'
    FOLLOWS_PRINCIPLE = 'FOLLOWS_PRINCIPLE'
    HAS_CRITICISM = 'HAS_CRITICISM'
    HAS_JUSTIFICATION = 'HAS_JUSTIFICATION'
    CLAIMS_NOVELTY = 'CLAIMS_NOVELTY'
    TRIGGERED_BY = 'TRIGGERED_BY'
    AVOIDS = 'AVOIDS'
    ENABLES = 'ENABLES'
    SIMILAR_TO = 'SIMILAR_TO'
    # Hierarchy edges (parent -> child)
    PARENT_OF = 'PARENT_OF'


@dataclass
class Node:
    id: str
    node_type: NodeType
    text: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[np.ndarray] = None


@dataclass
class Edge:
    id: str
    source_id: str
    target_id: str
    edge_type: EdgeType
    metadata: Dict[str, Any] = field(default_factory=dict)


class GraphStore:
    """Persistent graph store with semantic search capabilities."""

    SIMILARITY_THRESHOLD = 0.75  # For auto-linking (novelty rejection uses 0.92)

    def __init__(self, db_path: str = 'taxonomy.db'):
        self.db_path = db_path
        self.embedding_service = EmbeddingService(db_path)
        self.graph = nx.DiGraph()
        self._init_tables()
        self._load_graph()

    def _init_tables(self):
        """Create database tables if they don't exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS nodes (
                id TEXT PRIMARY KEY,
                node_type TEXT NOT NULL,
                text TEXT NOT NULL,
                metadata TEXT DEFAULT '{}',
                embedding BLOB
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS edges (
                id TEXT PRIMARY KEY,
                source_id TEXT NOT NULL,
                target_id TEXT NOT NULL,
                edge_type TEXT NOT NULL,
                metadata TEXT DEFAULT '{}',
                FOREIGN KEY (source_id) REFERENCES nodes(id),
                FOREIGN KEY (target_id) REFERENCES nodes(id)
            )
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_nodes_type ON nodes(node_type)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_edges_source ON edges(source_id)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_edges_target ON edges(target_id)
        ''')

        conn.commit()
        conn.close()

    def _load_graph(self):
        """Load graph from database into memory."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT id, node_type, text, metadata, embedding FROM nodes')
        for row in cursor.fetchall():
            node_id, node_type, text, metadata_json, embedding_blob = row
            embedding = np.frombuffer(embedding_blob, dtype=np.float32) if embedding_blob else None
            self.graph.add_node(
                node_id,
                node_type=NodeType(node_type),
                text=text,
                metadata=json.loads(metadata_json),
                embedding=embedding
            )

        cursor.execute('SELECT id, source_id, target_id, edge_type, metadata FROM edges')
        for row in cursor.fetchall():
            edge_id, source_id, target_id, edge_type, metadata_json = row
            self.graph.add_edge(
                source_id,
                target_id,
                id=edge_id,
                edge_type=EdgeType(edge_type),
                metadata=json.loads(metadata_json)
            )

        conn.close()

    def create_node(
        self,
        node_type: NodeType,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
        compute_embedding: bool = True
    ) -> str:
        """Create a new node in the graph."""
        node_id = str(uuid.uuid4())
        metadata = metadata or {}

        embedding = None
        embedding_blob = None
        if compute_embedding and node_type != NodeType.SOLUTION:
            embedding = self.embedding_service.get_embedding(text)
            embedding_blob = embedding.tobytes()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO nodes (id, node_type, text, metadata, embedding) VALUES (?, ?, ?, ?, ?)',
            (node_id, node_type.value, text, json.dumps(metadata), embedding_blob)
        )
        conn.commit()
        conn.close()

        self.graph.add_node(
            node_id,
            node_type=node_type,
            text=text,
            metadata=metadata,
            embedding=embedding
        )

        return node_id

    def create_edge(
        self,
        source_id: str,
        target_id: str,
        edge_type: EdgeType,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create a new edge in the graph."""
        edge_id = str(uuid.uuid4())
        metadata = metadata or {}

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO edges (id, source_id, target_id, edge_type, metadata) VALUES (?, ?, ?, ?, ?)',
            (edge_id, source_id, target_id, edge_type.value, json.dumps(metadata))
        )
        conn.commit()
        conn.close()

        self.graph.add_edge(
            source_id,
            target_id,
            id=edge_id,
            edge_type=edge_type,
            metadata=metadata
        )

        return edge_id

    def get_nodes_by_type(self, node_type: NodeType) -> List[Tuple[str, Dict]]:
        """Get all nodes of a specific type."""
        return [
            (node_id, data)
            for node_id, data in self.graph.nodes(data=True)
            if data.get('node_type') == node_type
        ]

    def find_similar_node(
        self,
        node_type: NodeType,
        text: str,
        threshold: Optional[float] = None
    ) -> Optional[Tuple[str, float]]:
        """Find existing node semantically similar to text.

        Returns:
            (node_id, similarity) if found above threshold, else None
        """
        threshold = threshold or self.SIMILARITY_THRESHOLD
        query_embedding = self.embedding_service.get_embedding(text)

        candidates = []
        for node_id, data in self.get_nodes_by_type(node_type):
            if data.get('embedding') is not None:
                candidates.append((node_id, data['embedding']))

        if not candidates:
            return None

        results = self.embedding_service.find_similar(
            query_embedding, candidates, threshold, top_k=1
        )

        if results:
            return results[0]
        return None

    def find_or_create_node(
        self,
        node_type: NodeType,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
        threshold: Optional[float] = None
    ) -> Tuple[str, bool]:
        """Find existing similar node or create new one.

        Returns:
            (node_id, is_new) - node_id and whether it was newly created
        """
        similar = self.find_similar_node(node_type, text, threshold)

        if similar:
            node_id, similarity = similar
            return node_id, False

        node_id = self.create_node(node_type, text, metadata)
        return node_id, True

    # Required schema: field_name -> (NodeType, EdgeType)
    REQUIRED_SCHEMA = {
        'core_mechanism':    (NodeType.MECHANISM,      EdgeType.USES_MECHANISM),
        'long_term_vision':  (NodeType.OUTCOME,        EdgeType.PRODUCES_OUTCOME),
        'design_principles': (NodeType.PRINCIPLE,      EdgeType.FOLLOWS_PRINCIPLE),
        'why_it_fails':      (NodeType.CRITICISM,      EdgeType.HAS_CRITICISM),
        'why_it_works':      (NodeType.JUSTIFICATION,  EdgeType.HAS_JUSTIFICATION),
        'what_is_new':       (NodeType.NOVELTY,        EdgeType.CLAIMS_NOVELTY),
    }

    def add_solution(
        self,
        solution: Dict[str, Any],
        field_mappings: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Add a solution with strict enforcement that EVERY schema field is mapped.

        ALL fields are required. For each field, agent explicitly decides:
        - 'NEW' or None → Create a new node with the text content
        - '<existing_node_id>' → Link to that existing node

        Args:
            solution: Solution dict with 'label' and ALL required field texts
            field_mappings: Dict mapping field_name -> 'NEW' or existing node_id
                           e.g. {'core_mechanism': 'NEW', 'why_it_fails': 'abc123'}
                           If None, all fields create NEW nodes (auto mode)

        Returns:
            Dict with solution_id, created nodes, linked nodes
            On failure: {"success": False, "error": "..."}
        """
        field_mappings = field_mappings or {}

        # 1. Validate 'label' is present
        if not solution.get('label'):
            return {"success": False, "error": "Missing required field: label"}

        # 2. Validate ALL required field texts are present
        missing_text = [k for k in self.REQUIRED_SCHEMA if not solution.get(k)]
        if missing_text:
            return {
                "success": False,
                "error": f"Missing required text fields: {missing_text}. ALL fields required."
            }

        # 3. Validate all explicit link IDs exist and have correct type
        for field_name, link_id in field_mappings.items():
            if field_name not in self.REQUIRED_SCHEMA:
                return {"success": False, "error": f"Unknown field in mapping: {field_name}"}

            if link_id and link_id.upper() != 'NEW':
                # Agent wants to link to existing node
                if link_id not in self.graph:
                    return {
                        "success": False,
                        "error": f"Cannot link {field_name}: node {link_id} does not exist"
                    }
                expected_type, _ = self.REQUIRED_SCHEMA[field_name]
                actual_type = self.graph.nodes[link_id].get('node_type')
                if actual_type != expected_type:
                    return {
                        "success": False,
                        "error": f"Type mismatch for {field_name}: expected {expected_type.name}, got {actual_type.name if actual_type else 'None'}"
                    }

        # 4. Create the container Solution node
        sol_id = self.create_node(
            NodeType.SOLUTION,
            solution['label'],
            metadata={'full_solution': solution},
            compute_embedding=False
        )

        created_nodes = {}
        linked_nodes = {}

        # 5. Process every required field
        for field_name, (node_type, edge_type) in self.REQUIRED_SCHEMA.items():
            text_content = solution[field_name]
            link_id = field_mappings.get(field_name)

            if link_id and link_id.upper() != 'NEW':
                # Case A: Explicit link (agent provided ID)
                target_id = link_id
                linked_nodes[field_name] = {
                    'id': target_id,
                    'existing_text': self.graph.nodes[target_id]['text'][:80]
                }
            else:
                # Case B: Auto-link if similar exists, otherwise create new
                similar = self.find_similar_node(node_type, text_content)  # Uses class default 0.85

                if similar:
                    target_id, sim = similar
                    linked_nodes[field_name] = {
                        'id': target_id,
                        'similarity': sim,
                        'existing_text': self.graph.nodes[target_id]['text'][:80]
                    }
                else:
                    target_id = self.create_node(node_type, text_content)
                    created_nodes[field_name] = {
                        'id': target_id,
                        'text': text_content[:80]
                    }

            # Create the edge
            self.create_edge(sol_id, target_id, edge_type)

        return {
            "success": True,
            "solution_id": sol_id,
            "created": created_nodes,
            "linked": linked_nodes
        }

    def get_solution_count_for_node(self, node_id: str) -> int:
        """Count how many solutions link to this node."""
        count = 0
        for pred in self.graph.predecessors(node_id):
            pred_data = self.graph.nodes[pred]
            if pred_data.get('node_type') == NodeType.SOLUTION:
                count += 1
        return count

    def find_gaps(self) -> Dict[str, Any]:
        """Find unexplored regions in the solution space.

        Returns:
            Dict with underused_mechanisms, orphan_outcomes, unseen_combos
        """
        gaps = {
            'underused_mechanisms': [],
            'orphan_outcomes': [],
            'unseen_combos': [],
            'summary': {}
        }

        mechanisms = self.get_nodes_by_type(NodeType.MECHANISM)
        for mech_id, data in mechanisms:
            count = self.get_solution_count_for_node(mech_id)
            if count < 2:
                gaps['underused_mechanisms'].append({
                    'id': mech_id,
                    'text': data['text'][:100],
                    'solution_count': count
                })

        outcomes = self.get_nodes_by_type(NodeType.OUTCOME)
        for out_id, data in outcomes:
            count = self.get_solution_count_for_node(out_id)
            if count == 0:
                gaps['orphan_outcomes'].append({
                    'id': out_id,
                    'text': data['text'][:100]
                })

        mech_outcome_pairs = set()
        solutions = self.get_nodes_by_type(NodeType.SOLUTION)
        for sol_id, _ in solutions:
            sol_mechs = [
                succ for succ in self.graph.successors(sol_id)
                if self.graph.nodes[succ].get('node_type') == NodeType.MECHANISM
            ]
            sol_outcomes = [
                succ for succ in self.graph.successors(sol_id)
                if self.graph.nodes[succ].get('node_type') == NodeType.OUTCOME
            ]
            for m in sol_mechs:
                for o in sol_outcomes:
                    mech_outcome_pairs.add((m, o))

        all_mechs = [m[0] for m in mechanisms[:10]]
        all_outcomes = [o[0] for o in outcomes[:10]]
        for m in all_mechs:
            for o in all_outcomes:
                if (m, o) not in mech_outcome_pairs:
                    gaps['unseen_combos'].append({
                        'mechanism_id': m,
                        'mechanism_text': self.graph.nodes[m]['text'][:60],
                        'outcome_id': o,
                        'outcome_text': self.graph.nodes[o]['text'][:60]
                    })
                    if len(gaps['unseen_combos']) >= 10:
                        break
            if len(gaps['unseen_combos']) >= 10:
                break

        gaps['summary'] = {
            'total_solutions': len(solutions),
            'total_mechanisms': len(mechanisms),
            'total_outcomes': len(outcomes),
            'underused_mechanism_count': len(gaps['underused_mechanisms']),
            'orphan_outcome_count': len(gaps['orphan_outcomes']),
            'unseen_combo_count': len(gaps['unseen_combos'])
        }

        return gaps

    def check_novelty(self, solution: Dict[str, Any]) -> Dict[str, Any]:
        """Check if a solution is novel enough to add.

        Returns:
            Dict with is_novel, similar_mechanism, suggestions for morphing
        """
        result = {
            'is_novel': True,
            'mechanism_overlap': None,
            'outcome_overlap': [],
            'suggestions': []
        }

        mechanism_text = solution.get('core_mechanism', '')
        if mechanism_text:
            similar = self.find_similar_node(NodeType.MECHANISM, mechanism_text)
            if similar:
                mech_id, sim = similar
                result['mechanism_overlap'] = {
                    'node_id': mech_id,
                    'similarity': sim,
                    'existing_text': self.graph.nodes[mech_id]['text'][:200]
                }
                if sim > 0.92:
                    result['is_novel'] = False

        # Handle both field names for outcomes
        outcomes = solution.get('long_term_implications') or solution.get('long_term_vision', [])
        if isinstance(outcomes, str):
            outcomes = [outcomes]
        for outcome_text in outcomes:
            similar = self.find_similar_node(NodeType.OUTCOME, outcome_text, threshold=0.90)
            if similar:
                out_id, sim = similar
                result['outcome_overlap'].append({
                    'node_id': out_id,
                    'similarity': sim,
                    'new_text': outcome_text[:100],
                    'existing_text': self.graph.nodes[out_id]['text'][:100]
                })

        if not result['is_novel']:
            gaps = self.find_gaps()
            if gaps['underused_mechanisms']:
                result['suggestions'].append(
                    f"Try using underexplored mechanism: {gaps['underused_mechanisms'][0]['text'][:80]}"
                )
            if gaps['unseen_combos']:
                combo = gaps['unseen_combos'][0]
                result['suggestions'].append(
                    f"Try combining '{combo['mechanism_text']}' with outcome '{combo['outcome_text']}'"
                )

        return result

    def merge_nodes(self, node_id_keep: str, node_id_remove: str) -> bool:
        """Merge two nodes, redirecting all edges to the kept node."""
        if node_id_keep not in self.graph or node_id_remove not in self.graph:
            return False

        for pred in list(self.graph.predecessors(node_id_remove)):
            edge_data = self.graph.edges[pred, node_id_remove]
            if not self.graph.has_edge(pred, node_id_keep):
                self.create_edge(pred, node_id_keep, edge_data['edge_type'], edge_data.get('metadata'))

        for succ in list(self.graph.successors(node_id_remove)):
            edge_data = self.graph.edges[node_id_remove, succ]
            if not self.graph.has_edge(node_id_keep, succ):
                self.create_edge(node_id_keep, succ, edge_data['edge_type'], edge_data.get('metadata'))

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM edges WHERE source_id = ? OR target_id = ?',
                       (node_id_remove, node_id_remove))
        cursor.execute('DELETE FROM nodes WHERE id = ?', (node_id_remove,))
        conn.commit()
        conn.close()

        self.graph.remove_node(node_id_remove)

        return True

    # =========================================================================
    # HIERARCHY OPERATIONS
    # =========================================================================

    def create_child(
        self,
        parent_id: str,
        text: str,
        node_type: Optional[NodeType] = None
    ) -> str:
        """Create a child node under a parent.

        If node_type not specified, inherits from parent.
        Returns the new child node ID.
        """
        if parent_id not in self.graph:
            raise ValueError(f"Parent node {parent_id} not found")

        parent_data = self.graph.nodes[parent_id]
        child_type = node_type or parent_data['node_type']

        # Create the child node
        child_id = self.create_node(child_type, text)

        # Create parent -> child edge
        self.create_edge(parent_id, child_id, EdgeType.PARENT_OF)

        return child_id

    def set_parent(self, child_id: str, parent_id: str) -> bool:
        """Set or change a node's parent.

        Removes any existing parent relationship first.
        """
        if child_id not in self.graph:
            raise ValueError(f"Child node {child_id} not found")
        if parent_id not in self.graph:
            raise ValueError(f"Parent node {parent_id} not found")

        # Verify same type
        child_type = self.graph.nodes[child_id]['node_type']
        parent_type = self.graph.nodes[parent_id]['node_type']
        if child_type != parent_type:
            raise ValueError(f"Type mismatch: child is {child_type}, parent is {parent_type}")

        # Remove existing parent edge if any
        for pred in list(self.graph.predecessors(child_id)):
            edge_data = self.graph.edges.get((pred, child_id), {})
            if edge_data.get('edge_type') == EdgeType.PARENT_OF:
                conn = sqlite3.connect(self.db_path)
                conn.execute('DELETE FROM edges WHERE source_id = ? AND target_id = ?',
                            (pred, child_id))
                conn.commit()
                conn.close()
                self.graph.remove_edge(pred, child_id)

        # Create new parent -> child edge
        self.create_edge(parent_id, child_id, EdgeType.PARENT_OF)
        return True

    def get_children(self, node_id: str) -> List[Tuple[str, Dict]]:
        """Get all direct children of a node."""
        if node_id not in self.graph:
            return []

        children = []
        for succ in self.graph.successors(node_id):
            edge_data = self.graph.edges.get((node_id, succ), {})
            if edge_data.get('edge_type') == EdgeType.PARENT_OF:
                children.append((succ, self.graph.nodes[succ]))
        return children

    def get_parent(self, node_id: str) -> Optional[Tuple[str, Dict]]:
        """Get the parent of a node, if any."""
        if node_id not in self.graph:
            return None

        for pred in self.graph.predecessors(node_id):
            edge_data = self.graph.edges.get((pred, node_id), {})
            if edge_data.get('edge_type') == EdgeType.PARENT_OF:
                return (pred, self.graph.nodes[pred])
        return None

    def get_roots(self, node_type: NodeType) -> List[Tuple[str, Dict]]:
        """Get all root nodes (no parent) of a given type."""
        roots = []
        for node_id, data in self.get_nodes_by_type(node_type):
            if self.get_parent(node_id) is None:
                roots.append((node_id, data))
        return roots

    def get_hierarchy_tree(self, node_type: NodeType, indent: int = 0) -> str:
        """Get a text representation of the hierarchy for a node type."""
        lines = []

        def add_node(node_id: str, data: Dict, depth: int):
            prefix = "  " * depth + ("├── " if depth > 0 else "")
            count = self.get_solution_count_for_node(node_id)
            lines.append(f"{prefix}[{count}] {data['text'][:50]}... ({node_id[:8]})")
            for child_id, child_data in self.get_children(node_id):
                add_node(child_id, child_data, depth + 1)

        roots = self.get_roots(node_type)
        if not roots:
            return f"No {node_type.name} hierarchy (all nodes are flat)"

        for root_id, root_data in roots:
            add_node(root_id, root_data, 0)

        return "\n".join(lines)

    def _render_hierarchy(self, node_type: NodeType, root_nodes: List[str], visited: set, level: int = 0) -> List[str]:
        """Recursively render a hierarchy of nodes as indented tree."""
        lines = []
        indent = "  " * level
        for node_id in root_nodes:
            if node_id in visited:
                continue
            visited.add(node_id)

            data = self.graph.nodes[node_id]
            count = self.get_solution_count_for_node(node_id)
            short_id = node_id[:8]

            # Formatting: "  [1a2b3c4d] Category Name (5 sols)"
            lines.append(f"{indent}[{short_id}] {data['text'][:60]} ({count} sols)")

            # Find children (nodes where THIS node is PARENT_OF child)
            children = []
            for successor in self.graph.successors(node_id):
                edge_data = self.graph.get_edge_data(node_id, successor)
                if edge_data.get('edge_type') == EdgeType.PARENT_OF:
                    children.append(successor)

            if children:
                lines.extend(self._render_hierarchy(node_type, children, visited, level + 1))

        return lines

    def _get_roots_for_type(self, node_type: NodeType) -> List[str]:
        """Find root nodes (no parent) of a given type."""
        all_nodes = [n for n, d in self.graph.nodes(data=True) if d.get('node_type') == node_type]
        roots = []
        for n in all_nodes:
            has_parent = False
            for pred in self.graph.predecessors(n):
                edge = self.graph.get_edge_data(pred, n)
                if edge.get('edge_type') == EdgeType.PARENT_OF:
                    has_parent = True
                    break
            if not has_parent:
                roots.append(n)
        return roots

    def get_graph_state_for_prompt(self) -> str:
        """Generate a hierarchical text summary of graph state for LLM prompts."""
        solutions = self.get_nodes_by_type(NodeType.SOLUTION)
        mechanisms = self.get_nodes_by_type(NodeType.MECHANISM)
        outcomes = self.get_nodes_by_type(NodeType.OUTCOME)
        principles = self.get_nodes_by_type(NodeType.PRINCIPLE)
        criticisms = self.get_nodes_by_type(NodeType.CRITICISM)
        justifications = self.get_nodes_by_type(NodeType.JUSTIFICATION)
        novelties = self.get_nodes_by_type(NodeType.NOVELTY)

        lines = ["=== CURRENT TAXONOMY ===", ""]
        lines.append(f"Solutions: {len(solutions)}")
        lines.append(f"Unique Mechanisms: {len(mechanisms)}")
        lines.append(f"Unique Outcomes: {len(outcomes)}")
        lines.append(f"Unique Principles: {len(principles)}")
        lines.append(f"Unique Criticisms: {len(criticisms)}")
        lines.append(f"Unique Justifications: {len(justifications)}")
        lines.append(f"Unique Novelties: {len(novelties)}")
        lines.append("")

        # Render hierarchies for key node types
        for n_type in [NodeType.MECHANISM, NodeType.OUTCOME, NodeType.PRINCIPLE]:
            type_nodes = self.get_nodes_by_type(n_type)
            if not type_nodes:
                continue

            lines.append(f"{n_type.name} HIERARCHY:")
            roots = self._get_roots_for_type(n_type)
            visited = set()
            tree_lines = self._render_hierarchy(n_type, roots, visited)
            if tree_lines:
                lines.extend(tree_lines)
            else:
                lines.append("  (no nodes)")
            lines.append("")

        # Show criticisms (shared failure modes) - flat for now
        if criticisms:
            lines.append("CRITICISMS (shared failure modes):")
            for crit_id, data in criticisms[:5]:
                count = self.get_solution_count_for_node(crit_id)
                short_id = crit_id[:8]
                lines.append(f"  [{short_id}] {data['text'][:60]} ({count} sols)")
            lines.append("")

        # Show justifications - flat for now
        if justifications:
            lines.append("JUSTIFICATIONS:")
            for just_id, data in justifications[:5]:
                count = self.get_solution_count_for_node(just_id)
                short_id = just_id[:8]
                lines.append(f"  [{short_id}] {data['text'][:60]} ({count} sols)")
            lines.append("")

        # Show gaps
        gaps = self.find_gaps()
        lines.append("=== UNEXPLORED GAPS ===")
        for gap in gaps['underused_mechanisms'][:3]:
            lines.append(f"  - Mechanism has only {gap['solution_count']} solution(s): {gap['text'][:60]}...")
        for combo in gaps['unseen_combos'][:3]:
            lines.append(f"  - No solution combines: '{combo['mechanism_text'][:40]}' with '{combo['outcome_text'][:40]}'")

        return "\n".join(lines)

    def stats(self) -> Dict[str, int]:
        """Get basic graph statistics."""
        return {
            'nodes': self.graph.number_of_nodes(),
            'edges': self.graph.number_of_edges(),
            'solutions': len(self.get_nodes_by_type(NodeType.SOLUTION)),
            'mechanisms': len(self.get_nodes_by_type(NodeType.MECHANISM)),
            'outcomes': len(self.get_nodes_by_type(NodeType.OUTCOME)),
            'principles': len(self.get_nodes_by_type(NodeType.PRINCIPLE)),
            'criticisms': len(self.get_nodes_by_type(NodeType.CRITICISM)),
            'justifications': len(self.get_nodes_by_type(NodeType.JUSTIFICATION)),
            'novelties': len(self.get_nodes_by_type(NodeType.NOVELTY))
        }

    # =========================================================================
    # TRANSACTIONAL RESTRUCTURING
    # =========================================================================

    def delete_node_cascade(self, node_id: str) -> Dict[str, Any]:
        """Delete a node and cascade-delete its edges (DB handles via foreign keys)."""
        if node_id not in self.graph:
            return {"success": False, "error": "Node not found"}

        # Count edges being removed
        edges_removed = self.graph.in_degree(node_id) + self.graph.out_degree(node_id)

        # Delete from DB (CASCADE handles edges via foreign keys)
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute('DELETE FROM nodes WHERE id = ?', (node_id,))
        conn.commit()
        conn.close()

        # Remove from in-memory graph
        self.graph.remove_node(node_id)

        return {"success": True, "edges_removed": edges_removed}

    def _validate_orphans(self, graph: nx.DiGraph) -> List[str]:
        """Find solutions missing required links (mechanism or outcome)."""
        orphans = []
        for node_id, data in graph.nodes(data=True):
            if data.get('node_type') == NodeType.SOLUTION:
                has_mech = False
                has_out = False
                for succ in graph.successors(node_id):
                    succ_type = graph.nodes[succ].get('node_type')
                    if succ_type == NodeType.MECHANISM:
                        has_mech = True
                    if succ_type == NodeType.OUTCOME:
                        has_out = True
                if not has_mech or not has_out:
                    label = data.get('text', node_id)
                    missing = []
                    if not has_mech:
                        missing.append('MECHANISM')
                    if not has_out:
                        missing.append('OUTCOME')
                    orphans.append(f"{label} (missing: {', '.join(missing)})")
        return orphans

    def execute_transaction(self, operations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Execute a batch of graph operations atomically with shadow validation.

        Operations format:
        [
            {'op': 'DELETE_NODE', 'id': 'node_uuid'},
            {'op': 'CREATE_NODE', 'type': 'MECHANISM', 'text': '...', 'temp_id': 'tmp1'},
            {'op': 'LINK', 'source_id': 'sol_id', 'target_temp_id': 'tmp1', 'edge_type': 'USES_MECHANISM'}
        ]
        """
        # 1. Create shadow graph for validation
        shadow_graph = self.graph.copy()
        temp_id_map = {}  # 'tmp1' -> real_uuid

        # 2. Replay operations on shadow graph
        try:
            for op in operations:
                if op['op'] == 'DELETE_NODE':
                    if op['id'] in shadow_graph:
                        shadow_graph.remove_node(op['id'])
                    else:
                        raise ValueError(f"Node not found: {op['id']}")

                elif op['op'] == 'CREATE_NODE':
                    real_id = str(uuid.uuid4())
                    temp_id = op.get('temp_id', real_id)
                    temp_id_map[temp_id] = real_id

                    shadow_graph.add_node(
                        real_id,
                        node_type=NodeType(op['type']),
                        text=op['text'],
                        metadata={}
                    )

                elif op['op'] == 'LINK':
                    # Resolve source
                    src = op.get('source_id')
                    if 'source_temp_id' in op:
                        src = temp_id_map.get(op['source_temp_id'])

                    # Resolve target
                    tgt = op.get('target_id')
                    if 'target_temp_id' in op:
                        tgt = temp_id_map.get(op['target_temp_id'])

                    if not src or not tgt:
                        raise ValueError(f"Invalid LINK: could not resolve IDs in {op}")

                    if src not in shadow_graph:
                        raise ValueError(f"Source not in graph: {src}")
                    if tgt not in shadow_graph:
                        raise ValueError(f"Target not in graph: {tgt}")

                    # Get edge type
                    edge_type = EdgeType(op.get('edge_type', 'USES_MECHANISM'))

                    # Remove existing edge of same type from source to any target
                    target_node_type = shadow_graph.nodes[tgt].get('node_type')
                    for existing_succ in list(shadow_graph.successors(src)):
                        if shadow_graph.nodes[existing_succ].get('node_type') == target_node_type:
                            shadow_graph.remove_edge(src, existing_succ)

                    # Add new edge
                    shadow_graph.add_edge(src, tgt, edge_type=edge_type)

        except Exception as e:
            return {"success": False, "error": f"Shadow replay failed: {str(e)}"}

        # 3. Validate orphan invariant on shadow
        orphans = self._validate_orphans(shadow_graph)
        if orphans:
            return {
                "success": False,
                "error": f"Orphan solutions would be created: {orphans}",
                "rolled_back": True
            }

        # 4. Commit to real graph + DB (replay operations)
        try:
            for op in operations:
                if op['op'] == 'DELETE_NODE':
                    self.delete_node_cascade(op['id'])

                elif op['op'] == 'CREATE_NODE':
                    real_id = temp_id_map[op.get('temp_id', list(temp_id_map.values())[-1])]
                    # Create with specific ID
                    metadata = {}
                    embedding = None
                    embedding_blob = None
                    if NodeType(op['type']) != NodeType.SOLUTION:
                        embedding = self.embedding_service.get_embedding(op['text'])
                        embedding_blob = embedding.tobytes()

                    conn = sqlite3.connect(self.db_path)
                    conn.execute(
                        'INSERT INTO nodes (id, node_type, text, metadata, embedding) VALUES (?, ?, ?, ?, ?)',
                        (real_id, op['type'], op['text'], json.dumps(metadata), embedding_blob)
                    )
                    conn.commit()
                    conn.close()

                    self.graph.add_node(
                        real_id,
                        node_type=NodeType(op['type']),
                        text=op['text'],
                        metadata=metadata,
                        embedding=embedding
                    )

                elif op['op'] == 'LINK':
                    src = op.get('source_id') or temp_id_map.get(op.get('source_temp_id'))
                    tgt = op.get('target_id') or temp_id_map.get(op.get('target_temp_id'))
                    edge_type = EdgeType(op.get('edge_type', 'USES_MECHANISM'))

                    # Remove existing edges of same type
                    target_node_type = self.graph.nodes[tgt].get('node_type')
                    for existing_succ in list(self.graph.successors(src)):
                        if self.graph.nodes[existing_succ].get('node_type') == target_node_type:
                            # Remove from DB
                            conn = sqlite3.connect(self.db_path)
                            conn.execute('DELETE FROM edges WHERE source_id = ? AND target_id = ?',
                                         (src, existing_succ))
                            conn.commit()
                            conn.close()
                            # Remove from graph
                            self.graph.remove_edge(src, existing_succ)

                    # Create new edge
                    self.create_edge(src, tgt, edge_type)

            return {"success": True, "temp_id_map": temp_id_map}

        except Exception as e:
            return {"success": False, "error": f"Commit failed: {str(e)}"}
