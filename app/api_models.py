from typing import Dict
from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    idea: str = Field(..., min_length=5)


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
