"use client";

import { create } from "zustand";

type EmotionType =
  | "idle"
  | "happy"
  | "thinking"
  | "celebrating"
  | "tired"
  | "encouraging"
  | "sleeping";

interface MascotState {
  emotion: EmotionType;
  setEmotion: (emotion: EmotionType) => void;
  think: () => void;
}

export const useMascot = create<MascotState>((set) => ({
  emotion: "idle", // ✅ FIXED - Default to "idle" instead of undefined
  setEmotion: (emotion) => set({ emotion }),
  think: () => {
    set({ emotion: "thinking" });
  },
}));
