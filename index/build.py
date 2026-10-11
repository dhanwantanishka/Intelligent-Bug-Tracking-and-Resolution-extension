"""
IBTRRS Offline Safe Index Builder
Extracts vocabulary and IDF weights into JSON, document matrix into SciPy/NumPy NPZ format.
Eliminates code execution risks (replaces joblib/pickle per ADR-010).
"""

from __future__ import annotations
import json
import hashlib
from pathlib import Path
import re
from typing import Dict, List, Any
import numpy as np
from scipy import sparse


def tokenize(text: str) -> List[str]:
    """Extract alphanumeric token strings."""
    return re.findall(r"\b[a-zA-Z0-9_]{2,}\b", text.lower())


def build_safe_index(
    corpus_jsonl_path: Path,
    artifacts_dir: Path
) -> Dict[str, Any]:
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    
    records = []
    corpus_sha = hashlib.sha256(corpus_jsonl_path.read_bytes()).hexdigest()
    
    with open(corpus_jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
                
    # Prepare documents: combine diagnostic code, message, explanation, and buggy snippet
    docs = []
    record_ids = []
    for r in records:
        record_ids.append(r["record_id"])
        combined_text = (
            f"{r['diagnostic']['code']} "
            f"{r['diagnostic']['message_pattern']} "
            f"{r['explanation']} "
            f"{r['buggy_snippet']}"
        )
        docs.append(tokenize(combined_text))
        
    N = len(docs)
    if N == 0:
        raise ValueError("Corpus contains no records")

    # Document frequencies
    df_counts: Dict[str, int] = {}
    for doc in docs:
        unique_tokens = set(doc)
        for token in unique_tokens:
            df_counts[token] = df_counts.get(token, 0) + 1
            
    # Build sorted vocabulary
    vocab = {token: idx for idx, token in enumerate(sorted(df_counts.keys()))}
    
    # Calculate smooth IDF: ln((1 + N) / (1 + df)) + 1
    idf = np.zeros(len(vocab), dtype=np.float32)
    for token, idx in vocab.items():
        df = df_counts[token]
        idf[idx] = float(np.log((1.0 + N) / (1.0 + df)) + 1.0)
        
    # Build sparse TF-IDF document matrix
    rows: List[int] = []
    cols: List[int] = []
    data: List[float] = []
    
    for doc_idx, doc in enumerate(docs):
        term_counts: Dict[str, int] = {}
        for token in doc:
            if token in vocab:
                term_counts[token] = term_counts.get(token, 0) + 1
        
        doc_len = len(doc) if len(doc) > 0 else 1
        for token, count in term_counts.items():
            feat_idx = vocab[token]
            tf = count / doc_len
            score = tf * idf[feat_idx]
            rows.append(doc_idx)
            cols.append(feat_idx)
            data.append(score)
            
    matrix = sparse.csr_matrix(
        (data, (rows, cols)),
        shape=(N, len(vocab)),
        dtype=np.float32
    )
    
    # L2 normalize rows for fast cosine ranking via dot product
    row_norms = sparse.linalg.norm(matrix, axis=1)
    row_norms[row_norms == 0] = 1.0
    matrix = matrix.multiply(sparse.csr_matrix(1.0 / row_norms).T).tocsr()

    # Paths
    vocab_file = artifacts_dir / "vocab.json"
    idf_file = artifacts_dir / "idf.json"
    matrix_file = artifacts_dir / "matrix.npz"
    records_file = artifacts_dir / "records.json"
    manifest_file = artifacts_dir / "manifest.json"

    # Write files
    vocab_file.write_text(json.dumps(vocab, indent=2), encoding="utf-8")
    idf_file.write_text(json.dumps(idf.tolist(), indent=2), encoding="utf-8")
    sparse.save_npz(matrix_file, matrix)
    records_file.write_text(json.dumps(records, indent=2), encoding="utf-8")
    
    # Write manifest with SHA-256 integrity verification
    manifest = {
        "manifest_version": "1.0",
        "record_count": N,
        "vocabulary_size": len(vocab),
        "corpus_sha256": corpus_sha,
        "vocab_sha256": hashlib.sha256(vocab_file.read_bytes()).hexdigest(),
        "idf_sha256": hashlib.sha256(idf_file.read_bytes()).hexdigest(),
        "matrix_sha256": hashlib.sha256(matrix_file.read_bytes()).hexdigest(),
        "records_sha256": hashlib.sha256(records_file.read_bytes()).hexdigest(),
    }
    manifest_file.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    
    return manifest


if __name__ == "__main__":
    base_dir = Path(__file__).resolve().parent.parent
    corpus_path = base_dir / "corpus" / "records" / "records.jsonl"
    art_dir = base_dir / "index" / "artifacts"
    manifest = build_safe_index(corpus_path, art_dir)
    print(f"Index built successfully: {manifest['record_count']} records, {manifest['vocabulary_size']} terms.")

