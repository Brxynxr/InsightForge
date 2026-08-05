export interface JobRequest {
  file_path: string;
  required_columns?: string[];
  target_language?: string;
  export_formats?: string[];
}

export interface JobResponse {
  batch_id: string;
  status: string;
  metrics: Record<string, number>;
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