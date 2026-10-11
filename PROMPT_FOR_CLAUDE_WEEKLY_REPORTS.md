# Prompt for Claude: Generate 4 Weekly Progress Reports (Week 1 to Week 4)

> **Instructions for the User:** Copy and paste the prompt below into Claude. It provides all necessary architectural context, technical specifications, and the exact structure required to generate comprehensive, professional progress reports for Weeks 1 through 4 of the IBTRRS project.

---

```markdown
# Prompt for Claude

You are an expert Lead Software Architect and Technical Program Manager. 

Please generate a detailed, professional, and audit-ready **4-Week Progress Report (Week 1 through Week 4)** for our project: **IBTRRS (Intelligent Bug Tracking and Resolution Recommendation System)**.

---

### Project Context & Baseline Architecture

1. **Product Summary:**
   - A VS Code extension (TypeScript) for Python developers backed by a local FastAPI service (Python).
   - Converts Python diagnostics (from Pyright/Pylance and Ruff) into either safe local deterministic Quick Fixes or reviewed, AI-proposed unified diffs with human-in-the-loop preview and post-fix verification.
   - Built under a strict **6-week single-engineer constraint** (42 days) with high security, privacy invariants, and zero arbitrary code execution.
   - Primary workspace location: `C:\Users\dhanw\Intelligent Bug Tracking`.

2. **Core Architectural Highlights & Decisions (ADRs):**
   - **Gate 1 Approval:** Blueprint v0.2 accepted.
   - **Deterministic vs. AI Separation:** Local rules execute instantly without network overhead; AI proposals are never returned as raw Quick Fixes and always require explicit side-by-side diff review.
   - **ADR-010 (Safe Index Serialization):** Scikit-learn's `joblib`/`pickle` was rejected due to Arbitrary Code Execution (ACE) risks. Replaced by `vocab.json` + `idf.json` + `matrix.npz` (SciPy/NumPy) + SHA-256 `manifest.json`.
   - **Cross-Platform POSIX Normalization:** All file targets and diff headers enforce workspace-relative POSIX paths (`/`), preventing Windows backslash mismatches.
   - **Tolerant Diff Validation:** Sliding-window context matching handles LLM line-number drift without failing valid fixes, backed by dry-run `ast.parse()` Python syntax verification.
   - **In-Memory Diff Previews:** Native `vscode.diff` powered by an in-memory `ibtrrs-diff://` virtual document provider (zero temporary files written to disk).
   - **Post-Fix Verification Settling:** Event-driven listener on `vscode.languages.onDidChangeDiagnostics` with a 600 ms debounce window and 8000 ms ceiling to resolve language server race conditions.
   - **Privacy by Design:** Bounded context window (≤ 200 lines, ≤ 16 KB), AI disabled by default in settings, zero telemetry, no source code in logs.

---

### Instructions for Report Generation

Please generate **four distinct weekly reports** (Week 1, Week 2, Week 3, Week 4). Each weekly report must follow this standard engineering structure:

1. **Executive Summary & Milestone Status:**
   - Period dates (e.g., Week 1 = Days 1–7, Week 2 = Days 8–14, Week 3 = Days 15–21, Week 4 = Days 22–28).
   - Review Gate outcome (Gate 1 for Week 1, Gate 2 for Week 2, Gate 3 for Week 3, Gate 4 for Week 4).
   - High-level status (On Track / Ahead / Mitigated).

2. **Key Objectives & Deliverables Completed:**
   - Specific modules, scripts, schemas, and tests completed during the sprint.
   - Reference exact file paths where appropriate (e.g., `docs/blueprint_v0.2.md`, `index/build.py`, `backend/app/patch/validate.py`, `extension/src/extension.ts`).

3. **Technical Deep-Dive / Architecture Decisions Highlight:**
   - Technical challenges encountered during that specific week and how they were solved (e.g., safe serialization in Week 2, prompt delimiters and fake providers in Week 3, tolerant diff matching and virtual diff preview in Week 4).

4. **Testing, Verification & Quality Assurance:**
   - Tests run, pass rates, CI checks, security/boundary validation.

5. **Risks, Blockers & Mitigations:**
   - Scope management, trade-offs made, fallbacks ready.

6. **Next Week's Outlook:**
   - Immediate priorities entering the next sprint.

---

### Roadmap Milestones for Reference

- **Week 1 (Days 1–7): Foundation, Threat Model & Contracts (Gate 1)**
  - Blueprint v0.2, STRIDE Threat Model (`docs/threat-model.md`), Privacy Inventory (`docs/privacy-inventory.md`), JSON Schema v1.0 (`corpus/schema/record.schema.json`), Pydantic models (`backend/app/schemas/repairs.py`), and CI skeleton (`.github/workflows/ci.yml`).

- **Week 2 (Days 8–14): Diagnostics, Rules, Corpus & Safe Index (Gate 2)**
  - Diagnostic normalization (`normalize.ts`), bounded context extractor (`extract.ts`), first deterministic rule (`unused-import.ts`), seed corpus records (`records.jsonl`), corpus validator (`corpus/validate.py`), and safe non-pickle index builder (`index/build.py`).

- **Week 3 (Days 15–21): Backend Services, Retrieval & LLM Protocol (Gate 3)**
  - TF-IDF search engine with cosine ranking and relevance floor (`app/retrieval/index.py`), prompt builder (`app/prompting/builder.py`), LLMProvider protocol & deterministic test adapter (`app/llm/base.py`), bearer token auth (`app/auth.py`), and repairs orchestration service (`app/services/repair.py`).

- **Week 4 (Days 22–28): Patching, Virtual Preview & Approval Loop (Gate 4)**
  - Tolerant diff validator with sliding-window matching and `ast.parse()` (`app/patch/validate.py`), virtual diff provider (`diffProvider.ts`), document staleness check (`stale.ts`), post-fix settling listener (`verify.ts`), and end-to-end extension integration in `extension.ts`.

---

Please write the complete, polished reports in clean Markdown with clear headings, tables, and metric breakdowns.
```

