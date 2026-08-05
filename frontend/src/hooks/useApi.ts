import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { processJob, checkHealth, getHistory, getJobDetail } from "@/services/api";
import { useAppStore } from "@/stores/appStore";
import type { JobResponse } from "@/types";

export function useProcessJob() {
  const queryClient = useQueryClient();
  const addHistory = useAppStore((state) => state.addHistory);

  return useMutation({
    mutationFn: (formData: FormData) => processJob(formData),
    onSuccess: (data: JobResponse) => {
      addHistory(data);
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
    queryFn: () => getJobDetail(batchId!),
    enabled: Boolean(batchId),
  });
}