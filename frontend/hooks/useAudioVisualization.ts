'use client';

import { useEffect, useRef, useCallback } from 'react';

interface AudioVisualizationData {
  getFrequencyData: () => Uint8Array | null;
  getAnalyser: () => AnalyserNode | null;
}

export function useAudioVisualization(audioStream: MediaStream | null): AudioVisualizationData {
  const analyserRef = useRef<AnalyserNode | null>(null);
  const frequencyDataRef = useRef<Uint8Array<ArrayBuffer> | null>(null);
  const animationFrameRef = useRef<number | undefined>(undefined);

  useEffect(() => {
    // Clean up previous state
    if (!audioStream) {
      analyserRef.current = null;
      frequencyDataRef.current = null;
      if (animationFrameRef.current !== undefined) {
        cancelAnimationFrame(animationFrameRef.current);
      }
      return;
    }

    const audioContext = new AudioContext();
    const analyser = audioContext.createAnalyser();
    const source = audioContext.createMediaStreamSource(audioStream);

    analyser.fftSize = 256;
    source.connect(analyser);

    const bufferLength = analyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);

    frequencyDataRef.current = dataArray;
    analyserRef.current = analyser;

    const updateFrequency = () => {
      if (analyserRef.current && frequencyDataRef.current) {
        // ✅ This will now work because dataArray is Uint8Array<ArrayBuffer>
        analyserRef.current.getByteFrequencyData(frequencyDataRef.current);
      }
      animationFrameRef.current = requestAnimationFrame(updateFrequency);
    };

    updateFrequency();

    return () => {
      if (animationFrameRef.current !== undefined) {
        cancelAnimationFrame(animationFrameRef.current);
      }
      source.disconnect();
      audioContext.close();
    };
  }, [audioStream]);

  // Return functions instead of refs directly
  const getFrequencyData = useCallback(() => {
    return frequencyDataRef.current;
  }, []);

  const getAnalyser = useCallback(() => {
    return analyserRef.current;
  }, []);

  return {
    getFrequencyData,
    getAnalyser
  };
}
