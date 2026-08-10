"""Pure function implementations of engines.

Each function receives EngineContext and returns modified EngineContext.
No classes, no internal state - just pure transformations.
"""

import io
from typing import Any

import pandas as pd
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


COST_PER_MILLION_TOKENS = 2.50


def cost_engine(context: EngineContext) -> EngineContext:
    """Calculate costs at $2.50 USD per million tokens.
    Supports daily (10k reviews) and monthly (300k reviews) projections."""
    total_tokens = context.metrics.total_tokens
    total_input_tokens = context.metrics.total_input_tokens
    tokens = total_tokens or total_input_tokens

    estimated_cost = (tokens / 1_000_000) * COST_PER_MILLION_TOKENS

    total_records = context.metadata.total_records
    avg_tokens_per_record = tokens / max(total_records, 1)

    daily_10k = avg_tokens_per_record * 10_000
    monthly_300k = avg_tokens_per_record * 300_000

    context.metrics.cost_per_million_tokens = COST_PER_MILLION_TOKENS
    context.metrics.estimated_cost = round(estimated_cost, 6)
    context.metrics.daily_estimate_10k_reviews = {
        "total_tokens": round(daily_10k),
        "cost_usd": round((daily_10k / 1_000_000) * COST_PER_MILLION_TOKENS, 2),
    }
    context.metrics.monthly_estimate_300k_reviews = {
        "total_tokens": round(monthly_300k),
        "cost_usd": round(
            (monthly_300k / 1_000_000) * COST_PER_MILLION_TOKENS, 2
        ),
    }

    return context


def export_engine(context: EngineContext) -> EngineContext:
    """Export records to Excel, JSON, or CSV formats."""
    formats = context.metadata.export_formats or ["json"]
    records = context.records
    results = context.results

    merged = []
    for i, record in enumerate(records):
        row = record.model_dump()
        if i < len(results):
            result_item = results[i]
            row["result"] = (
                result_item.model_dump()
                if hasattr(result_item, "model_dump")
                else result_item
            )
        merged.append(row)

    exports: dict[str, Any] = {}
    for fmt in formats:
        df = pd.DataFrame(merged)
        buffer = io.BytesIO()
        if fmt == "excel":
            df.to_excel(buffer, index=False)
            buffer.seek(0)
            exports[fmt] = buffer.getvalue()
        elif fmt == "csv":
            df.to_csv(buffer, index=False)
            buffer.seek(0)
            exports[fmt] = buffer.getvalue()
        else:
            result_bytes = df.to_json(orient="records").encode("utf-8")
            exports[fmt] = result_bytes

    context.metadata.exports = exports
    return context

