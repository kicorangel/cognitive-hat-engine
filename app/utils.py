import uuid
from typing import Dict, Any, List


def new_run_id() -> str:
    return str(uuid.uuid4())


def ensure_outputs_bucket(outputs: Dict[str, Any], hat: str, role: str) -> None:
    if hat not in outputs:
        outputs[hat] = {}
    if role not in outputs[hat]:
        outputs[hat][role] = []


def uniq_extend(target: List[str], items: List[str]) -> None:
    seen = set(target)
    for x in items or []:
        x = (x or "").strip()
        if x and x not in seen:
            target.append(x)
            seen.add(x)
