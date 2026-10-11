# IBTRRS Architecture Blueprint (v0.2, Gate 1 Approved)
Intelligent Bug Tracking and Resolution Recommendation System

Legend: **[F]** verified fact · **[A]** assumption · **[D]** decision · **[Q]** open question · **[P]** proposed default

---

## 1. Executive Architecture Summary

**Product.** A VS Code extension for Python developers. It turns a Python diagnostic (error or lint warning) into either a safe local Quick Fix or a reviewed, AI-proposed unified diff. The developer always previews and approves. The extension then re-checks diagnostics and reports what actually happened.

**Users.** Individual Python developers working in VS Code on a local workspace.

**Core problem.** Fixing a diagnostic costs context switching. Generic chat tools lack editor state, make unverifiable edits, and send too much code. IBTRRS keeps the workflow in the editor and makes every change explicit and checkable.

**Components.**
- *Extension (TypeScript)* is the product. It owns diagnostics, context extraction, routing, local fixes, virtual diff preview, approval, apply, and verification.
- *Backend (Python, FastAPI, modular monolith)* owns retrieval over a secure TF-IDF index (JSON vocab/weights + NumPy matrix), prompt building, LLM calls through an adapter protocol, and tolerant patch validation.
- *Corpus and index pipeline (offline, Python)* builds a versioned, validated, reproducible artifact.

**Workflow.** Diagnostic → Quick Fix or "Recommend Resolution" → (local rule OR backend request) → proposal → in-memory virtual diff preview (`ibtrrs-diff://`) → explicit Apply/Reject → stale check → apply → re-run diagnostics with settling debounce → report outcome.

**Deterministic vs AI boundary.** Deterministic rules handle a small set of narrow, mechanically checkable fixes with explicit preconditions (including multi-line string & suppression comment guards). The AI path handles everything else, and its output is never trusted: it is parsed, validated, previewed, and approved before any change. Diagnostic severity and TF-IDF similarity are never presented as repair confidence.

---

## 2. Assumptions, Constraints, and Decisions (Gate 1 Updates)

| ID | Item | Status | Decision & Resolution |
|---|---|---|---|
| A1 | Diagnostics source | [D] | VS Code diagnostic collection populated by Pyright/Pylance or Ruff. |
| A2 | VS Code engine | [P] | Pin to minimum stable version supported by `@vscode/vsce`. |
| A3 | Backend deployment | [D] | Default local (`127.0.0.1`), loopback with token file. Remote out of MVP scope. |
| A4 | LLM provider strategy | [D] | Provider-independent `LLMProvider` protocol (ADR-003). OpenAI/Anthropic/LiteLLM compatible adapter for live mode; deterministic `FakeLLMProvider` for tests and local CI. |
| A5 | Corpus source | [D] | Hand-authored, CC0-1.0 synthetic fixtures written for this project (ADR-004). |
| A6 | Persistence | [D] | In-memory session log in extension; optional local JSONL history. Zero backend DB (ADR-007). |
| A7 | Test environment | [F] | Windows & Linux support. Universal POSIX path normalization enforced. |
| A8 | Index serialization | [D] | **ADR-010 Accepted:** Replace `joblib` with safe `vocab.json` + `idf.json` + `matrix.npz`. No arbitrary code execution risk. |

---

## 3. System-Context Architecture & Trust Boundaries

- **TB-1: Workspace/editor ↔ extension:** Workspace content is untrusted input.
- **TB-2: Extension ↔ backend:** Loopback HTTP (`127.0.0.1`) authenticated via 256-bit bearer token file with strict OS filesystem permissions.
- **TB-3: Backend ↔ LLM provider:** Remote HTTPS. Only bounded snippet ($\le 200$ lines, $\le 16$ KB), relative path, and diagnostic text are transmitted.
- **TB-4: Corpus/Index files ↔ backend:** Read-only data. Safe JSON + `.npz` deserialization without Python `pickle`.

---

## 4. Enhanced Component Specifications & Improvisations

### 4.1 Cross-Platform Path Normalization
- All file targets are strictly normalized to workspace-relative POSIX paths using forward slashes (`/`).
- Windows backslashes (`\`) are stripped/replaced at the boundary in both `context/extract.ts` and `backend/app/patch/validate.py`.
- Path traversal (`..`, absolute paths, symlinks outside workspace) is blocked by both client and backend validators.

### 4.2 Secure TF-IDF Retrieval Pipeline (ADR-010)
- Offline index build produces:
  1. `vocab.json`: Map of `{ token: index }`.
  2. `idf.json`: Array of float weights.
  3. `matrix.npz`: Sparse document vectors saved via `scipy.sparse.save_npz`.
  4. `manifest.json`: SHA-256 hashes of all files, corpus record count, build timestamp.
- Runtime query vectorizer: Uses token extraction matching `vocab.json` + IDF multiplication in NumPy. Cosine ranking via dot product against `matrix.npz`. **Zero `joblib` or `pickle` deserialization.**

### 4.3 Tolerant Patch Parsing & Offset Relocation
- Unified diffs produced by LLMs frequently suffer from header line-offset hallucination.
- The patch validator:
  1. Parses diff into expected context/deletion lines and addition lines.
  2. Tests exact line match at specified header line.
  3. If offset drifted, performs sliding-window context match within `context.text`.
  4. Validates that resulting python snippet parses cleanly with `ast.parse()`.
  5. Fine-grained refusal codes returned on failure.

### 4.4 In-Memory Virtual Diff Preview
- Extension registers `ibtrrs-diff://` scheme via `TextDocumentContentProvider`.
- Proposal content stored in memory mapped by request UUID.
- Diff shown via `vscode.commands.executeCommand('vscode.diff', targetUri, virtualUri, 'IBTRRS: Proposed Resolution')`.
- No temporary files created on disk; memory cleared on apply or reject.

### 4.5 Post-Fix Verification Settling (`verify.ts`)
- Verification uses an event-driven settling window:
  1. `doc.save()` triggered on apply.
  2. Subscribes to `vscode.languages.onDidChangeDiagnostics` for the target URI.
  3. Enforces a 600 ms debounce quiet-period (ceiling timeout: 8000 ms).
  4. Reports outcomes: `diagnostic_cleared`, `new_diagnostics`, `inconclusive`.

---

## 5. 6-Week Roadmap (Strict 7-Day Sprints)

| Week | Days | Phase Focus | Key Deliverables | Gate Milestone |
|---|---|---|---|---|
| **Week 1** | Days 1–7 | Foundation & Contracts | Threat model, privacy inventory, schemas, repo skeletons, CI green | **Gate 1** (Day 3 approved), Contract freeze (Day 7) |
| **Week 2** | Days 8–14 | Diagnostics, Rules & Corpus | `normalize.ts`, `extract.ts`, Rule 1 (unused import), 15–20 corpus records, safe index builder | **Gate 2** (Day 14) |
| **Week 3** | Days 15–21 | Backend & Retrieval | Search ranking + floor, prompt builder, fake & real LLM adapter, repair service | **Gate 3** (Day 21) |
| **Week 4** | Days 22–28 | Patching, Preview & Apply | Tolerant diff validator, AST dry-run, `ibtrrs-diff://` preview, approval state machine, stale check | **Gate 4** (Day 28: End-to-end flow) |
| **Week 5** | Days 29–35 | Verification & Hardening | Diagnostic settling listener, security-negative test suite, failure UX pass, runtime capture decision | **Gate 5** (Day 35) |
| **Week 6** | Days 36–42 | Evaluation & Packaging | Benchmark cases, retrieval ablation study, VSIX clean packaging, documentation & demo | **Gate 6** (Day 42: Release) |

