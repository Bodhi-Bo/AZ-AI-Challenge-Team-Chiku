'use client';

import { useState, useRef, useCallback } from 'react';

interface UseTextToSpeechReturn {
  speak: (text: string) => Promise<void>;
  stop: () => void;
  isSpeaking: boolean;
  error: string | null;
}

export function useTextToSpeechElevenlabs(): UseTextToSpeechReturn {
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const speak = useCallback(async (text: string) => {
    if (!text.trim()) return;

    console.log('🎤 Starting speech generation for:', text.substring(0, 50) + '...');
    setIsSpeaking(true);
    setError(null);

    try {
      // Call our API route
      console.log('📡 Calling /api/text-to-speech...');
      const response = await fetch('/api/text-to-speech', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ text }),
      });

      console.log('📡 Response status:', response.status);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ error: 'Unknown error' }));
        console.error('❌ API error:', errorData);
        throw new Error(errorData.error || 'Failed to generate speech');
      }

      // Get audio blob
      console.log('🎵 Received audio, creating blob...');
      const audioBlob = await response.blob();
      const audioUrl = URL.createObjectURL(audioBlob);

      // Create and play audio
      const audio = new Audio(audioUrl);
      audioRef.current = audio;

      audio.addEventListener('ended', () => {
        console.log('✅ Audio playback finished');
        setIsSpeaking(false);
        URL.revokeObjectURL(audioUrl);
      });

      audio.addEventListener('error', (e) => {
        console.error('❌ Audio playback error:', e);
        setIsSpeaking(false);
        setError('Failed to play audio');
      });

      console.log('▶️ Playing audio...');
      await audio.play();

    } catch (err) {
      console.error('❌ Speech error:', err);
      setError(err instanceof Error ? err.message : 'Speech generation failed');
      setIsSpeaking(false);
    }
  }, []);

  const stop = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
      setIsSpeaking(false);
    }
  }, []);

  return {
    speak,
    stop,
    isSpeaking,
    error,
  };
}
