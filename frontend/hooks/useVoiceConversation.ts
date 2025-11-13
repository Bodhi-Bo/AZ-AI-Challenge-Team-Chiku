'use client';

import { useCallback, useRef, useState } from 'react';
import { useElevenLabsStream } from '@/components/voice/useElevenLabsStream';

type Phase = 'idle' | 'listening' | 'thinking' | 'speaking' | 'error';

interface UseVoiceConversationReturn {
  phase: Phase;
  transcription: string;
  isListening: boolean;
  isSpeaking: boolean;
  start: () => Promise<void>;
  stop: () => void;
  error: string | null;
}

// Helper to sleep
const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

export function useVoiceConversation(): UseVoiceConversationReturn {
  const [phase, setPhase] = useState<Phase>('idle');
  const [transcription, setTranscription] = useState('');
  const [error, setError] = useState<string | null>(null);

  const recognitionRef = useRef<SpeechRecognition | null>(null);
  const mediaStreamRef = useRef<MediaStream | null>(null);
  const silenceTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const isActiveRef = useRef(false);

  // TTS integration
  const {
    isSpeaking,
    speak,
    stopSpeaking,
    error: ttsError,
  } = useElevenLabsStream();

  // Clean up mic and recognition
  const cleanupMic = useCallback(() => {
    // Stop recognition
    if (recognitionRef.current) {
      try {
        recognitionRef.current.stop();
      } catch {}
      recognitionRef.current = null;
    }

    // Stop media stream
    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach((track) => track.stop());
      mediaStreamRef.current = null;
    }

    // Clear timers
    if (silenceTimerRef.current) {
      clearTimeout(silenceTimerRef.current);
      silenceTimerRef.current = null;
    }
  }, []);

  // Start listening for user speech
  const startListening = useCallback(async (): Promise<string> => {
    console.log('🎤 [Voice] Starting to listen...');

    // Don't start if TTS is still speaking
    if (isSpeaking) {
      console.warn('⛔ [Voice] Cannot listen while speaking');
      throw new Error('Cannot listen while speaking');
    }

    setPhase('listening');
    setTranscription('');

    return new Promise<string>(async (resolve, reject) => {
      try {
        // Request microphone access
        const stream = await navigator.mediaDevices.getUserMedia({
          audio: {
            echoCancellation: true,
            noiseSuppression: true,
            autoGainControl: true,
          },
        });
        mediaStreamRef.current = stream;

        // Initialize speech recognition
        const SpeechRecognitionAPI =
          window.SpeechRecognition || window.webkitSpeechRecognition;

        if (!SpeechRecognitionAPI) {
          throw new Error('Speech recognition not supported in this browser');
        }

        const recognition = new SpeechRecognitionAPI();
        recognition.continuous = true;
        recognition.interimResults = true;
        recognition.lang = 'en-US';
        recognitionRef.current = recognition;

        let finalTranscript = '';

        recognition.onresult = (event: SpeechRecognitionEvent) => {
          // Clear silence timer on any speech
          if (silenceTimerRef.current) {
            clearTimeout(silenceTimerRef.current);
          }

          let interimText = '';
          let newFinal = '';

          for (let i = event.resultIndex; i < event.results.length; i++) {
            const transcript = event.results[i][0].transcript;
            if (event.results[i].isFinal) {
              newFinal += transcript;
            } else {
              interimText += transcript;
            }
          }

          // Update final transcript
          if (newFinal) {
            finalTranscript += newFinal + ' ';
          }

          // Show live transcription
          setTranscription((finalTranscript + interimText).trim());

          // If we got final text, wait for silence before ending
          if (newFinal) {
            silenceTimerRef.current = setTimeout(() => {
              console.log('🔇 [Voice] Silence detected, ending listening');
              cleanupMic();
              const result = finalTranscript.trim();
              if (result) {
                resolve(result);
              } else {
                reject(new Error('No speech detected'));
              }
            }, 1500); // 1.5s silence threshold
          }
        };

        recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
          console.error('❌ [Voice] Recognition error:', event.error);
          cleanupMic();
          reject(new Error(`Speech recognition error: ${event.error}`));
        };

        recognition.onend = () => {
          console.log('🏁 [Voice] Recognition ended');
        };

        recognition.start();

        // Safety timeout: max 15 seconds of listening
        setTimeout(() => {
          if (recognitionRef.current) {
            console.warn('⏱️ [Voice] Safety timeout reached');
            cleanupMic();
            const result = finalTranscript.trim();
            if (result) {
              resolve(result);
            } else {
              reject(new Error('No speech within timeout'));
            }
          }
        }, 15000);
      } catch (err) {
        cleanupMic();
        reject(err);
      }
    });
  }, [isSpeaking, cleanupMic]);

  // Query the server with user input
  const queryServer = useCallback(async (message: string): Promise<string> => {
    console.log('💬 [Voice] Querying server:', message);

    const response = await fetch('/api/voice-stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error('❌ [Voice] Server error:', response.status, errorText);
      throw new Error(`Server request failed: ${response.status}`);
    }

    const data = await response.json();
    console.log('📦 [Voice] Server response data:', data);

    const reply = data.response || data.reply || '';
    console.log('💬 [Voice] Extracted reply:', reply);

    if (!reply) {
      throw new Error('Server returned empty response');
    }

    return reply;
  }, []);

  // Run one complete conversation turn
  const conversationTurn = useCallback(async () => {
    if (!isActiveRef.current) return;

    try {
      // Step 1: Listen for user input
      const userInput = await startListening();
      console.log('✅ [Voice] User said:', userInput);

      if (!isActiveRef.current) return;

      // Step 2: Query server
      setPhase('thinking');
      const serverResponse = await queryServer(userInput);
      console.log('✅ [Voice] Server replied:', serverResponse);
      console.log('📏 [Voice] Response length:', serverResponse?.length);

      if (!isActiveRef.current) return;

      // Step 3: Speak response
      setPhase('speaking');
      console.log('🎙️ [Voice] About to call speak() with:', serverResponse);
      await speak(serverResponse);
      console.log('✅ [Voice] Finished speaking');

      if (!isActiveRef.current) return;

      // Step 4: Cooldown to prevent echo
      console.log('⏳ [Voice] Cooldown...');
      await sleep(800);

      if (!isActiveRef.current) return;

      // Step 5: Start next turn
      setPhase('idle');
      setTranscription('');

      // Small delay before restarting
      await sleep(200);

      if (isActiveRef.current) {
        conversationTurn(); // Next turn
      }
    } catch (err) {
      console.error('❌ [Voice] Conversation turn error:', err);

      if (isActiveRef.current) {
        setError(err instanceof Error ? err.message : 'Unknown error');
        setPhase('error');

        // Try to recover after error
        await sleep(2000);
        if (isActiveRef.current) {
          setError(null);
          setPhase('idle');
          await sleep(500);
          if (isActiveRef.current) {
            conversationTurn(); // Retry
          }
        }
      }
    }
  }, [startListening, queryServer, speak]);

  // Start the conversation loop
  const start = useCallback(async () => {
    if (isActiveRef.current) {
      console.log('⏩ [Voice] Already active');
      return;
    }

    console.log('🚀 [Voice] Starting conversation');
    isActiveRef.current = true;
    setError(null);
    setPhase('idle');

    // Small delay to ensure UI is ready
    await sleep(100);

    if (isActiveRef.current) {
      conversationTurn();
    }
  }, [conversationTurn]);

  // Stop the conversation loop
  const stop = useCallback(() => {
    console.log('🛑 [Voice] Stopping conversation');
    isActiveRef.current = false;
    cleanupMic();
    stopSpeaking();
    setPhase('idle');
    setTranscription('');
    setError(null);
  }, [cleanupMic, stopSpeaking]);

  // Sync TTS errors
  if (ttsError && !error) {
    setError(ttsError);
    setPhase('error');
  }

  return {
    phase,
    transcription,
    isListening: phase === 'listening',
    isSpeaking,
    start,
    stop,
    error,
  };
}
