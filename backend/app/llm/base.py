"""
LLM Provider Protocol and Deterministic Fake Provider
"""

from __future__ import annotations
from typing import Protocol, List, Dict, Any, Optional
import json


class LLMProvider(Protocol):
    async def generate_resolution(
        self,
        system_instruction: str,
        user_prompt: str,
        temperature: float = 0.0
    ) -> str:
        """Generates raw text response matching expected JSON schema."""
        ...


class FakeLLMProvider:
    """
    Deterministic provider for automated testing and CI.
    Generates verifiable unified diffs without making external network calls.
    """
    def __init__(self, should_fail: bool = False, malformed: bool = False):
        self.should_fail = should_fail
        self.malformed = malformed

    async def generate_resolution(
        self,
        system_instruction: str,
        user_prompt: str,
        temperature: float = 0.0
    ) -> str:
        if self.should_fail:
            raise RuntimeError("Provider connection timeout simulated")

        if self.malformed:
            return "Here is your fix: please replace the code..."

        # Deterministic valid response
        payload = {
            "explanation": "Guard against None before attribute access to satisfy static typing.",
            "unified_diff": (
                "--- a/tokens.py\n"
                "+++ b/tokens.py\n"
                "@@ -1,3 +1,5 @@\n"
                " def clean(val):\n"
                "-    return val.strip()\n"
                "+    if val is None:\n"
                "+        return \"\"\n"
                "+    return val.strip()\n"
            )
        }
        return json.dumps(payload)

