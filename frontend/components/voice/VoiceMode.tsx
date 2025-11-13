"use client";

import { AnimatePresence } from "framer-motion";
import VoiceTransition from "./VoiceTransition";
import VoiceMascot from "./VoiceMascot";
import WaveformVisualizer from "./WaveformVisualizer";
import TranscriptionDisplay from "./TranscriptionDisplay";
import VoiceControls from "./VoiceControls";

import { useVoice } from "@/hooks/useVoice";
import { useEffect, useRef, useState } from "react";
import VoiceBackground from "../backgrounds/VoiceBackground";

interface VoiceModeProps {
  isActive: boolean;
  onClose: () => void;
}

export default function VoiceMode({ isActive, onClose }: VoiceModeProps) {
  const {
    isListening,
    isSpeaking,
    transcription,
    audioStream,
    startListening,
    stopListening,
    speak,
    stopSpeaking,
  } = useVoice();

  // Track if we need to re-enable listening after TTS finishes
  const [queueNextListen, setQueueNextListen] = useState(false);

  const lastSpokenReply = useRef("");
  const lastProcessedTranscription = useRef("");
  const isProcessingRef = useRef(false);

  // Auto-start listening ONLY when mode opens
  useEffect(() => {
    if (isActive && !isListening && !isSpeaking) {
      startListening();
      lastSpokenReply.current = "";
      lastProcessedTranscription.current = "";
    }
  }, [isActive, isListening, isSpeaking, startListening]);

  const handleVoiceMessage = async (message: string) => {
    // Prevent processing duplicate or echo messages
    if (isProcessingRef.current) {
      console.log("⏭️ Skipping duplicate processing");
      return;
    }

    // Filter out messages that are echoes of our own TTS
    const lowerMessage = message.toLowerCase().trim();
    const lowerLastReply = lastSpokenReply.current.toLowerCase().trim();

    // ✅ FIX: Check if the incoming MESSAGE contains echo phrases
    if (lowerMessage.includes("i heard you say")) {
      console.log(
        '🔇 Echo detected (contains "i heard you say"), ignoring:',
        message
      );
      return;
    }

    // Additional echo pattern: "how can i help you with"
    if (lowerMessage.includes("how can i help you with")) {
      console.log(
        "🔇 Echo detected (contains response pattern), ignoring:",
        message
      );
      return;
    }

    // Check for partial matches (the mic might have caught part of TTS)
    if (
      lowerLastReply &&
      lowerMessage.length > 10 &&
      lowerLastReply.includes(lowerMessage)
    ) {
      console.log("🔇 Partial echo detected, ignoring:", message);
      return;
    }

    // Ignore very short messages that are likely noise
    if (lowerMessage.length < 3) {
      console.log("🔇 Message too short, ignoring:", message);
      return;
    }

    try {
      isProcessingRef.current = true;
      console.log("📤 Sending voice message:", message);

      // ✅ CRITICAL: Stop listening immediately to prevent echo
      stopListening();

      const response = await fetch("/api/voice-stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message }),
      });

      const data = await response.json();

      if (data.response && data.shouldSpeak) {
        speak(data.response); // TTS playback
        lastSpokenReply.current = data.response;
        setQueueNextListen(true); // queue next mic activation after reply
      }
    } catch (error) {
      console.error("❌ Failed to process voice message:", error);
    } finally {
      isProcessingRef.current = false;
    }
  };

  // Re-enable listening after TTS completes (with delay to prevent echo)
  useEffect(() => {
    if (queueNextListen && !isSpeaking) {
      console.log(
        "⏰ TTS finished. Waiting 1500ms before re-enabling microphone (echo prevention)"
      );

      // Add delay to ensure audio has completely stopped and no echo remains
      const timer = setTimeout(() => {
        console.log("✅ Delay complete, re-enabling microphone");
        lastProcessedTranscription.current = "";
        startListening();
        setQueueNextListen(false);
      }, 1500); // 1500ms delay to prevent echo pickup

      return () => clearTimeout(timer);
    }
  }, [isSpeaking, queueNextListen, startListening]);

  // Process transcription when it's ready
  useEffect(() => {
    if (
      transcription &&
      !isListening &&
      !isSpeaking &&
      transcription !== lastProcessedTranscription.current &&
      transcription.trim().length > 0
    ) {
      console.log("🎤 New transcription received:", transcription);
      console.log("   Last processed:", lastProcessedTranscription.current);
      console.log(
        "   Will process:",
        transcription !== lastProcessedTranscription.current
      );

      lastProcessedTranscription.current = transcription;
      handleVoiceMessage(transcription);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [transcription, isListening, isSpeaking]);

  const handleClose = () => {
    stopListening();
    stopSpeaking();
    onClose();
    setQueueNextListen(false);
  };

  return (
    <AnimatePresence>
      {isActive && (
        <VoiceTransition isAnimating={isActive}>
          <div className="fixed inset-0 z-50 flex">
            {/* Voice Experience Area */}
            <div className="flex-1 relative">
              <VoiceBackground />

              <div className="relative z-10 h-full flex flex-col items-center justify-center p-8">
                {/* Animated Mascot */}
                <VoiceMascot
                  status={
                    isSpeaking ? "speaking" : isListening ? "listening" : "idle"
                  }
                  className="mb-12"
                />

                {/* Waveform Visualization */}
                <WaveformVisualizer
                  audioStream={audioStream}
                  isActive={isListening || isSpeaking}
                  className="mb-8"
                />

                {/* Live Transcription */}
                <TranscriptionDisplay
                  text={transcription}
                  isListening={isListening}
                  className="mb-12"
                />

                {/* Controls */}
                <VoiceControls
                  isListening={isListening}
                  onToggle={isListening ? stopListening : startListening}
                  onEnd={handleClose}
                />
              </div>
            </div>
          </div>
        </VoiceTransition>
      )}
    </AnimatePresence>
  );
}
