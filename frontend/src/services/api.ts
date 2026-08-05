import axios from "axios";
import type {
  JobResponse,
  HealthStatus,
  HistoryItem,
  JobDetailResponse,
} from "@/types";

const api = axios.create({
  baseURL: "/api/v1",
});

export const processJob = async (data: FormData): Promise<JobResponse> => {
  const response = await api.post<JobResponse>("/process", data);
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