'use client';

import { useState, useRef, useCallback, useEffect } from 'react';

interface UseElevenLabsStreamReturn {
  isSpeaking: boolean;
  speak: (text: string) => Promise<void>;
  stopSpeaking: () => void;
  error: string | null;
}

export function useElevenLabsStream(): UseElevenLabsStreamReturn {
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const audioQueueRef = useRef<AudioBuffer[]>([]);
  const currentSourceRef = useRef<AudioBufferSourceNode | null>(null);

  // Track completion state
  const wsClosedRef = useRef(false);
  const isPlayingRef = useRef(false);
  const resolveCompleteRef = useRef<(() => void) | null>(null);
  const playNextAudioRef = useRef<() => void>(() => {});

  // Ensure AudioContext is ready
  const ensureAudioContext = async () => {
    if (!audioContextRef.current) {
      audioContextRef.current = new AudioContext();
    }
    if (audioContextRef.current.state === 'suspended') {
      await audioContextRef.current.resume();
    }
  };

  // Check if we're truly done: WebSocket closed + queue empty + not playing
  const checkIfComplete = useCallback(() => {
    const isDone =
      wsClosedRef.current &&
      audioQueueRef.current.length === 0 &&
      !isPlayingRef.current;

    if (isDone && resolveCompleteRef.current) {
      console.log('✅ [TTS] Playback complete - resolving');
      const resolve = resolveCompleteRef.current;
      resolveCompleteRef.current = null;
      setIsSpeaking(false);
      resolve();
    }
  }, []);

  // Play next audio buffer from queue
  const playNextAudio = useCallback(() => {
    if (isPlayingRef.current || audioQueueRef.current.length === 0) {
      return;
    }
    if (!audioContextRef.current) return;

    const audioBuffer = audioQueueRef.current.shift()!;
    isPlayingRef.current = true;

    const source = audioContextRef.current.createBufferSource();
    source.buffer = audioBuffer;
    source.connect(audioContextRef.current.destination);
    currentSourceRef.current = source;

    source.onended = () => {
      isPlayingRef.current = false;
      currentSourceRef.current = null;

      // Try to play next buffer
      if (audioQueueRef.current.length > 0) {
        playNextAudioRef.current();
      } else {
        // Queue empty - check if we're completely done
        checkIfComplete();
      }
    };

    source.start();
  }, [checkIfComplete]);

  // Update ref when callback changes
  useEffect(() => {
    playNextAudioRef.current = playNextAudio;
  }, [playNextAudio]);

  const speak = useCallback(
    async (text: string) => {
      console.log('🔊 [TTS] speak() called with:', {
        text,
        length: text?.length,
        trimmed: text?.trim().length,
      });

      if (!text.trim()) {
        console.warn('⚠️ [TTS] Empty text provided, skipping');
        return;
      }

      console.log('🔊 [TTS] Starting speech:', text.substring(0, 50));

      // Reset state
      wsClosedRef.current = false;
      audioQueueRef.current = [];
      setError(null);
      setIsSpeaking(true);

      await ensureAudioContext();

      const voiceId = process.env.NEXT_PUBLIC_ELEVENLABS_VOICE_ID;
      const modelId = process.env.NEXT_PUBLIC_ELEVENLABS_MODEL_ID;
      const apiKey = process.env.NEXT_PUBLIC_ELEVENLABS_API_KEY;

      console.log('🔑 [TTS] Config:', {
        voiceId: voiceId ? '✅ Set' : '❌ Missing',
        modelId: modelId ? '✅ Set' : '❌ Missing',
        apiKey: apiKey ? '✅ Set' : '❌ Missing',
      });

      if (!apiKey) {
        console.error('❌ [TTS] Missing API key');
        setError('ElevenLabs API key not found');
        setIsSpeaking(false);
        return;
      }

      if (!voiceId) {
        console.error('❌ [TTS] Missing voice ID');
        setError('ElevenLabs voice ID not found');
        setIsSpeaking(false);
        return;
      }

      const wsUrl = `wss://api.elevenlabs.io/v1/text-to-speech/${voiceId}/stream-input?model_id=${modelId}`;
      console.log('🔗 [TTS] WebSocket URL ready');

      return new Promise<void>((resolve, reject) => {
        resolveCompleteRef.current = resolve;

        // Safety timeout: never hang forever
        const safetyTimeout = setTimeout(() => {
          console.warn(
            '⚠️ [TTS] Safety timeout reached - no connection in 30s'
          );
          try {
            wsRef.current?.close();
          } catch {}
          setIsSpeaking(false);
          if (resolveCompleteRef.current) {
            resolveCompleteRef.current();
            resolveCompleteRef.current = null;
          }
        }, 30000);

        // Connection timeout: if not connected in 5s, fail fast
        const connectionTimeout = setTimeout(() => {
          if (wsRef.current && wsRef.current.readyState !== WebSocket.OPEN) {
            console.error(
              '❌ [TTS] Connection timeout - WebSocket failed to open'
            );
            try {
              wsRef.current?.close();
            } catch {}
            setError('Failed to connect to ElevenLabs');
            setIsSpeaking(false);
            if (resolveCompleteRef.current) {
              reject(new Error('Connection timeout'));
              resolveCompleteRef.current = null;
            }
            clearTimeout(safetyTimeout);
          }
        }, 5000);

        try {
          console.log('🔌 [TTS] Creating WebSocket connection...');
          const ws = new WebSocket(wsUrl);
          wsRef.current = ws;

          ws.addEventListener('open', async () => {
            console.log('✅ [WebSocket] Connected to ElevenLabs');
            clearTimeout(connectionTimeout);

            await ensureAudioContext();

            // Send initialization message with API key
            const initMessage = {
              text: ' ',
              xi_api_key: apiKey,
              voice_settings: {
                stability: 0.5,
                similarity_boost: 0.8,
                style: 0.7,
                use_speaker_boost: true,
              },
              generation_config: {
                chunk_length_schedule: [120, 160, 250, 290],
              },
            };
            console.log('📤 [TTS] Sending init message');
            ws.send(JSON.stringify(initMessage));

            // Send main text with API key
            console.log('📤 [TTS] Sending text message');
            ws.send(JSON.stringify({ text, xi_api_key: apiKey }));

            // Flush to signal end with API key
            console.log('📤 [TTS] Sending flush message');
            ws.send(
              JSON.stringify({ text: '', xi_api_key: apiKey, flush: true })
            );
          });

          ws.addEventListener('message', async (event) => {
            try {
              const data = JSON.parse(event.data);

              if (data.audio) {
                console.log('🎵 [TTS] Received audio chunk');
                // Decode base64 audio
                const audioData = atob(data.audio);
                const arrayBuffer = new Uint8Array(audioData.length);
                for (let i = 0; i < audioData.length; i++) {
                  arrayBuffer[i] = audioData.charCodeAt(i);
                }

                if (audioContextRef.current) {
                  try {
                    const audioBuffer =
                      await audioContextRef.current.decodeAudioData(
                        arrayBuffer.buffer
                      );
                    audioQueueRef.current.push(audioBuffer);
                    console.log(
                      '✅ [TTS] Audio decoded, queue size:',
                      audioQueueRef.current.length
                    );

                    // Start playing if not already playing
                    if (!isPlayingRef.current) {
                      console.log('▶️ [TTS] Starting playback');
                      playNextAudio();
                    }
                  } catch (decodeErr) {
                    console.error('❌ [TTS] Audio decode error:', decodeErr);
                  }
                }
              }

              if (data.isFinal) {
                console.log('🏁 [TTS] Received isFinal signal');
                ws.close();
              }
            } catch (err) {
              console.error('❌ [TTS] Message processing error:', err);
            }
          });

          ws.addEventListener('error', (event) => {
            console.error('❌ [WebSocket] Error event:', event);
            console.error('❌ [WebSocket] ReadyState:', ws.readyState);
            clearTimeout(safetyTimeout);
            clearTimeout(connectionTimeout);
            setError('Failed to connect to speech service');
            setIsSpeaking(false);
            if (resolveCompleteRef.current) {
              reject(new Error('WebSocket error'));
              resolveCompleteRef.current = null;
            }
          });

          ws.addEventListener('close', (event) => {
            console.log('🔌 [WebSocket] Connection closed');
            console.log(
              '🔌 [WebSocket] Close code:',
              event.code,
              'reason:',
              event.reason
            );
            clearTimeout(safetyTimeout);
            clearTimeout(connectionTimeout);
            wsClosedRef.current = true;
            wsRef.current = null;

            // Check if playback is complete
            checkIfComplete();
          });
        } catch (err) {
          clearTimeout(safetyTimeout);
          console.error('❌ [TTS] Stream error:', err);
          setError(
            err instanceof Error ? err.message : 'Failed to stream audio'
          );
          setIsSpeaking(false);
          reject(err);
        }
      });
    },
    [playNextAudio, checkIfComplete]
  );

  const stopSpeaking = useCallback(() => {
    console.log('🛑 [TTS] Stopping speech');

    // Close WebSocket
    if (wsRef.current) {
      try {
        wsRef.current.close();
      } catch {}
      wsRef.current = null;
    }

    // Stop current audio
    if (currentSourceRef.current) {
      try {
        currentSourceRef.current.stop();
      } catch {}
      currentSourceRef.current = null;
    }

    // Clear queue and state
    audioQueueRef.current = [];
    isPlayingRef.current = false;
    wsClosedRef.current = true;
    setIsSpeaking(false);

    // Resolve any pending promise
    if (resolveCompleteRef.current) {
      resolveCompleteRef.current();
      resolveCompleteRef.current = null;
    }
  }, []);

  // Initialize AudioContext and cleanup
  useEffect(() => {
    audioContextRef.current = new AudioContext();
    return () => {
      stopSpeaking();
      audioContextRef.current?.close();
    };
  }, [stopSpeaking]);

  return {
    isSpeaking,
    speak,
    stopSpeaking,
    error,
  };
}
