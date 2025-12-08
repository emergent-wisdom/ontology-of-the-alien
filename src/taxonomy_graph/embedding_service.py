"""Embedding service using sentence-transformers for semantic similarity."""

import numpy as np
from typing import List, Tuple, Optional
import sqlite3
import json


class EmbeddingService:
    """Handles text embeddings using sentence-transformers MiniLM model."""

    MODEL_NAME = 'all-MiniLM-L6-v2'
    EMBEDDING_DIM = 384

    def __init__(self, db_path: str = 'taxonomy.db'):
        self.db_path = db_path
        self._model = None
        self._init_cache_table()

    @property
    def model(self):
        """Lazy load the model."""
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self.MODEL_NAME)
        return self._model

    def _init_cache_table(self):
        """Create embedding cache table if it doesn't exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS embedding_cache (
                text_hash TEXT PRIMARY KEY,
                text TEXT NOT NULL,
                embedding BLOB NOT NULL
            )
        ''')
        conn.commit()
        conn.close()

    def _hash_text(self, text: str) -> str:
        """Create a hash for text lookup."""
        import hashlib
        return hashlib.sha256(text.encode()).hexdigest()

    def get_embedding(self, text: str) -> np.ndarray:
        """Get embedding for text, using cache if available."""
        text_hash = self._hash_text(text)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            'SELECT embedding FROM embedding_cache WHERE text_hash = ?',
            (text_hash,)
        )
        row = cursor.fetchone()

        if row:
            conn.close()
            return np.frombuffer(row[0], dtype=np.float32)

        embedding = self.model.encode(text, convert_to_numpy=True).astype(np.float32)

        cursor.execute(
            'INSERT INTO embedding_cache (text_hash, text, embedding) VALUES (?, ?, ?)',
            (text_hash, text, embedding.tobytes())
        )
        conn.commit()
        conn.close()

        return embedding

    def get_embeddings(self, texts: List[str]) -> List[np.ndarray]:
        """Get embeddings for multiple texts."""
        return [self.get_embedding(text) for text in texts]

    def cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """Compute cosine similarity between two vectors."""
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(np.dot(a, b) / (norm_a * norm_b))

    def find_similar(
        self,
        query_embedding: np.ndarray,
        candidates: List[Tuple[str, np.ndarray]],
        threshold: float = 0.85,
        top_k: int = 5
    ) -> List[Tuple[str, float]]:
        """Find candidates similar to query above threshold.

        Args:
            query_embedding: The embedding to search for
            candidates: List of (id, embedding) tuples to search
            threshold: Minimum similarity to include
            top_k: Maximum results to return

        Returns:
            List of (id, similarity) tuples, sorted by similarity desc
        """
        results = []
        for node_id, embedding in candidates:
            sim = self.cosine_similarity(query_embedding, embedding)
            if sim >= threshold:
                results.append((node_id, sim))

        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]
