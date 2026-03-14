from typing import Dict, Any, Literal

from langgraph.graph import StateGraph, END

from .state import CognitiveState
from .llm import LLMClient
from .prompts import ROLES, build_role_prompt
from .utils import ensure_outputs_bucket, uniq_extend
from .synthesis import build_blue_hat_prompt, synthesize_blue_hat_without_llm
from .settings import DEFAULT_HAT_SEQUENCE


def init_state(state: Dict[str, Any]) -> Dict[str, Any]:
    state.setdefault("hat_history", [])
    state.setdefault("iteration", 0)
    state.setdefault("hat_index", 0)
    state.setdefault("outputs", {})
    state.setdefault("assumptions", [])
    state.setdefault("open_questions", [])
    state.setdefault("risks", [])
    state.setdefault("opportunities", [])
    state.setdefault("alternatives", [])
    state.setdefault("contradictions", [])
    state.setdefault("tradeoffs", [])
    state.setdefault("debug", {})
    state.setdefault("max_bullets", 5)
    state.setdefault("include_red_hat", False)
    state.setdefault("objective", "")
    state.setdefault("constraints", {})
    state.setdefault("success_criteria", [])
    state.setdefault("context", {})
    state.setdefault("interpreted_brief", "")


    hats = state.get("hat_sequence") or DEFAULT_HAT_SEQUENCE
    if state.get("include_red_hat") and "RED" not in hats:
        # inject RED before BLUE by default
        hats = [h for h in hats if h != "BLUE"] + ["RED", "BLUE"]
    state["hat_sequence"] = hats

    # set initial hat
    state["current_hat"] = hats[0] if hats else "BLUE"
    return state

def interpret_brief(state: Dict[str, Any]) -> Dict[str, Any]:
    llm = LLMClient()
    state["mode"] = llm.mode

    idea = state.get("idea", "")

    if llm.mode == "mock":
        state["objective"] = "Clarify the strategic opportunity and define an MVP path."
        state["constraints"] = {"inferred": "No explicit constraints provided yet."}
        state["success_criteria"] = ["Clear recommendation", "Actionable next steps"]
        state["context"] = {"inferred": "Context not explicitly provided."}
        state["interpreted_brief"] = (
            "The user has provided a strategic idea in free text. "
            "The system should infer likely objectives, constraints, and success criteria, "
            "then analyze the idea through the configured roles and hats."
        )
        return state

    prompt = f"""
You are the Blue Hat pre-processor for a strategic multi-agent system.

Your task is to interpret the user's raw idea and transform it into an internal structured brief
that other agents can use for analysis.

User idea:
{idea}

Return STRICT JSON only with:
- objective: string
- constraints: object with string values
- success_criteria: array of strings
- context: object with string values
- interpreted_brief: string

Rules:
- Infer only what is reasonable from the idea.
- Do not over-specify.
- If something is unclear, keep it general and conservative.
- The interpreted_brief should be concise but useful for downstream reasoning.
""".strip()

    data = llm.generate_json(prompt)

    state["objective"] = str(data.get("objective", "")).strip()
    state["constraints"] = data.get("constraints") or {}
    state["success_criteria"] = data.get("success_criteria") or []
    state["context"] = data.get("context") or {}
    state["interpreted_brief"] = str(data.get("interpreted_brief", "")).strip()

    return state


def run_hat_round(state: Dict[str, Any]) -> Dict[str, Any]:
    llm = LLMClient()
    state["mode"] = llm.mode

    hat = state["current_hat"]
    if hat == "BLUE":
        return state

    for role in ROLES:
        prompt = build_role_prompt(
            role=role,
            hat=hat,
            idea=state["idea"],
            interpreted_brief=state.get("interpreted_brief", ""),
            objective=state.get("objective", ""),
            constraints=state.get("constraints", {}),
            success_criteria=state.get("success_criteria", []),
            context=state.get("context", {}),
            max_bullets=int(state.get("max_bullets", 5)),
        )
        data = llm.generate_json(prompt)

        ensure_outputs_bucket(state["outputs"], hat, role)

        role_output = {
            "role": role,
            "hat": hat,
            "content": str(data.get("content", "")).strip(),
            "confidence": data.get("confidence"),
            "assumptions": data.get("assumptions") or [],
            "questions": data.get("questions") or [],
        }
        state["outputs"][hat][role].append(role_output)

        # Consolidate emergent knowledge (light-touch; we do deeper consolidation in BLUE)
        uniq_extend(state["assumptions"], role_output["assumptions"])
        uniq_extend(state["open_questions"], role_output["questions"])

        # Optionally route some items into category buckets based on hat
        if hat == "BLACK":
            # treat content bullets as candidate risks (rough)
            uniq_extend(state["risks"], _bullets_to_items(role_output["content"]))
        elif hat == "YELLOW":
            uniq_extend(state["opportunities"], _bullets_to_items(role_output["content"]))
        elif hat == "GREEN":
            uniq_extend(state["alternatives"], _bullets_to_items(role_output["content"]))

    state["hat_history"].append(hat)
    return state


def _bullets_to_items(text: str) -> list[str]:
    lines = [l.strip() for l in (text or "").splitlines()]
    items = []
    for l in lines:
        l = l.lstrip("-•* ").strip()
        if l:
            items.append(l)
    return items[:10]


def blue_hat_synthesis(state: Dict[str, Any]) -> Dict[str, Any]:
    llm = LLMClient()
    state["mode"] = llm.mode

    if llm.mode == "mock":
        executive_summary, options, recommendation, confidence = synthesize_blue_hat_without_llm(state)
        state["executive_summary"] = executive_summary
        state["options"] = options
        state["recommendation"] = recommendation
        state["decision_confidence"] = confidence
        state["current_hat"] = "BLUE"
        return state

    prompt = build_blue_hat_prompt(state)
    data = llm.generate_json(prompt)

    state["executive_summary"] = str(data.get("executive_summary", "")).strip()
    state["options"] = data.get("options") or {"A": "", "B": "", "C": ""}
    state["recommendation"] = str(data.get("recommendation", "")).strip()
    state["decision_confidence"] = data.get("decision_confidence", "medium")
    state["next_steps"] = data.get("next_steps") or []
    state["experiments"] = data.get("experiments") or []
    state["metrics"] = data.get("metrics") or []
    state["contradictions"] = data.get("contradictions") or state.get("contradictions", [])
    state["tradeoffs"] = data.get("tradeoffs") or state.get("tradeoffs", [])

    state["current_hat"] = "BLUE"
    return state


def advance_hat(state: Dict[str, Any]) -> Dict[str, Any]:
    hats = state.get("hat_sequence") or DEFAULT_HAT_SEQUENCE
    idx = int(state.get("hat_index", 0))

    # If current hat just ran, move on
    idx += 1
    state["hat_index"] = idx

    if idx >= len(hats):
        state["current_hat"] = "BLUE"
        return state

    state["current_hat"] = hats[idx]
    return state


def should_continue(state: Dict[str, Any]) -> Literal["RUN", "BLUE", "END"]:
    hat = state.get("current_hat")
    if hat == "BLUE":
        return "BLUE"
    return "RUN"


def build_graph():
    g = StateGraph(CognitiveState)

    g.add_node("init", init_state)
    g.add_node("run_hat_round", run_hat_round)
    g.add_node("advance_hat", advance_hat)
    g.add_node("blue_hat", blue_hat_synthesis)
    g.add_node("interpret_brief", interpret_brief)

    g.set_entry_point("init")
    g.add_edge("init", "interpret_brief")
    g.add_edge("interpret_brief", "run_hat_round")
    g.add_edge("run_hat_round", "advance_hat")

    g.add_conditional_edges(
        "advance_hat",
        should_continue,
        {
            "RUN": "run_hat_round",
            "BLUE": "blue_hat",
        },
    )

    g.add_edge("blue_hat", END)

    return g.compile()
