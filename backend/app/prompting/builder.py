"""
Prompt Builder
Constructs delimited prompts with trusted instructions and untrusted code blocks.
"""

from __future__ import annotations
from typing import List, Dict, Any


SYSTEM_PROMPT = """You are an automated software repair engine assisting a Python developer.
Your task is to analyze a Python diagnostic error and propose a minimal, safe, syntax-valid unified diff to resolve it.

RULES:
1. Output MUST be a single raw valid JSON object. Do not include markdown code block backticks (no ```json).
2. The JSON object must strictly have two string fields:
   - "explanation": Brief explanation of the root cause and repair rationale.
   - "unified_diff": Single-file unified diff targeting the relative file path provided.
3. The diff must modify only the provided bounded snippet. Never invent imports or touch outside files.
4. If you cannot produce a safe, certain resolution, return: {"explanation": "Cannot resolve safely", "unified_diff": ""}
"""


def build_repair_prompt(
    target_path: str,
    diagnostic: Dict[str, Any],
    bounded_snippet: str,
    examples: List[Dict[str, Any]]
) -> str:
    examples_str = ""
    if examples:
        examples_str += "\n=== RETRIEVED REPAIR EXAMPLES (FOR INSPIRATION ONLY) ===\n"
        for idx, ex in enumerate(examples, start=1):
            examples_str += (
                f"\n--- Example {idx} [{ex.get('record_id', '')}] ---\n"
                f"Diagnostic: {ex.get('diagnostic', {}).get('code', '')}: {ex.get('diagnostic', {}).get('message_pattern', '')}\n"
                f"Buggy Code:\n{ex.get('buggy_snippet', '')}\n"
                f"Fixed Code:\n{ex.get('fixed_snippet', '')}\n"
            )

    return f"""Target File: {target_path}
Diagnostic Source: {diagnostic.get('source')}
Diagnostic Code: {diagnostic.get('code')}
Diagnostic Message: {diagnostic.get('message')}

=== BEGIN UNTRUSTED USER CODE SNIPPET ===
{bounded_snippet}
=== END UNTRUSTED USER CODE SNIPPET ===
{examples_str}
Generate a minimal unified diff to fix the diagnostic above.
"""

