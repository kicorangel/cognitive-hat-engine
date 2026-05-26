from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api_models import AnalyzeRequest, AnalyzeResponse
from .graph import build_graph
from .utils import new_run_id

app = FastAPI(title="Cognitive Hat Engine", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

graph = build_graph()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(req: AnalyzeRequest):
    run_id = new_run_id()

    initial_state = {
        "run_id": run_id,
        "idea": req.idea,
        "roles": [role.model_dump() for role in req.roles] if req.roles else None,
    }

    final_state = graph.invoke(initial_state)

    executive_summary = final_state.get("executive_summary") or ""
    options = final_state.get("options") or {"A": "", "B": "", "C": ""}
    recommendation = final_state.get("recommendation") or ""
    decision_confidence = final_state.get("decision_confidence") or "medium"
    metrics = final_state.get("analysis_metrics") or {}

    return AnalyzeResponse(
        run_id=run_id,
        mode=final_state.get("mode", "mock"),
        final_hat=final_state.get("current_hat", "BLUE"),
        executive_summary=executive_summary,
        options=options,
        recommendation=recommendation,
        decision_confidence=decision_confidence,
        agent_interactions_count=int(metrics.get("agent_interactions_count", 0)),
        llm_calls_count=int(metrics.get("llm_calls_count", 0)),
        analysis_metrics=metrics,
        state=final_state,
    )
