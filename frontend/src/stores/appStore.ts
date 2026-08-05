import { create } from "zustand";
import type { JobResponse, JobRequest } from "@/types";

interface AppState {
  history: JobResponse[];
  currentJob: JobResponse | null;
  settings: JobRequest;
  addHistory: (_job: JobResponse) => void;
  setCurrentJob: (_job: JobResponse | null) => void;
  updateSettings: (_newSettings: Partial<JobRequest>) => void;
}

export const useAppStore = create<AppState>((set) => ({
  history: [],
  currentJob: null,
  settings: {
    file_path: "",
    target_language: "es",
    export_formats: ["json"],
  },
  addHistory: (job: JobResponse) =>
    set((state) => ({
      history: [job, ...state.history],
    })),
  setCurrentJob: (job: JobResponse | null) =>
    set({ currentJob: job }),
  updateSettings: (newSettings: Partial<JobRequest>) =>
    set((state) => ({
      settings: { ...state.settings, ...newSettings },
    })),
}));
