import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  checkHealth,
  getHistory,
  getJobDetail,
  analyzeReviews,
  runBenchmark,
} from "@/services/api";
import type { BenchmarkResult } from "@/types";

export function useAnalyzeReviews() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (formData: FormData) => analyzeReviews(formData),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["history"] });
    },
  });
}

export function useHealthCheck() {
  return useQuery({
    queryKey: ["health"],
    queryFn: () => checkHealth(),
    refetchInterval: 15000,
    staleTime: 5000,
  });
}

export function useHistory() {
  return useQuery({
    queryKey: ["history"],
    queryFn: () => getHistory(),
    refetchInterval: 10000,
  });
}

export function useJobDetail(batchId: string | null) {
  return useQuery({
    queryKey: ["jobDetail", batchId],
    queryFn: () => getJobDetail(batchId as string),
    enabled: Boolean(batchId),
  });
}

export function useBenchmark() {
  return useMutation({
    mutationFn: (formData: FormData) => runBenchmark(formData),
  });
}
