from typing import Any

import httpx

from app.core.config import settings
from app.engines.base import BaseEngine, EngineContext


class LLMEngine(BaseEngine):
    """Responsible only for provider communication. Never manipulates business data."""

    def execute(self, context: EngineContext) -> EngineContext:
        api_key = settings.OPENAI_API_KEY
        model = settings.LLM_MODEL
        prompts: list[dict[str, Any]] = context.metadata.get("prompts", [])
        responses: list[Any] = []

        if api_key:
            for prompt in prompts:
                try:
                    with httpx.Client(
                        base_url="https://api.openai.com/v1", timeout=60.0
                    ) as client:
                        resp = client.post(
                            "/chat/completions",
                            headers={"Authorization": f"Bearer {api_key}"},
                            json={
                                "model": model,
                                "messages": [
                                    {"role": "system", "content": prompt["system"]},
                                    {"role": "user", "content": prompt["user"]},
                                ],
                                "max_tokens": 2000,
                            },
                        )
                        data = resp.json()
                        if "choices" in data and data["choices"]:
                            responses.append(data["choices"][0]["message"]["content"])
                        else:
                            responses.append({"error": f"Unexpected response: {data}"})
                except httpx.HTTPStatusError as e:
                    responses.append({"error": f"HTTP {e.response.status_code}: {e.response.text}"})
                except Exception as e:
                    responses.append({"error": str(e)})
        else:
            responses = [{"error": "No OPENAI_API_KEY configured"} for _ in prompts]

        context.metadata["llm_responses"] = responses
        return context
