# ADR-010: Safe Serialization for TF-IDF Corpus & Index Artifacts

## Context
The IBTRRS backend relies on an offline-computed TF-IDF index over hand-authored bug/fix records for retrieval-augmented prompt construction. In standard scikit-learn workflows, models and sparse matrices are persisted via `joblib.dump()` or `pickle.dump()`.

However, Python's `pickle` and `joblib` formats are inherently insecure: deserializing an untrusted or maliciously modified `.joblib` file can result in Arbitrary Code Execution (ACE) via `__reduce__` exploit payloads. While MVP artifacts are built locally, supply-chain attacks, git tampering, or distribution of index packages to users present an unacceptable security liability.

## Decision
We reject `joblib` and `pickle` for runtime index artifact storage. We instead adopt an explicit, non-executable data format:

1. **Vocabulary Mapping:** Serialized to `vocab.json` as a UTF-8 JSON object mapping `{ "term": feature_index }`.
2. **IDF Weights:** Serialized to `idf.json` as a UTF-8 JSON array of floats corresponding to feature indices.
3. **Document Matrix:** Serialized to `matrix.npz` using `scipy.sparse.save_npz` / `load_npz` (or raw NumPy array buffers), which stores compressed arrays of indices, indptr, and data without executable Python objects.
4. **Manifest & Integrity:** Serialized to `manifest.json` containing SHA-256 hashes of `vocab.json`, `idf.json`, `matrix.npz`, and the corpus source file, alongside build metadata.
5. **Runtime Inference:** Runtime query vectorization is implemented via a pure tokenization + vocabulary lookup + IDF weighting step, followed by vector dot-product cosine similarity against the sparse matrix.

## Status
**Accepted** (Gates 1 & 2 baseline)

## Consequences
- **Positive:** Completely eliminates the Arbitrary Code Execution threat vector from index deserialization.
- **Positive:** Index files are human-inspectable (`vocab.json`, `manifest.json`) and portable across Python versions without pickling incompatibility.
- **Positive:** Enables zero-dependency ranking if scikit-learn is ever removed from backend runtime dependencies.
- **Negative:** Requires a custom tokenization and scoring utility instead of calling `vectorizer.transform()` directly. This small offline/online utility is easy to unit-test and verify.

