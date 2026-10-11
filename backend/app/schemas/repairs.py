"""
Pydantic Request and Response Schemas for IBTRRS API v1
"""

from __future__ import annotations
from typing import List, Optional, Literal
from pydantic import BaseModel, Field


class DiagnosticPosition(BaseModel):
    line: int = Field(..., ge=0, description="0-indexed line number")
    character: int = Field(..., ge=0, description="0-indexed character offset")


class DiagnosticRange(BaseModel):
    start: DiagnosticPosition
    end: DiagnosticPosition


class DiagnosticPayload(BaseModel):
    source: str = Field(..., example="pyright")
    code: str = Field(..., example="reportAttributeAccessIssue")
    message: str = Field(..., max_length=2048)
    severity: Literal["error", "warning", "information", "hint"]
    range: DiagnosticRange


class TargetPayload(BaseModel):
    workspace_relative_path: str = Field(
        ...,
        pattern=r"^(?!\/)(?!.*\.\.)[a-zA-Z0-9_\-\.\/]+$",
        description="Relative POSIX path within the workspace"
    )
    language_id: Literal["python"] = "python"


class DocumentPayload(BaseModel):
    version: int = Field(..., ge=0)
    content_sha256: str = Field(..., min_length=64, max_length=64)


class ContextPayload(BaseModel):
    start_line: int = Field(..., ge=0)
    end_line: int = Field(..., ge=0)
    text: str = Field(..., max_length=16384, description="Bounded source context snippet (max 16KB)")
    truncated: bool = False


class RepairOptions(BaseModel):
    allow_examples: bool = True
    max_examples: int = Field(default=3, ge=1, le=5)


class RepairRequest(BaseModel):
    api_version: Literal["v1"] = "v1"
    request_id: str = Field(..., description="UUIDv4 correlation identifier")
    language: Literal["python"] = "python"
    diagnostic: DiagnosticPayload
    target: TargetPayload
    document: DocumentPayload
    context: ContextPayload
    options: RepairOptions = Field(default_factory=RepairOptions)


class RetrievalExample(BaseModel):
    record_id: str
    score: float
    above_floor: bool


class RetrievalMetadata(BaseModel):
    status: Literal["used", "none", "retrieval_unavailable"]
    examples: List[RetrievalExample] = Field(default_factory=list)
    index_manifest_id: Optional[str] = None


class ValidationMetadata(BaseModel):
    result: Literal["accepted", "rejected"]
    checks: List[str]


class ErrorPayload(BaseModel):
    code: str
    message: str
    retryable: bool = False


class RepairResponse(BaseModel):
    api_version: Literal["v1"] = "v1"
    request_id: str
    status: Literal["proposal", "no_proposal"]
    strategy: Optional[Literal["retrieval_augmented_llm", "deterministic_rule"]] = None
    explanation: Optional[str] = None
    unified_diff: Optional[str] = None
    retrieval: Optional[RetrievalMetadata] = None
    validation: Optional[ValidationMetadata] = None
    verification: Optional[dict] = None
    error: Optional[ErrorPayload] = None


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded"]
    api_version: Literal["v1"] = "v1"
    index_manifest_id: Optional[str] = None
    records_indexed: int = 0

