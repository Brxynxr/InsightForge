from app.engines.base import BaseEngine, EngineContext


class ParserEngine(BaseEngine):
    """Responsible for converting AI responses into structured JSON."""

    def execute(self, context: EngineContext) -> EngineContext:
        responses = context.metadata.get("llm_responses", [])
        parsed = []
        for i, resp in enumerate(responses):
            if isinstance(resp, dict) and "error" in resp:
                parsed.append({"error": resp["error"], "record_index": i})
            else:
                try:
                    parsed.append({"parsed_text": resp})
                except Exception as e:
                    parsed.append({"error": str(e), "record_index": i})
        context.results = parsed
        return context
