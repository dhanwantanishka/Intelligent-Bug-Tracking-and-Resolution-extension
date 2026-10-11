# Intelligent Bug Tracking and Resolution Recommendation System (IBTRRS)

A lightweight, privacy-preserving VS Code extension for Python developers paired with a local FastAPI backend. Turns Python diagnostics into either deterministic Quick Fixes or reviewed, AI-proposed unified diffs with human-in-the-loop preview and post-fix verification.

---

## Key Features
- **Deterministic vs. AI Separation:** Local rules (like unused import removal) execute instantly without network overhead.
- **Safe TF-IDF Retrieval:** Replaces unsafe `joblib` deserialization with explicit `vocab.json`, `idf.json`, and `matrix.npz` files (ADR-010).
- **Tolerant Diff Matching:** Employs sliding-window context matching to handle LLM line-number drift without failing valid patches.
- **In-Memory Diff Preview:** Previews diffs natively in VS Code (`ibtrrs-diff://`) without writing temporary files to disk.
- **Post-Fix Verification:** Settling debounce mechanism to accurately track whether diagnostics were resolved by Pyright/Ruff.
- **Privacy by Design:** Bounded context windows ($\le 200$ lines, $\le 16$ KB), no telemetry, AI disabled by default.

---

## Directory Structure
- `docs/`: Architecture blueprint, threat model, privacy inventory, and ADRs.
- `corpus/`: CC0-1.0 authored bug/fix records and validation tooling.
- `index/`: Offline reproducible safe index builder.
- `backend/`: FastAPI application, retrieval engine, prompt builder, and patch validator.
- `extension/`: TypeScript VS Code extension.

---

## Getting Started

### 1. Backend Setup
```bash
cd backend
pip install -e .
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### 2. Extension Setup
```bash
cd extension
npm install
npm run compile
```
Press `F5` in VS Code to launch the Extension Development Host.

