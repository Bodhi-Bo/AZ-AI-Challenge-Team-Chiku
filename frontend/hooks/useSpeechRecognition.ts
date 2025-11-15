'use client';

import { useCallback, useRef, useState } from "react";

export function useSpeechRecognition() {
  const [transcript, setTranscript] = useState('');
  const [isListening, setIsListening] = useState(false);
  const [isFinal, setIsFinal] = useState(false);

  const recognitionRef = useRef<any>(null);
  const silenceTimerRef = useRef<NodeJS.Timeout | null>(null);
  const lastSentTranscriptRef = useRef('');

  const startListening = useCallback(() => {
    const SpeechRecognition =
      (window as any).SpeechRecognition ||
      (window as any).webkitSpeechRecognition;

    if (!SpeechRecognition) {
      alert('Your browser does not support speech recognition');
      return;
    }

    const recognition = new SpeechRecognition();

    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'en-US';

    recognition.onresult = (event: any) => {
      let fullTranscript = '';

      for (let i = 0; i < event.results.length; i++) {
        const result = event.results[i];
        fullTranscript += result[0].transcript;

        if (result.isFinal) {
          fullTranscript += ' ';
        }
      }

      fullTranscript = fullTranscript.trim();
      setTranscript(fullTranscript);
      setIsFinal(false);

      console.log('📝 Transcript:', fullTranscript);

      if (silenceTimerRef.current) {
        clearTimeout(silenceTimerRef.current);
      }

      silenceTimerRef.current = setTimeout(() => {
        if (fullTranscript && fullTranscript !== lastSentTranscriptRef.current) {
          console.log('🔔 User stopped speaking - ready to send');
          lastSentTranscriptRef.current = fullTranscript;
          setIsFinal(true);
        }
      }, 2000);
    };

    recognition.onend = () => {
      console.log('🛑 Recognition ended');
      setIsListening(false);

      if (silenceTimerRef.current) {
        clearTimeout(silenceTimerRef.current);
      }
    };

    recognition.onerror = (event: any) => {
      console.error('Recognition error:', event.error);
    };

    recognition.start();

    recognitionRef.current = recognition;
    setIsListening(true);
    setTranscript('');
    setIsFinal(false);
    lastSentTranscriptRef.current = '';
    console.log('🎤 Started listening...');
  }, []);

  const stopListening = useCallback(() => {
    if (recognitionRef.current) {
      recognitionRef.current.stop();
      setIsListening(false);
      console.log('🛑 Stopped listening');

      if (silenceTimerRef.current) {
        clearTimeout(silenceTimerRef.current);
      }

      lastSentTranscriptRef.current = '';
    }
  }, []);

  const resetTranscript = useCallback(() => {
    setTranscript('');
    setIsFinal(false);
  }, []);

  return {
    transcript,
    isListening,
    isFinal,
    startListening,
    stopListening,
    resetTranscript
  };
}
