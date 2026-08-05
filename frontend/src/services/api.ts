import axios from "axios";
import type {
  HealthStatus,
  HistoryItem,
  JobDetailResponse,
  AnalyzeResponse,
  BenchmarkResult,
} from "@/types";

const api = axios.create({
  baseURL: "/api/v1",
});

export const analyzeReviews = async (data: FormData): Promise<AnalyzeResponse> => {
  const response = await api.post<AnalyzeResponse>("/analyze", data);
  return response.data;
};

export const checkHealth = async (): Promise<HealthStatus> => {
  const response = await api.get<HealthStatus>("/health");
  return response.data;
};

export const getHistory = async (): Promise<{ history: HistoryItem[] }> => {
  const response = await api.get<{ history: HistoryItem[] }>("/history");
  return response.data;
};

export const getJobDetail = async (batchId: string): Promise<JobDetailResponse> => {
  const response = await api.get<JobDetailResponse>(`/history/${batchId}`);
  return response.data;
};

export const runBenchmark = async (data: FormData): Promise<BenchmarkResult> => {
  const response = await api.post<BenchmarkResult>("/benchmark", data);
  return response.data;
};
