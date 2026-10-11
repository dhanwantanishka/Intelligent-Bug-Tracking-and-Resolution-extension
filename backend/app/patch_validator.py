"""
IBTRRS Tolerant Patch Validator
Applies AST syntax checks, context sliding-window relocation, and bounds enforcement.
"""

from __future__ import annotations
import ast
import re
from typing import Dict, Any, List, Optional, Tuple


class PatchValidationError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


def normalize_posix_path(raw_path: str) -> str:
    """Normalize path to POSIX relative form, stripping Windows backslashes and prefixes."""
    clean = raw_path.replace("\\", "/").strip()
    if clean.startswith("a/") or clean.startswith("b/"):
        clean = clean[2:]
    # Strip any leading slashes or dots
    clean = re.sub(r"^(\./|/)+", "", clean)
    if ".." in clean.split("/"):
        raise PatchValidationError("path_traversal", "Path traversal elements ('..') are forbidden")
    return clean


def parse_unified_diff(diff_str: str) -> Tuple[str, str, List[Tuple[int, int, List[str], List[str]]]]:
    """
    Parses single-file unified diff.
    Returns (orig_path, new_path, hunks) where each hunk has (old_start, old_lines, del_lines, add_lines).
    """
    lines = diff_str.strip().splitlines()
    orig_path: Optional[str] = None
    new_path: Optional[str] = None
    hunks = []

    for line in lines:
        if line.startswith("--- "):
            orig_path = normalize_posix_path(line[4:].strip())
        elif line.startswith("+++ "):
            new_path = normalize_posix_path(line[4:].strip())

    if not orig_path or not new_path:
        raise PatchValidationError("malformed_diff", "Diff missing '---' or '+++' file headers")
    if orig_path != new_path:
        raise PatchValidationError("multi_file_diff", "Diff modifies multiple files or renames target")

    # Parse hunks
    hunk_header_re = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")
    current_hunk = None

    for line in lines:
        match = hunk_header_re.match(line)
        if match:
            old_start = int(match.group(1))
            old_lines = int(match.group(2) or 1)
            current_hunk = (old_start, old_lines, [], [])
            hunks.append(current_hunk)
            continue
        
        if current_hunk is not None:
            if line.startswith("-"):
                current_hunk[2].append(line[1:])
            elif line.startswith("+"):
                current_hunk[3].append(line[1:])
            elif line.startswith(" "):
                current_hunk[2].append(line[1:])
                current_hunk[3].append(line[1:])

    if not hunks:
        raise PatchValidationError("no_hunks", "No valid hunks found in unified diff")

    return orig_path, new_path, hunks


def validate_and_apply_patch(
    diff_str: str,
    target_posix_path: str,
    bounded_snippet: str,
    max_hunk_lines: int = 50
) -> Dict[str, Any]:
    """
    Validates patch target identity, line bounds, applies changes in dry-run,
    and runs AST validation on the resulting code.
    """
    orig_path, new_path, hunks = parse_unified_diff(diff_str)
    
    # 1. Target Identity Check
    expected_norm = normalize_posix_path(target_posix_path)
    if new_path != expected_norm:
        raise PatchValidationError(
            "target_path_mismatch",
            f"Diff target '{new_path}' does not match expected target '{expected_norm}'"
        )

    snippet_lines = bounded_snippet.splitlines()

    # 2. Tolerant context matching & replacement
    current_lines = list(snippet_lines)
    for old_start, _, del_lines, add_lines in hunks:
        if len(del_lines) > max_hunk_lines or len(add_lines) > max_hunk_lines:
            raise PatchValidationError(
                "patch_size_exceeded",
                f"Hunk exceeds maximum permitted size of {max_hunk_lines} lines"
            )

        # Attempt exact match at hunk offset first
        match_idx = -1
        del_block = "\n".join(del_lines)

        # Sliding window fallback to handle LLM line-number hallucination
        for i in range(len(current_lines) - len(del_lines) + 1):
            window = "\n".join(current_lines[i:i + len(del_lines)])
            if window == del_block:
                match_idx = i
                break

        if match_idx == -1:
            raise PatchValidationError(
                "context_text_mismatch",
                "Hunk context lines do not match target source lines in bounded snippet"
            )

        # Apply replacement
        current_lines[match_idx:match_idx + len(del_lines)] = add_lines

    modified_snippet = "\n".join(current_lines)

    # 3. Dry-Run AST Syntax Validation
    try:
        ast.parse(modified_snippet)
    except SyntaxError as e:
        raise PatchValidationError(
            "dry_run_syntax_error",
            f"Modified code fails Python AST syntax parsing: {e.msg} at line {e.lineno}"
        )

    return {
        "status": "accepted",
        "target_path": expected_norm,
        "modified_snippet": modified_snippet,
        "checks_passed": [
            "single_file",
            "target_path_match",
            "context_match_verified",
            "patch_size_ok",
            "ast_syntax_valid"
        ]
    }
