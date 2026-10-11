# IBTRRS Privacy Inventory and Data Lifecycle (v1.0)

## 1. Principles
1. **Bounded context:** Never read or transmit full files beyond the diagnostic window ($\le 200$ lines, $\le 16$ KB).
2. **Explicit consent:** Remote AI assistance is **disabled by default**. Transmitting code to an LLM provider requires explicit user configuration and toggle in VS Code settings.
3. **Redacted logs:** Source code, diagnostics, prompts, and tokens are never logged to disk or console. Only anonymized metadata (request IDs, timings, error codes) is logged.
4. **Zero telemetry:** No usage tracking, metrics collection, or analytics sent to external servers.

---

## 2. Data Inventory Table

| Data Element | Bounded / Raw | Leaves Machine? | Destination | Retention | Redaction / Protection |
|---|---|---|---|---|---|
| **Source Context** | Bounded ($\le 200$ lines, $\le 16$ KB) | Yes, when AI enabled | Backend (loopback) $\to$ Configured LLM provider | Ephemeral in-memory during request; not stored on disk | Never written to logs |
| **Diagnostic Details** | Source, code, message, range | Yes, when AI enabled | Backend $\to$ LLM provider | Ephemeral | Message sanitized of local file paths |
| **File Path** | Relative POSIX path | Yes (relative only) | Backend $\to$ LLM provider | Ephemeral | Absolute system paths are stripped |
| **Document Content Hash** | SHA-256 | Yes | Backend $\to$ Client (stale check) | Ephemeral | Safe 64-char hex string |
| **Proposed Patch** | Unified diff | No (returns to client) | Client memory (`ibtrrs-diff://`) | Memory only; discarded on reject/apply | Rendered in virtual editor |
| **Bearer Token** | 256-bit random string | Loopback only | Extension HTTP client | Local file with 0600 / ACL user permissions | Redacted in logs (`Bearer [REDACTED]`) |
| **LLM Provider API Key** | Secrets | No (Backend env/keychain only) | Backend process memory | Never sent to extension or logged | Masked in config validation |

---

## 3. User Controls
- `ibtrrs.ai.enabled` (Boolean, default `false`): Must be set to `true` by user before any request is sent to the backend.
- `ibtrrs.backend.url` (String, default `http://127.0.0.1:8000`): Allows configuring local loopback or custom backend instance.
- `ibtrrs.clearSessionHistory` (Command): Wipes any in-memory diagnostic logs and cached virtual diff proposals.

