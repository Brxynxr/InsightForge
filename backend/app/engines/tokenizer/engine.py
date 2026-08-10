import tiktoken

from app.core.config import settings
from app.engines.base import BaseEngine
from app.engines.context_models import EngineContext


class TokenizerEngine(BaseEngine):
    """Responsible for token counting, encoding selection, statistics."""

    def __init__(self) -> None:
        self._encoding = tiktoken.get_encoding(settings.TOKENIZER_ENCODING)

    def execute(self, context: EngineContext) -> EngineContext:
        total_tokens = 0
        for record in context.records:
            text = record.get("optimized_text", record.get("text", ""))
            tokens = self._encoding.encode(text)
            token_count = len(tokens)
            record["token_count"] = token_count
            total_tokens += token_count

        context.metrics.total_tokens = total_tokens
        context.metrics.avg_tokens_per_record = total_tokens / max(len(context.records), 1)
        return context
