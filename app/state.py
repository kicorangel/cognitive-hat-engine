from typing import TypedDict, Dict, List, Optional, Any


HAT = str
ROLE = str


class RoleOutput(TypedDict):
    role: str
    hat: str
    content: str
    confidence: Optional[str]
    assumptions: List[str]
    questions: List[str]


class CognitiveState(TypedDict, total=False):
    # Meta
    run_id: str
    mode: str  # "mock" or "llm"

    # A. Context
    idea: str
    objective: str
    constraints: Dict[str, str]
    success_criteria: List[str]
    context: Dict[str, str]
    interpreted_brief: str

    # B. Cognitive control
    current_hat: str
    hat_sequence: List[str]
    hat_index: int
    hat_history: List[str]
    iteration: int

    # C. Outputs per hat and role
    outputs: Dict[HAT, Dict[ROLE, List[RoleOutput]]]

    # D. Emergent knowledge
    assumptions: List[str]
    open_questions: List[str]
    risks: List[str]
    opportunities: List[str]
    alternatives: List[str]

    # E. Tensions
    contradictions: List[str]
    tradeoffs: List[str]

    # F. Final synthesis
    executive_summary: Optional[str]
    options: Optional[Dict[str, str]]
    recommendation: Optional[str]
    decision_confidence: Optional[str]
    next_steps: Optional[List[str]]
    experiments: Optional[List[str]]
    metrics: Optional[List[str]]

    # Runtime config
    max_bullets: int
    include_red_hat: bool

    # Debug
    debug: Dict[str, Any]
