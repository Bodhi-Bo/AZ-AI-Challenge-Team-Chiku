'use client';

import { useState, useRef, useCallback, useEffect } from 'react';

interface UseElevenLabsStreamReturn {
  isConnected: boolean;
  isSpeaking: boolean;
  streamText: (text: string) => void;
  stopSpeaking: () => void;
  error: string | null;
}

export function useElevenLabsStream(): UseElevenLabsStreamReturn {
  const [isConnected, setIsConnected] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const audioQueueRef = useRef<AudioBuffer[]>([]);
  const isPlayingRef = useRef(false);

  // Initialize AudioContext
  useEffect(() => {
    audioContextRef.current = new AudioContext();
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
      audioContextRef.current?.close();
    };
  }, []);

  // ✅ FIX: Provide initial value (empty function)
  const playNextAudioRef = useRef<() => void>(() => {});

  const playNextAudio = useCallback(() => {
    console.log('[playNextAudio] Called - isPlaying:', isPlayingRef.current, 'queueLength:', audioQueueRef.current.length);
    if (isPlayingRef.current || audioQueueRef.current.length === 0) return;
    if (!audioContextRef.current) return;

    isPlayingRef.current = true;
    const audioBuffer = audioQueueRef.current.shift()!;
    console.log('[playNextAudio] Playing audio buffer, remaining in queue:', audioQueueRef.current.length);

    const source = audioContextRef.current.createBufferSource();
    source.buffer = audioBuffer;
    source.connect(audioContextRef.current.destination);

    source.onended = () => {
      console.log('[playNextAudio] Audio ended, remaining in queue:', audioQueueRef.current.length);
      isPlayingRef.current = false;
      if (audioQueueRef.current.length > 0) {
        playNextAudioRef.current();  // ✅ No optional chaining needed
      } else {
        console.log('[playNextAudio] Queue empty, stopping speech');
        setIsSpeaking(false);
      }
    };

    source.start();
  }, []);

  // Update ref when function changes
  useEffect(() => {
    playNextAudioRef.current = playNextAudio;
  }, [playNextAudio]);

  const streamText = useCallback(async (text: string) => {
    console.log('[streamText] Called with text:', text.substring(0, 50) + '...');
    if (!text.trim()) {
      console.log('[streamText] Empty text, aborting');
      return;
    }

    setIsSpeaking(true);
    setError(null);


const voiceId = process.env.NEXT_PUBLIC_ELEVENLABS_VOICE_ID;
const modelId = process.env.NEXT_PUBLIC_ELEVENLABS_MODEL_ID;
const apiKey = process.env.NEXT_PUBLIC_ELEVENLABS_API_KEY;

    console.log('[streamText] Config - voiceId:', voiceId, 'modelId:', modelId, 'apiKey:', apiKey ? 'present' : 'missing');

    if (!apiKey) {
      console.error('[streamText] API key missing');
      setError('ElevenLabs API key not found');
      setIsSpeaking(false);
      return;
    }

   const wsUrl = `wss://api.elevenlabs.io/v1/text-to-speech/${voiceId}/stream-input?model_id=${modelId}&xi-api-key=${apiKey}`;


   console.log('[streamText] wsUrl: ', wsUrl);
    try {
      console.log('[streamText] Creating WebSocket connection...');
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.addEventListener('open', () => {
  const initMessage = {
    text: ' ',
    xi_api_key: apiKey,
    voice_settings: {
      stability: 0.5,
      similarity_boost: 0.8,
      style: 0.7,
      use_speaker_boost: true
    },
    generation_config: {
      chunk_length_schedule: [120, 160, 250, 290]
    }
  };
  ws.send(JSON.stringify(initMessage));

  ws.send(JSON.stringify({ text, xi_api_key: apiKey }));
  ws.send(JSON.stringify({ text: '', xi_api_key: apiKey }));
});

      ws.addEventListener('message', async (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log('[WebSocket] Message received:', { hasAudio: !!data.audio, isFinal: data.isFinal, keys: Object.keys(data) });

          if (data.audio) {
            console.log('[WebSocket] Processing audio chunk, size:', data.audio.length);
            const audioData = atob(data.audio);
            const arrayBuffer = new Uint8Array(audioData.length);
            for (let i = 0; i < audioData.length; i++) {
              arrayBuffer[i] = audioData.charCodeAt(i);
            }

            if (audioContextRef.current) {
              const audioBuffer = await audioContextRef.current.decodeAudioData(
                arrayBuffer.buffer
              );
              audioQueueRef.current.push(audioBuffer);
              console.log('[WebSocket] Audio buffer decoded and queued. Queue length:', audioQueueRef.current.length);

              if (!isPlayingRef.current) {
                console.log('[WebSocket] Starting playback');
                playNextAudio();
              }
            }
          }

          if (data.isFinal) {
            console.log('✅ [WebSocket] Audio stream complete (isFinal received)');
            ws.close();
          }
        } catch (err) {
          console.error('❌ [WebSocket] Error processing audio:', err);
        }
      });

      ws.addEventListener('error', (err) => {
        console.error('❌ [WebSocket] Error:', err);
        setError('Failed to connect to speech service');
        setIsSpeaking(false);
        setIsConnected(false);
      });

      ws.addEventListener('close', (event) => {
        console.log('🔌 [WebSocket] Closed - Code:', event.code, 'Reason:', event.reason, 'Clean:', event.wasClean);
        setIsConnected(false);
      });

    } catch (err) {
      console.error('❌ [streamText] Stream error:', err);
      setError(err instanceof Error ? err.message : 'Failed to stream audio');
      setIsSpeaking(false);
    }
  }, [playNextAudio]);

  const stopSpeaking = useCallback(() => {
    console.log('[stopSpeaking] Called - Closing WebSocket and clearing queue');
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    // Stop any currently playing audio
    if (audioContextRef.current) {
      try {
        audioContextRef.current.suspend();
      } catch (e) {
        console.error('[stopSpeaking] Error suspending audio context:', e);
      }
    }

    audioQueueRef.current = [];
    isPlayingRef.current = false;
    setIsSpeaking(false);
    setIsConnected(false);
    console.log('[stopSpeaking] Cleanup complete');
  }, []);

  return {
    isConnected,
    isSpeaking,
    streamText,
    stopSpeaking,
    error
  };
}
