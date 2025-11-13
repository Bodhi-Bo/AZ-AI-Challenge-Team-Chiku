"use client";

import { useEffect, useRef } from "react";
import { motion } from "framer-motion";
import { useAudioVisualization } from "@/hooks/useAudioVisualization";

interface WaveformVisualizerProps {
  audioStream: MediaStream | null;
  isActive: boolean;
  className?: string;
}

export default function WaveformVisualizer({
  audioStream,
  isActive,
  className = "",
}: WaveformVisualizerProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const { getFrequencyData, getAnalyser } = useAudioVisualization(audioStream);
  const animationFrameRef = useRef<number | undefined>(undefined); // ✅ Provide initial value

  useEffect(() => {
    const analyser = getAnalyser();
    if (!canvasRef.current || !isActive || !analyser) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const bufferLength = analyser.frequencyBinCount;

    const draw = () => {
      if (!isActive) return;

      const width = canvas.width;
      const height = canvas.height;

      ctx.clearRect(0, 0, width, height);

      // ✅ Get frequency data via function
      const dataArray = getFrequencyData();
      if (!dataArray) return;

      const barWidth = width / bufferLength;
      const gradient = ctx.createLinearGradient(0, 0, width, 0);
      gradient.addColorStop(0, "#667eea");
      gradient.addColorStop(0.5, "#764ba2");
      gradient.addColorStop(1, "#f093fb");

      for (let i = 0; i < bufferLength; i++) {
        const value = dataArray[i];
        const barHeight = (value / 255) * height * 0.8;
        const x = i * barWidth;
        const y = (height - barHeight) / 2;

        ctx.fillStyle = gradient;
        ctx.fillRect(x, y, barWidth - 2, barHeight);
      }

      animationFrameRef.current = requestAnimationFrame(draw);
    };

    draw();

    return () => {
      if (animationFrameRef.current !== undefined) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, [isActive, getFrequencyData, getAnalyser]);

  return (
    <motion.div
      className={`relative ${className}`}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <canvas
        ref={canvasRef}
        width={600}
        height={120}
        className="rounded-2xl"
        style={{
          background: "rgba(255, 255, 255, 0.05)",
          backdropFilter: "blur(10px)",
        }}
      />
    </motion.div>
  );
}
