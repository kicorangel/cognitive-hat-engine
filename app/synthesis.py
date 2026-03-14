from typing import Dict, Any, List, Tuple

from .prompts import ROLES


def _collect_hat_text(state: Dict[str, Any], hat: str) -> str:
    outputs = state.get("outputs", {}).get(hat, {})
    chunks = []
    for role in ROLES:
        role_items = outputs.get(role, [])
        if not role_items:
            continue
        last = role_items[-1]
        chunks.append(f"{role}:\n{last.get('content','')}".strip())
    return "\n\n".join(chunks)


def synthesize_blue_hat_without_llm(state: Dict[str, Any]) -> Tuple[str, Dict[str, str], str, str]:
    """
    Fallback synthesis if you're running mock mode.
    """
    executive_summary = (
        "Mock synthesis: configure OPENAI_API_KEY for real outputs. "
        "This pack shows the full structure and flow."
    )
    options = {
        "A": "Build MVP with 3 hats (WHITE/YELLOW/BLACK) + BLUE summary, 6 roles, no memory.",
        "B": "Add GREEN + Auditor, basic persistence, minimal evaluation.",
        "C": "Full system: loops for missing data, conflict arbitration, memory per project, dashboards.",
    }
    recommendation = "A (start small), then evolve to B once inputs/outputs are stable."
    confidence = "low"
    return executive_summary, options, recommendation, confidence


def build_blue_hat_prompt(state: Dict[str, Any]) -> str:
    idea = state.get("idea", "")
    objective = state.get("objective", "")
    constraints = state.get("constraints", {}) or {}
    success = state.get("success_criteria", []) or []
    context = state.get("context", {}) or {}

    constraints_txt = ", ".join([f"{k}={v}" for k, v in constraints.items()]) or "none"
    success_txt = "; ".join(success) or "none"
    context_txt = ", ".join([f"{k}={v}" for k, v in context.items()]) or "none"

    white = _collect_hat_text(state, "WHITE")
    yellow = _collect_hat_text(state, "YELLOW")
    black = _collect_hat_text(state, "BLACK")
    green = _collect_hat_text(state, "GREEN")
    red = _collect_hat_text(state, "RED")

    return f"""
You are the Blue Hat Coordinator. You must synthesize a structured strategic conclusion.

Brief:
- Idea: {idea}
- Objective: {objective}
- Constraints: {constraints_txt}
- Success criteria: {success_txt}
- Context: {context_txt}

Inputs from hats (per role):
[WHITE]
{white}

[YELLOW]
{yellow}

[BLACK]
{black}

[GREEN]
{green}

[RED]
{red}

Return STRICT JSON only with:
- executive_summary: string (<= 10 lines)
- options: object with keys A, B, C (each a concise option)
- recommendation: string (choose A/B/C and justify in 2-4 lines)
- decision_confidence: one of ["high","medium","low"]
- next_steps: array of strings (5-10 items)
- experiments: array of strings (0-6 items)
- metrics: array of strings (3-8 items)
- contradictions: array of strings (0-8 items)  # consolidate main tensions
- tradeoffs: array of strings (0-8 items)      # explicit trade-offs
""".strip()
