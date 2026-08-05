import tiktoken

from app.engines.base import BaseEngine, EngineContext


class TokenizerEngine(BaseEngine):
    """Responsible for token counting, encoding selection, statistics."""

    def __init__(self, encoding_name: str = "o200k_base"):
        self.encoding_name = encoding_name
        self._encoding = tiktoken.get_encoding(encoding_name)

    def execute(self, context: EngineContext) -> EngineContext:
        total_tokens = 0
        for record in context.records:
            text = record.get("optimized_text", record.get("text", ""))
            tokens = self._encoding.encode(text)
            token_count = len(tokens)
            record["token_count"] = token_count
            total_tokens += token_count

        context.metrics["total_tokens"] = total_tokens
        context.metrics["avg_tokens_per_record"] = total_tokens / max(len(context.records), 1)
        return context
