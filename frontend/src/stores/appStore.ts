import { create } from "zustand";
import type { JobRequest } from "@/types";

interface AppSettings extends JobRequest {
  openai_api_key?: string;
  batch_size: number;
}

interface AppState {
  settings: AppSettings;
  updateSettings: (_newSettings: Partial<AppSettings>) => void;
}

export const useAppStore = create<AppState>((set) => ({
  settings: {
    file_path: "",
    target_language: "es",
    export_formats: ["json"],
    batch_size: 1000,
  },
  updateSettings: (newSettings: Partial<AppSettings>) =>
    set((state) => ({
      settings: { ...state.settings, ...newSettings },
    })),
}));
