import time
from typing import Any

import pandas as pd
import tiktoken

from app.core.config import settings


def run_benchmark(
    file_path: str,
    review_column: str = "reseña",
    optimize_tokens: bool = True,
    target_language: str = "en",
) -> dict[str, Any]:
    """Run a benchmark on a single file and return detailed timing metrics."""
    encoding = tiktoken.get_encoding(settings.TOKENIZER_ENCODING)
    timings: dict[str, float] = {}

    # --- Step 1: Read file ---
    t0 = time.perf_counter()
    df = pd.read_excel(file_path)
    timings["lectura_excel"] = round(time.perf_counter() - t0, 4)

    total_records = len(df)
    columns = list(df.columns)

    # --- Step 2: Count empty vs non-empty ---
    t1 = time.perf_counter()
    texts = df[review_column].fillna("").astype(str)
    empty_mask = texts.str.strip() == ""
    empty_count = int(empty_mask.sum())
    non_empty_count = total_records - empty_count
    timings["deteccion_vacios"] = round(time.perf_counter() - t1, 4)

    # --- Step 3: Tokenize original ---
    t2 = time.perf_counter()
    valid_texts = texts[~empty_mask].tolist()
    token_counts_original = [len(encoding.encode(t)) for t in valid_texts]
    total_tokens_original = sum(token_counts_original)
    timings["tokenizacion_original"] = round(time.perf_counter() - t2, 4)

    # --- Step 4: Simulate translation (if optimize_tokens) ---
    tokens_translated = total_tokens_original
    if optimize_tokens and target_language != "es":
        # Simulate translation by estimating token reduction (English ~15% fewer)
        tokens_translated = int(total_tokens_original * 0.85)
        timings["simulacion_traduccion"] = 0.0  # Would be real translation time
    else:
        timings["simulacion_traduccion"] = 0.0

    # --- Step 5: Cost calculation ---
    t3 = time.perf_counter()
    cost_original = (total_tokens_original / 1_000_000) * 2.50
    cost_translated = (tokens_translated / 1_000_000) * 2.50
    cost_savings = cost_original - cost_translated
    timings["calculo_costos"] = round(time.perf_counter() - t3, 4)

    # --- Step 6: Export simulation ---
    t4 = time.perf_counter()
    output_buffer = df.to_json(orient="records").encode("utf-8")
    output_size_kb = round(len(output_buffer) / 1024, 2)
    timings["exportacion"] = round(time.perf_counter() - t4, 4)

    # --- Totals ---
    total_time = sum(timings.values())

    # Projections
    avg_tokens = total_tokens_original / max(non_empty_count, 1)
    daily_10k_tokens = avg_tokens * 10_000
    monthly_300k_tokens = avg_tokens * 300_000

    return {
        "file_path": file_path,
        "columns": columns,
        "total_records": total_records,
        "reviews_with_text": non_empty_count,
        "empty_reviews": empty_count,
        "review_column": review_column,
        "optimize_tokens": optimize_tokens,
        "target_language": target_language,
        "timings": timings,
        "totals": {
            "total_time_seconds": round(total_time, 4),
            "tokens_original": total_tokens_original,
            "tokens_translated": tokens_translated,
            "token_difference": total_tokens_original - tokens_translated,
            "percentage_reduction": round(
                ((total_tokens_original - tokens_translated)
                 / max(total_tokens_original, 1)) * 100, 2
            ),
            "cost_original_usd": round(cost_original, 4),
            "cost_translated_usd": round(cost_translated, 4),
            "cost_savings_usd": round(cost_savings, 4),
            "output_size_kb": output_size_kb,
            "tokens_per_record": round(avg_tokens, 1),
            "records_per_second_read": round(
                total_records / max(timings["lectura_excel"], 0.001), 0
            ),
        },
        "projections": {
            "daily_10k": {
                "tokens": round(daily_10k_tokens),
                "cost_usd": round(
                    (daily_10k_tokens / 1_000_000) * 2.50, 2
                ),
            },
            "monthly_300k": {
                "tokens": round(monthly_300k_tokens),
                "cost_usd": round(
                    (monthly_300k_tokens / 1_000_000) * 2.50, 2
                ),
            },
        },
    }
