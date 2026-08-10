"""Pure function implementations of engines.

Each function receives EngineContext and returns modified EngineContext.
No classes, no internal state - just pure transformations.
"""

import tiktoken

from app.core.config import settings
from app.engines.context_models import EngineContext

# Module-level encoding (initialized once)
_tokenizer_encoding = None


def _get_encoding() -> tiktoken.Encoding:
    global _tokenizer_encoding
    if _tokenizer_encoding is None:
        _tokenizer_encoding = tiktoken.get_encoding(settings.TOKENIZER_ENCODING)
    return _tokenizer_encoding


def tokenizer_engine(context: EngineContext) -> EngineContext:
    """Count tokens for each record using tiktoken encoding."""
    encoding = _get_encoding()
    total_tokens = 0

    for record in context.records:
        text = record.get("optimized_text", record.get("text", ""))
        tokens = encoding.encode(text)
        token_count = len(tokens)
        record["token_count"] = token_count
        total_tokens += token_count

    context.metrics.total_tokens = total_tokens
    context.metrics.avg_tokens_per_record = total_tokens / max(len(context.records), 1)
    return context

