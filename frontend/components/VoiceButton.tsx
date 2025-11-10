"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Mic, MicOff } from "lucide-react";
import { useSpeechToText } from "@/lib/speechToText";
import { useStore } from "@/lib/store";
import { useMascot } from "@/lib/mascotStore";
import { Card } from "@/components/ui/card";
import { toast } from "sonner";

export default function VoiceButton() {
  const [showTranscript, setShowTranscript] = useState(false);
  const { setListening, addMessage } = useStore();
  const { think, setEmotion } = useMascot();

  const {
    transcript,
    isListening: isListeningState,
    startListening,
    stopListening,
    error,
  } = useSpeechToText({
    onFinalTranscript: async (finalTranscript) => {
      if (finalTranscript.trim()) {
        // Mascot starts thinking
        think();

        // Add user message
        const userMessage = {
          id: Date.now().toString(),
          role: "user" as const,
          content: finalTranscript,
          timestamp: new Date(),
          isVoice: true,
        };
        addMessage(userMessage);

        // Send to API
        try {
          const response = await fetch("/api/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              message: finalTranscript,
            }),
          });

          if (!response.ok) {
            throw new Error("Failed to get response");
          }

          const data = await response.json();

          // Add assistant message
          const assistantMessage = {
            id: (Date.now() + 1).toString(),
            role: "assistant" as const,
            content: data.reply,
            timestamp: new Date(),
          };
          addMessage(assistantMessage);

          // Mascot shows happy emotion
          setEmotion("happy");
          setTimeout(() => setEmotion("idle"), 3000);
        } catch (err) {
          console.error("Error sending message:", err);
          toast.error("Failed to send message. Please try again.");

          // Mascot shows tired/error emotion
          setEmotion("tired");
          setTimeout(() => setEmotion("idle"), 3000);
        }
      }
      setShowTranscript(false);
    },
    autoStopTimeout: 10000,
  });

  // Sync listening state
  useEffect(() => {
    setListening(isListeningState);
  }, [isListeningState, setListening]);

  // Show error toast
  useEffect(() => {
    if (error) {
      toast.error(error);
    }
  }, [error]);

  // Show transcript when listening
  useEffect(() => {
    setShowTranscript(isListeningState && transcript.length > 0);
  }, [isListeningState, transcript]);

  const handleToggle = () => {
    if (isListeningState) {
      stopListening();
      setShowTranscript(false);
    } else {
      startListening();
    }
  };

  return (
    <div className="flex flex-col items-center gap-2">
      {/* Transcript card */}
      <AnimatePresence>
        {showTranscript && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 10 }}
            className="mb-2"
          >
            <Card className="px-4 py-2 bg-white dark:bg-gray-800 shadow-lg">
              <p className="text-sm text-gray-700 dark:text-gray-300 max-w-xs">
                {transcript || "Listening..."}
              </p>
            </Card>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Voice button */}
      <motion.button
        onClick={handleToggle}
        className={`
          relative w-20 h-20 rounded-full flex items-center justify-center
          shadow-lg transition-all duration-300
          ${
            isListeningState
              ? "bg-gradient-to-br from-red-500 to-red-600"
              : "bg-gradient-to-br from-indigo-500 to-indigo-600"
          }
          hover:scale-105 active:scale-95
          focus:outline-none focus:ring-4 focus:ring-indigo-300 dark:focus:ring-indigo-800
        `}
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        animate={
          isListeningState
            ? {
                scale: [1, 1.1, 1],
              }
            : {}
        }
        transition={{
          duration: 1.5,
          repeat: isListeningState ? Infinity : 0,
          ease: "easeInOut",
        }}
        aria-label={isListeningState ? "Stop listening" : "Start listening"}
      >
        {isListeningState ? (
          <MicOff className="h-8 w-8 text-white" />
        ) : (
          <Mic className="h-8 w-8 text-white" />
        )}

        {/* Ripple effect */}
        {isListeningState && (
          <motion.div
            className="absolute inset-0 rounded-full border-2 border-red-400"
            animate={{
              scale: [1, 1.5, 2],
              opacity: [0.8, 0.4, 0],
            }}
            transition={{
              duration: 2,
              repeat: Infinity,
              ease: "easeOut",
            }}
          />
        )}
      </motion.button>

      {/* Listening text */}
      {isListeningState && (
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="text-sm text-gray-600 dark:text-gray-400"
        >
          Listening...
        </motion.p>
      )}
    </div>
  );
}
