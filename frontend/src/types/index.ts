export interface JobRequest {
  file_path: string;
  required_columns?: string[];
  target_language?: string;
  export_formats?: string[];
  optimize_tokens?: boolean;
}

export interface JobResponse {
  batch_id: string;
  status: string;
  metrics: Record<string, unknown>;
  results: Record<string, unknown>[];
  exports?: Record<string, unknown>;
}

export interface HistoryItem {
  batch_id: string;
  status: string;
  file_name?: string;
  total_records: number;
  validated_records: number;
  rejected_records: number;
  total_tokens: number;
  estimated_cost: number;
  target_language?: string;
  export_formats?: string[];
  created_at?: string;
  completed_at?: string;
  metrics: Record<string, number>;
}

export interface JobRecordDetail {
  record_index: number;
  original_data: Record<string, unknown>;
  optimized_text?: string;
  token_count: number;
  prompt?: string;
  llm_response?: string;
  parsed_result: Record<string, unknown>;
  error?: string;
}

export interface JobDetailResponse {
  job: HistoryItem;
  records: JobRecordDetail[];
}

export interface HealthStatus {
  status: string;
}

export interface TokenComparison {
  total_original_tokens: number;
  total_translated_tokens: number;
  token_difference: number;
  percentage_reduction: number;
  cost_original_usd: number;
  cost_translated_usd: number;
  cost_savings_usd: number;
  cost_per_million_tokens: number;
  daily_projection_10k: {
    tokens_original: number;
    tokens_translated: number;
    cost_original_usd: number;
    cost_translated_usd: number;
    savings_usd: number;
  };
  monthly_projection_300k: {
    tokens_original: number;
    tokens_translated: number;
    cost_original_usd: number;
    cost_translated_usd: number;
    savings_usd: number;
  };
}

export interface AnalyzeResponse {
  batch_id: string;
  status: string;
  metrics: Record<string, unknown>;
  results: Record<string, unknown>[];
  token_comparison?: TokenComparison;
}

export interface BenchmarkResult {
  file_path: string;
  columns: string[];
  total_records: number;
  reviews_with_text: number;
  empty_reviews: number;
  review_column: string;
  optimize_tokens: boolean;
  target_language: string;
  timings: Record<string, number>;
  totals: {
    total_time_seconds: number;
    tokens_original: number;
    tokens_translated: number;
    token_difference: number;
    percentage_reduction: number;
    cost_original_usd: number;
    cost_translated_usd: number;
    cost_savings_usd: number;
    output_size_kb: number;
    tokens_per_record: number;
    records_per_second_read: number;
  };
  projections: {
    daily_10k: { tokens: number; cost_usd: number };
    monthly_300k: { tokens: number; cost_usd: number };
  };
}