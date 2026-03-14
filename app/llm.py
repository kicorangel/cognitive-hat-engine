import json
import os
from typing import Dict, Any, Optional

from dotenv import load_dotenv

load_dotenv()

try:
    from openai import OpenAI
except Exception:
    OpenAI = None


class LLMClient:
    def __init__(self) -> None:
        self.api_key = os.getenv("OPENAI_API_KEY", "").strip()

        raw_base_url = os.getenv("OPENAI_BASE_URL")
        if raw_base_url is not None:
            raw_base_url = raw_base_url.strip()
        self.base_url = raw_base_url if raw_base_url else None

        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip()
        self.temperature = float(os.getenv("OPENAI_TEMPERATURE", "0.2"))
        self.mode = "mock" if not self.api_key else "llm"

        self._client: Optional[Any] = None
        if self.mode == "llm":
            if OpenAI is None:
                raise RuntimeError("openai package not installed, but OPENAI_API_KEY is set.")

            kwargs = {"api_key": self.api_key}

            if self.base_url:
                if not (
                    self.base_url.startswith("http://")
                    or self.base_url.startswith("https://")
                ):
                    raise ValueError(
                        f"OPENAI_BASE_URL is invalid: {self.base_url!r}. "
                        "It must start with 'http://' or 'https://'."
                    )
                kwargs["base_url"] = self.base_url

            self._client = OpenAI(**kwargs)

    def generate_json(self, prompt: str) -> Dict[str, Any]:
        if self.mode == "mock":
            return {
                "content": "- (mock) Placeholder bullets based on the active hat.\n- (mock) Replace by configuring OPENAI_API_KEY.",
                "confidence": "low",
                "assumptions": ["Mock mode: no external LLM configured."],
                "questions": ["Set OPENAI_API_KEY to enable real analysis."],
            }

        assert self._client is not None
        resp = self._client.chat.completions.create(
            model=self.model,
            temperature=self.temperature,
            messages=[
                {"role": "system", "content": "You are a precise assistant that outputs STRICT JSON only."},
                {"role": "user", "content": prompt},
            ],
        )
        text = resp.choices[0].message.content or ""
        text = text.strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            text2 = text.strip("` \n")
            try:
                return json.loads(text2)
            except Exception as e:
                raise ValueError(f"LLM returned non-JSON content. Raw: {text[:500]}") from e
