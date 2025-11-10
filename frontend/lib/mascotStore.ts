import { create } from 'zustand';

type EmotionType =
  | 'idle'
  | 'happy'
  | 'thinking'
  | 'celebrating'
  | 'tired'
  | 'encouraging'
  | 'sleeping';

interface MascotState {
  emotion: EmotionType;
  setEmotion: (emotion: EmotionType) => void;
  celebrate: () => void;
  think: () => void;
  encourage: () => void;
  rest: () => void;
}

export const useMascot = create<MascotState>((set) => ({
  emotion: 'idle',

  setEmotion: (emotion) => set({ emotion }),

  // Helper methods for common emotion sequences
  celebrate: () => {
    set({ emotion: 'celebrating' });
    setTimeout(() => set({ emotion: 'happy' }), 2500);
    setTimeout(() => set({ emotion: 'idle' }), 5000);
  },

  think: () => {
    set({ emotion: 'thinking' });
    // Caller will reset when done
  },

  encourage: () => {
    set({ emotion: 'encouraging' });
    setTimeout(() => set({ emotion: 'idle' }), 4000);
  },

  rest: () => {
    set({ emotion: 'tired' });
    setTimeout(() => set({ emotion: 'sleeping' }), 3000);
    setTimeout(() => set({ emotion: 'idle' }), 8000);
  },
}));
