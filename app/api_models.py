from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class ThinkingRole(BaseModel):
    code: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    title: Optional[str] = None
    profile: str = Field(..., min_length=10)


class AnalyzeRequest(BaseModel):
    idea: str = Field(..., min_length=5)
    roles: Optional[List[ThinkingRole]] = None


class AnalyzeResponse(BaseModel):
    run_id: str
    mode: str  # "mock" or "llm"
    final_hat: str
    executive_summary: str
    options: Dict[str, str]
    recommendation: str
    decision_confidence: str

    # audit payload
    state: Dict