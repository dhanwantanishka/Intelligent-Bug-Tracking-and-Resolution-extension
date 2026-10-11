"""
Safe TF-IDF Search Engine
Loads JSON vocabulary and IDF arrays, alongside SciPy sparse matrix.
Performs cosine ranking without executing pickle files.
"""

from __future__ import annotations
import json
import re
from pathlib import Path
from typing import List, Dict, Any, Tuple
import numpy as np
from scipy import sparse


def tokenize(text: str) -> List[str]:
    return re.findall(r"\b[a-zA-Z0-9_]{2,}\b", text.lower())


class IndexEngine:
    def __init__(self, artifacts_dir: Path):
        self.artifacts_dir = artifacts_dir
        self.vocab: Dict[str, int] = {}
        self.idf: np.ndarray = np.array([])
        self.matrix: Optional[sparse.csr_matrix] = None
        self.records: List[Dict[str, Any]] = []
        self.manifest: Dict[str, Any] = {}
        self.is_loaded = False

    def load(self) -> bool:
        vocab_path = self.artifacts_dir / "vocab.json"
        idf_path = self.artifacts_dir / "idf.json"
        matrix_path = self.artifacts_dir / "matrix.npz"
        records_path = self.artifacts_dir / "records.json"
        manifest_path = self.artifacts_dir / "manifest.json"

        if not (vocab_path.exists() and idf_path.exists() and matrix_path.exists() and records_path.exists()):
            return False

        self.vocab = json.loads(vocab_path.read_text(encoding="utf-8"))
        self.idf = np.array(json.loads(idf_path.read_text(encoding="utf-8")), dtype=np.float32)
        self.matrix = sparse.load_npz(matrix_path)
        self.records = json.loads(records_path.read_text(encoding="utf-8"))
        if manifest_path.exists():
            self.manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

        self.is_loaded = True
        return True

    def query(self, query_text: str, top_k: int = 3, relevance_floor: float = 0.25) -> List[Tuple[Dict[str, Any], float]]:
        if not self.is_loaded or self.matrix is None:
            return []

        tokens = tokenize(query_text)
        if not tokens:
            return []

        # Build query vector
        term_counts: Dict[str, int] = {}
        for t in tokens:
            if t in self.vocab:
                term_counts[t] = term_counts.get(t, 0) + 1

        if not term_counts:
            return []

        q_vec = np.zeros(len(self.vocab), dtype=np.float32)
        q_len = len(tokens)
        for t, count in term_counts.items():
            idx = self.vocab[t]
            tf = count / q_len
            q_vec[idx] = tf * self.idf[idx]

        norm = np.linalg.norm(q_vec)
        if norm > 0:
            q_vec /= norm

        # Cosine similarity dot product against normalized matrix rows
        scores = self.matrix.dot(q_vec)
        ranked_indices = np.argsort(scores)[::-1]

        results = []
        for idx in ranked_indices[:top_k]:
            score = float(scores[idx])
            if score >= relevance_floor:
                results.append((self.records[idx], score))

        return results

