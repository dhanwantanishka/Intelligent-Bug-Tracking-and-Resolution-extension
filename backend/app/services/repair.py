"""
Repairs Orchestration Service
Coordinates retrieval, prompt construction, LLM adapter call, and patch validation.
"""

from __future__ import annotations
import json
import re
from typing import Dict, Any, Optional
from app.config import settings
from app.schemas.repairs import (
    RepairRequest,
    RepairResponse,
    RetrievalMetadata,
    RetrievalExample,
    ValidationMetadata,
    ErrorPayload
)
from app.retrieval.index import IndexEngine
from app.prompting.builder import SYSTEM_PROMPT, build_repair_prompt
from app.llm.base import FakeLLMProvider
from app.patch.validate import validate_and_apply_patch, PatchValidationError

# Global index engine instance
index_engine = IndexEngine(settings.ARTIFACTS_DIR)
fake_llm = FakeLLMProvider()


def extract_json_payload(raw_text: str) -> Dict[str, Any]:
    cleaned = raw_text.strip()
    # Strip markdown backticks if returned
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\n?", "", cleaned)
        cleaned = re.sub(r"\n?```$", "", cleaned)
    
    # Extract outer balanced braces
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if match:
        cleaned = match.group(0)
    return json.loads(cleaned)


async def orchestrate_repair(req: RepairRequest) -> RepairResponse:
    # 1. Retrieval
    examples = []
    retrieval_status = "none"
    retrieval_meta = RetrievalMetadata(status="none")

    if req.options.allow_examples and index_engine.is_loaded:
        query_text = f"{req.diagnostic.code} {req.diagnostic.message} {req.context.text}"
        ranked = index_engine.query(
            query_text=query_text,
            top_k=req.options.max_examples,
            relevance_floor=settings.RELEVANCE_FLOOR
        )
        if ranked:
            retrieval_status = "used"
            examples = [r[0] for r in ranked]
            retrieval_meta = RetrievalMetadata(
                status="used",
                examples=[
                    RetrievalExample(
                        record_id=r[0]["record_id"],
                        score=r[1],
                        above_floor=True
                    ) for r in ranked
                ],
                index_manifest_id=index_engine.manifest.get("manifest_version", "1.0")
            )

    # 2. Prompt Generation
    user_prompt = build_repair_prompt(
        target_path=req.target.workspace_relative_path,
        diagnostic=req.diagnostic.dict(),
        bounded_snippet=req.context.text,
        examples=examples
    )

    # 3. LLM Generation
    try:
        raw_response = await fake_llm.generate_resolution(
            system_instruction=SYSTEM_PROMPT,
            user_prompt=user_prompt
        )
        parsed = extract_json_payload(raw_response)
    except Exception as e:
        return RepairResponse(
            request_id=req.request_id,
            status="no_proposal",
            error=ErrorPayload(
                code="llm_unavailable",
                message=f"Model failed to generate valid output: {str(e)}",
                retryable=True
            )
        )

    explanation = parsed.get("explanation", "")
    diff_str = parsed.get("unified_diff", "")

    if not diff_str:
        return RepairResponse(
            request_id=req.request_id,
            status="no_proposal",
            explanation=explanation,
            error=ErrorPayload(
                code="no_repair_produced",
                message="Model determined no safe patch could be generated.",
                retryable=False
            )
        )

    # 4. Patch Validation & AST Dry Run
    try:
        val_result = validate_and_apply_patch(
            diff_str=diff_str,
            target_posix_path=req.target.workspace_relative_path,
            bounded_snippet=req.context.text
        )
    except PatchValidationError as e:
        return RepairResponse(
            request_id=req.request_id,
            status="no_proposal",
            explanation=explanation,
            validation=ValidationMetadata(
                result="rejected",
                checks=[e.code]
            ),
            error=ErrorPayload(
                code=e.code,
                message=e.message,
                retryable=False
            )
        )

    return RepairResponse(
        request_id=req.request_id,
        status="proposal",
        strategy="retrieval_augmented_llm",
        explanation=explanation,
        unified_diff=diff_str,
        retrieval=retrieval_meta,
        validation=ValidationMetadata(
            result="accepted",
            checks=val_result["checks_passed"]
        ),
        verification=None,
        error=None
    )

