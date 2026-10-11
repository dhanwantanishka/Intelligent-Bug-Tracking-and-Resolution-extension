# IBTRRS Threat Model (STRIDE)

## 1. Trust Boundaries
- **TB-1: Workspace / Editor $\leftrightarrow$ Extension:** Workspace files are untrusted inputs. File contents, malicious comments, or crafted diagnostic messages must not trigger arbitrary code execution in the extension host.
- **TB-2: Extension $\leftrightarrow$ Backend:** Loopback HTTP connection (`127.0.0.1`). Protected by bearer token generated at backend startup with restrictive OS ACLs (`0600` on POSIX, User profile ACL on Windows).
- **TB-3: Backend $\leftrightarrow$ LLM Provider:** Remote HTTPS. Only bounded context, relative path, and diagnostic text cross this boundary. Provider output is treated as untrusted text.
- **TB-4: Corpus & Index Artifacts $\leftrightarrow$ Backend:** Read-only data files. Safe JSON + SciPy NPZ format (no Python `pickle`/`joblib`). Manifest SHA-256 integrity verified at startup.

---

## 2. Threat Analysis (STRIDE)

| Category | Threat Description | Asset Impacted | Mitigation Strategy | Residual Risk |
|---|---|---|---|---|
| **Spoofing** | Unauthorized local process accesses backend API | Backend API / LLM tokens | Random 256-bit bearer token file with strict user-only read permissions; loopback bind only. | Low (compromise of user account could read token). |
| **Tampering** | Model returns patch touching files outside target or workspace | Workspace integrity | Strict target identity check (`+++ b/path` == `target.path`); rejection of `..` and absolute paths in both backend and extension. | Low. Human preview and approval always required. |
| **Tampering** | Model output executes code during deserialization | Backend / Extension runtime | Rejection of `joblib`/`pickle` (ADR-010). Model output parsed strictly as JSON and validated with Pydantic. | Zero. |
| **Repudiation** | User denies applying a breaking patch | Developer accountability | Changes applied exclusively via VS Code `WorkspaceEdit` on explicit button click; undoable via standard VS Code undo stack. | Low. |
| **Information Disclosure** | Leakage of workspace code or credentials | Source code, API keys | Bounded context ($\le 200$ lines); absolute paths stripped; provider API keys stored only on backend; zero logging of code/prompts. | Low (only user-selected snippet leaves machine). |
| **Denial of Service** | Oversized payloads or runaway LLM generation hangs editor | Extension responsiveness | Backend body limit (64 KB); context limit (16 KB); client HTTP timeout (30 s); provider timeout (25 s); async cancellation. | Low. |
| **Elevation of Privilege** | Prompt injection via crafted comments steers model to output malicious diff | Workspace files | Delimited prompt structure; model has no tool-use or shell access; output parsed strictly as diff; mandatory diff preview and human approval. | Low (human review remains final safeguard). |

