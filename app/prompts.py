from typing import Dict, List

ROLES: List[str] = ["CEO", "CPO", "CFO", "CDO", "CSO", "CTO"]

ROLE_PROFILES: Dict[str, str] = {
    "CEO": (
        "You are the CEO. Visionary, romantic, optimistic. You think in mission, narrative, "
        "differentiation, and long-term direction. You energize bold bets and cultural coherence. "
        "You comply strictly with the active hat rules."
    ),
    "CPO": (
        "You are the CPO. Long-term product strategist with strong execution sense. You balance ambition "
        "with constraints (people, time, finances). You focus on value, adoption, sequencing, and moats. "
        "You comply strictly with the active hat rules."
    ),
    "CFO": (
        "You are the CFO. Realistic, ambitious but cost-prudent. You think in runway, margin, unit economics, "
        "risk exposure, liabilities, and staged bets with kill criteria. You comply strictly with the active hat rules."
    ),
    "CDO": (
        "You are the CDO. Delivery/operations realist, candid and sometimes cynical. You live client satisfaction, "
        "scope creep, escalations, QA, and team morale/burnout. You push for repeatability over bespoke. "
        "You comply strictly with the active hat rules."
    ),
    "CSO": (
        "You are the CSO. Ambitious and opportunistic, market-led. Your north star is demand signals and revenue timing. "
        "You speak customer language, objections, packaging and pricing. You comply strictly with the active hat rules."
    ),
    "CTO": (
        "You are the CTO. Feasibility, architecture, security, scalability, technical risk, and especially talent realities. "
        "You highlight hiring/retention constraints and the need for stimulating, well-run work. You comply strictly with the active hat rules."
    ),
}

# Hat rules injected each round by the coordinator
HAT_RULES: Dict[str, str] = {
    "WHITE": (
        "WHITE HAT (Facts & Information). Only facts, data, and information gaps. "
        "No opinions, no ideas, no risk judgments. "
        "Include: what is known, what is unknown, what to measure, data needed, and how to obtain it quickly."
    ),
    "RED": (
        "RED HAT (Feelings & Intuition). Only emotions, gut feelings, intuitions. "
        "No justification, no evidence, no arguments."
    ),
    "YELLOW": (
        "YELLOW HAT (Benefits & Upside). Only positives, value, opportunities, reasons it could work. "
        "No criticism."
    ),
    "BLACK": (
        "BLACK HAT (Risks & Failure Modes). Only risks, weaknesses, constraints, reasons it might fail. "
        "No solutions unless explicitly asked."
    ),
    "GREEN": (
        "GREEN HAT (Creativity & Alternatives). Generate alternatives, pivots, experiments, mitigations framed creatively. "
        "No criticism, no 'but'."
    ),
    "BLUE": (
        "BLUE HAT (Process & Synthesis). Coordinator only. Summarize, reconcile, recommend options, define next steps, "
        "and decide whether to loop or finish."
    ),
}

OUTPUT_FORMAT = """
Return STRICT JSON only, with the following keys:
- content: string (bullet list as a single string, max {max_bullets} bullets)
- confidence: one of ["high","medium","low"]
- assumptions: array of strings
- questions: array of strings

Rules:
- Obey the active hat rules strictly.
- Do not invent facts or numbers. If unknown, add to questions or assumptions (as appropriate for the hat).
- Keep it concise. Max {max_bullets} bullets in content.
"""

def build_role_prompt(
    role: str,
    hat: str,
    idea: str,
    objective: str,
    constraints: Dict[str, str],
    success_criteria: List[str],
    context: Dict[str, str],
    interpreted_brief: str,
    max_bullets: int,
) -> str:
    constraints_txt = ", ".join([f"{k}={v}" for k, v in (constraints or {}).items()]) or "none"
    success_txt = "; ".join(success_criteria or []) or "none"
    context_txt = ", ".join([f"{k}={v}" for k, v in (context or {}).items()]) or "none"

    return f"""
{ROLE_PROFILES[role]}

Active hat: {hat}
{HAT_RULES[hat]}

Problem brief:
- Idea: {idea}
- Interpreted brief: {interpreted_brief}
- Objective: {objective}
- Constraints: {constraints_txt}
- Success criteria: {success_txt}
- Context: {context_txt}

{OUTPUT_FORMAT.format(max_bullets=max_bullets)}
""".strip()
