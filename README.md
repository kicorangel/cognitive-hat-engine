# Cognitive Hat Engine (LangGraph + FastAPI)

A multi-role, Six Thinking Hats-based strategic analysis engine.
Roles: CEO, CPO, CFO, CDO, CSO, CTO.
Hats: WHITE, RED, YELLOW, BLACK, GREEN, BLUE.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# edit .env with your OPENAI_API_KEY (optional)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

## Test locally
curl -X POST http://localhost:8000/analyze   -H "Content-Type: application/json"   -d '{"idea": "Evaluate whether we should launch the new AI product in Germany first"}'
