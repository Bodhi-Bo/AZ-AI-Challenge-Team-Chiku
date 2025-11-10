/**
 * Text-to-Speech utility using Web Speech API
 */

import { useState, useEffect, useCallback, useRef } from 'react';

interface UseTextToSpeechReturn {
  speak: (text: string) => void;
  stop: () => void;
  isSpeaking: boolean;
  voices: SpeechSynthesisVoice[];
  selectedVoice: SpeechSynthesisVoice | null;
  setVoice: (voice: SpeechSynthesisVoice) => void;
}

const CHUNK_LENGTH = 200; // Maximum characters per chunk

export function useTextToSpeech(): UseTextToSpeechReturn {
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [voices, setVoices] = useState<SpeechSynthesisVoice[]>([]);
  const [selectedVoice, setSelectedVoice] = useState<SpeechSynthesisVoice | null>(null);
  
  const utteranceRef = useRef<SpeechSynthesisUtterance | null>(null);
  const chunksRef = useRef<string[]>([]);
  const currentChunkIndexRef = useRef(0);

  // Load voices on mount
  useEffect(() => {
    const loadVoices = () => {
      const availableVoices = window.speechSynthesis.getVoices();
      setVoices(availableVoices);
      
      // Select a friendly English voice by default
      if (!selectedVoice && availableVoices.length > 0) {
        const preferredVoice =
          availableVoices.find(
            (voice) =>
              voice.lang.startsWith('en') &&
              (voice.name.includes('Google') ||
                voice.name.includes('Natural') ||
                voice.name.includes('Samantha') ||
                voice.name.includes('Alex'))
          ) || availableVoices.find((voice) => voice.lang.startsWith('en')) || availableVoices[0];
        
        setSelectedVoice(preferredVoice);
      }
    };

    loadVoices();
    
    // Some browsers load voices asynchronously
    if (window.speechSynthesis.onvoiceschanged !== undefined) {
      window.speechSynthesis.onvoiceschanged = loadVoices;
    }
  }, [selectedVoice]);

  const speakChunk = useCallback((chunk: string, index: number, total: number) => {
    if (!window.speechSynthesis) {
      console.error('Speech synthesis not supported');
      return;
    }

    // Cancel any ongoing speech
    window.speechSynthesis.cancel();

    const utterance = new SpeechSynthesisUtterance(chunk);
    
    // Configure voice settings
    if (selectedVoice) {
      utterance.voice = selectedVoice;
    }
    utterance.rate = 0.9;
    utterance.pitch = 1.1;
    utterance.volume = 1;

    utterance.onstart = () => {
      if (index === 0) {
        setIsSpeaking(true);
      }
    };

    utterance.onend = () => {
      // Speak next chunk if available
      if (index < total - 1) {
        speakChunk(chunksRef.current[index + 1], index + 1, total);
      } else {
        setIsSpeaking(false);
        chunksRef.current = [];
        currentChunkIndexRef.current = 0;
      }
    };

    utterance.onerror = (event) => {
      console.error('Speech synthesis error:', event);
      setIsSpeaking(false);
      chunksRef.current = [];
      currentChunkIndexRef.current = 0;
    };

    utteranceRef.current = utterance;
    window.speechSynthesis.speak(utterance);
  }, [selectedVoice]);

  const speak = useCallback((text: string) => {
    if (!text.trim()) return;

    // Stop any ongoing speech
    stop();

    // Split text into chunks if too long
    if (text.length > CHUNK_LENGTH) {
      const words = text.split(' ');
      chunksRef.current = [];
      let currentChunk = '';

      for (const word of words) {
        if ((currentChunk + ' ' + word).length <= CHUNK_LENGTH) {
          currentChunk += (currentChunk ? ' ' : '') + word;
        } else {
          if (currentChunk) {
            chunksRef.current.push(currentChunk);
          }
          currentChunk = word;
        }
      }
      
      if (currentChunk) {
        chunksRef.current.push(currentChunk);
      }

      currentChunkIndexRef.current = 0;
      speakChunk(chunksRef.current[0], 0, chunksRef.current.length);
    } else {
      chunksRef.current = [text];
      speakChunk(text, 0, 1);
    }
  }, [speakChunk]);

  const stop = useCallback(() => {
    if (window.speechSynthesis) {
      window.speechSynthesis.cancel();
    }
    setIsSpeaking(false);
    chunksRef.current = [];
    currentChunkIndexRef.current = 0;
  }, []);

  return {
    speak,
    stop,
    isSpeaking,
    voices,
    selectedVoice,
    setVoice: setSelectedVoice,
  };
}

