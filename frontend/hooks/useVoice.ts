'use client';

import { useElevenLabsStream } from "@/components/voice/useElevenLabsStream";
import { useState, useRef, useCallback } from 'react';

export function useVoice() {
  const [isListening, setIsListening] = useState(false);
  const [transcription, setTranscription] = useState("");
  const [audioStream, setAudioStream] = useState<MediaStream | null>(null);

  const recognitionRef = useRef<SpeechRecognition | null>(null);
  const silenceTimerRef = useRef<NodeJS.Timeout | null>(null);

  // Use ElevenLabs for TTS
  const { isSpeaking, streamText, stopSpeaking, error: ttsError } = useElevenLabsStream();

    const stopListening = useCallback(() => {
    if (audioStream) {
      audioStream.getTracks().forEach(track => track.stop());
      setAudioStream(null);
    }
    if (recognitionRef.current) {
      recognitionRef.current.stop();
      recognitionRef.current = null;
    }
    if (silenceTimerRef.current) {
      clearTimeout(silenceTimerRef.current);
      silenceTimerRef.current = null;
    }
    setIsListening(false);
  }, [audioStream]);

  // Start listening: enables mic and sets up recognition, stops on pause or utterance end
  const startListening = useCallback(async () => {
    // ⚠️ CRITICAL: Don't start listening if TTS is speaking to prevent echo loop
    if (isSpeaking) {
      console.log('🔇 [startListening] Blocked: TTS is currently speaking');
      return;
    }

    try {
      // Get microphone access with echo cancellation
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true
        }
      });
      setAudioStream(stream);

      const SpeechRecognitionAPI = window.SpeechRecognition || window.webkitSpeechRecognition;
      if (SpeechRecognitionAPI) {
        const recognition = new SpeechRecognitionAPI();
        recognition.continuous = true;      // capture until pause
        recognition.interimResults = true;  // show real-time text

        recognition.onresult = (event: SpeechRecognitionEvent) => {
          // Reset the silence timer with each patch received
          if (silenceTimerRef.current) clearTimeout(silenceTimerRef.current);

          let finalTranscript = "";
          let interimTranscript = "";

          for (let i = event.resultIndex; i < event.results.length; i++) {
            const transcript = event.results[i][0].transcript;
            if (event.results[i].isFinal) {
              finalTranscript += transcript;
            } else {
              interimTranscript += transcript;
            }
          }

          // Display live text in UI
          setTranscription(interimTranscript || finalTranscript);

          // Detect "end": finalTranscript means user finished a phrase
          if (finalTranscript !== "") {
            setTranscription(finalTranscript);
            stopListening();      // stop on utterance end
            return;
          }

          // If user goes silent for 2 seconds, end recognition
          silenceTimerRef.current = setTimeout(() => {
            stopListening();
          }, 2000);
        };

        recognition.onend = () => {
          // STT has ended (user finished speaking or silent too long)
          if (silenceTimerRef.current) clearTimeout(silenceTimerRef.current);
        };

        recognition.onerror = () => {
          if (silenceTimerRef.current) clearTimeout(silenceTimerRef.current);
          stopListening();
        };

        recognition.start();
        recognitionRef.current = recognition;
        setIsListening(true);
      }
    } catch (error) {
      console.error('❌ Error starting voice:', error);
    }
  }, [stopListening, isSpeaking]);

  // Speak TTS
  const speak = useCallback((text: string) => {
    streamText(text);
  }, [streamText]);

  return {
    isListening,
    isSpeaking,
    transcription,
    audioStream,
    startListening,
    stopListening,
    speak,
    stopSpeaking,
    error: ttsError
  };
}
