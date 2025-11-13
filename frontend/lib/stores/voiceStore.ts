// lib/stores/voiceStore.ts
import { create } from 'zustand';

interface VoiceState {
  isVoiceMode: boolean;
  isListening: boolean;
  isSpeaking: boolean;
  isProcessing: boolean;

  setVoiceMode: (active: boolean) => void;
  setListening: (listening: boolean) => void;
  setSpeaking: (speaking: boolean) => void;
  setProcessing: (processing: boolean) => void;
}

export const useVoiceStore = create<VoiceState>((set) => ({
  isVoiceMode: false,
  isListening: false,
  isSpeaking: false,
  isProcessing: false,

  setVoiceMode: (active) => set({ isVoiceMode: active }),
  setListening: (listening) => set({ isListening: listening }),
  setSpeaking: (speaking) => set({ isSpeaking: speaking }),
  setProcessing: (processing) => set({ isProcessing: processing }),
}));
