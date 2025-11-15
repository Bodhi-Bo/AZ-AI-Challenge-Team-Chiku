'use client';

import { useState, useCallback, useRef, useEffect } from 'react';
import { useSpeechRecognition } from './useSpeechRecognition';
import { useElevenLabs } from './useElevenLabs';

type Phase = 'idle' | 'listening' | 'thinking' | 'speaking' | 'error';

interface UseVoiceConversationReturn {
  phase: Phase;
  transcription: string;
  isListening: boolean;
  isSpeaking: boolean;
  start: () => void;
  stop: () => void;
  error: string | null;
}

export function useVoiceConversation(): UseVoiceConversationReturn {
  const [phase, setPhase] = useState<Phase>('idle');
  const [error, setError] = useState<string | null>(null);

  const previousSpeakingRef = useRef(false);
  const lastSentMessageRef = useRef('');
  const isActiveRef = useRef(false);

  const {
    transcript,
    isListening,
    isFinal,
    startListening,
    stopListening,
    resetTranscript
  } = useSpeechRecognition();

  const {
    speak,
    isSpeaking,
    error: ttsError
  } = useElevenLabs();

  // Query the server with user input
  const queryServer = useCallback(async (message: string): Promise<string> => {
    console.log('💬 [Voice] Querying server:', message);

    try {
      const response = await fetch('/api/voice-stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message }),
      });

      if (!response.ok) {
        throw new Error(`Server request failed: ${response.status}`);
      }

      const data = await response.json();
      const reply = data.response || data.reply || '';

      if (!reply) {
        throw new Error('Server returned empty response');
      }

      console.log('✅ [Voice] Server replied:', reply);
      return reply;
    } catch (err) {
      console.error('❌ [Voice] Server error:', err);
      throw err;
    }
  }, []);

  // Handle AI speaking state changes (echo prevention + auto-resume)
  useEffect(() => {
    const wasSpeaking = previousSpeakingRef.current;
    const isCurrentlySpeaking = isSpeaking;

    console.log(`🔊 Speaking: ${wasSpeaking} → ${isCurrentlySpeaking}`);
    previousSpeakingRef.current = isCurrentlySpeaking;

    // AI started speaking
    if (!wasSpeaking && isCurrentlySpeaking) {
      console.log("🔇 AI started speaking - stopping mic");
      setPhase('speaking');
      if (isListening) {
        stopListening();
      }
    }

    // AI finished speaking
    if (wasSpeaking && !isCurrentlySpeaking) {
      console.log("🎤 AI finished speaking");

      // Only auto-resume if conversation is active
      if (isActiveRef.current) {
        setPhase('idle');

        setTimeout(() => {
          if (isActiveRef.current) {
            console.log('🔄 Auto-resuming microphone...');
            setPhase('listening');
            startListening();
          }
        }, 1000);
      }
    }
  }, [isSpeaking, isListening, stopListening, startListening]);

  // Handle sending messages when user pauses
  useEffect(() => {
    if (!isFinal || !transcript || !isActiveRef.current) return;
    if (phase === 'thinking' || phase === 'speaking') return;

    // Prevent duplicate sends
    if (transcript === lastSentMessageRef.current) {
      console.log('⏭️ Skipping duplicate message');
      resetTranscript();
      return;
    }

    const sendMessage = async () => {
      console.log('📤 Sending:', transcript);
      lastSentMessageRef.current = transcript;

      setPhase('thinking');
      stopListening();

      try {
        const response = await queryServer(transcript);

        if (!isActiveRef.current) return;

        setPhase('speaking');
        await speak(response);

      } catch (err) {
        console.error('❌ Send error:', err);
        setError(err instanceof Error ? err.message : 'Failed to process message');
        setPhase('error');

        // Auto-recover from error
        setTimeout(() => {
          if (isActiveRef.current) {
            setError(null);
            setPhase('listening');
            startListening();
          }
        }, 2000);
      } finally {
        resetTranscript();
      }
    };

    sendMessage();
  }, [isFinal, transcript, phase, queryServer, speak, stopListening, resetTranscript, startListening]);

  // Sync TTS errors
  useEffect(() => {
    if (ttsError) {
      setError(ttsError);
      setPhase('error');
    }
  }, [ttsError]);

  // Start voice conversation
  const start = useCallback(() => {
    if (isActiveRef.current) {
      console.log('⏩ [Voice] Already active');
      return;
    }

    console.log('🚀 [Voice] Starting conversation');
    isActiveRef.current = true;
    setError(null);
    setPhase('listening');

    // Start listening after small delay
    setTimeout(() => {
      if (isActiveRef.current) {
        startListening();
      }
    }, 500);
  }, [startListening]);

  // Stop voice conversation
  const stop = useCallback(() => {
    console.log('🛑 [Voice] Stopping conversation');
    isActiveRef.current = false;
    stopListening();
    setPhase('idle');
    resetTranscript();
    setError(null);
    lastSentMessageRef.current = '';
  }, [stopListening, resetTranscript]);

  return {
    phase,
    transcription: transcript,
    isListening,
    isSpeaking,
    start,
    stop,
    error,
  };
}
