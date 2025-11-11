"use client";

import { useState, useRef, useEffect } from "react";
import { Send, Mic, MicOff, X, Volume2, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useStore } from "@/lib/store";
import { useMascot } from "@/lib/mascotStore";
import { useSpeechToText } from "@/lib/speechToText";
import { useTextToSpeechElevenlabs } from "@/lib/useTextToSpeechElevenlabs";
import ChatMessage from "./ChatMessage";
import { toast } from "sonner";
import { motion, AnimatePresence } from "framer-motion";
import Image from "next/image";

// Emotion image mapping
const emotionImageMap: Record<string, string> = {
  idle: "Neutral peaceful,.jpg",
  happy: "Happy.jpg",
  thinking: "Gentle.jpg",
  celebrating: "Happy and surprised.jpg",
  tired: "Slightly uneasy.jpg",
  encouraging: "Winking.jpg",
  sleeping: "Gentle.jpg",
};

export default function ChatInterface() {
  const { messages, addMessage, setListening, setSpeaking } = useStore();
  const { emotion, setEmotion, think } = useMascot();
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [voiceMode, setVoiceMode] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // ElevenLabs text-to-speech
  const { speak, stop: stopSpeaking, isSpeaking } = useTextToSpeechElevenlabs();

  // Sync speaking state
  useEffect(() => {
    setSpeaking(isSpeaking);
  }, [isSpeaking, setSpeaking]);

  // Animate mascot mouth while speaking
  useEffect(() => {
    if (isSpeaking) {
      let toggle = true;
      const mouthInterval = setInterval(() => {
        setEmotion((prev) => {
          // Keep special emotions during speaking
          if (
            prev === "celebrating" ||
            prev === "encouraging" ||
            prev === "thinking"
          ) {
            return prev;
          }
          // Alternate between happy and idle for mouth movement
          toggle = !toggle;
          return toggle ? "happy" : "idle";
        });
      }, 300);

      return () => clearInterval(mouthInterval);
    }
  }, [isSpeaking, setEmotion]);

  // Add dummy conversation on mount
  useEffect(() => {
    if (messages.length === 0) {
      const baseTime = Date.now();
      const dummyMessages = [
        {
          id: `msg-${baseTime - 120000}`,
          role: "assistant" as const,
          content:
            "Hi! I'm Chiku, your ADHD-friendly study buddy! 👋\n\nI can help you break down tasks, manage your schedule, and stay focused. What would you like to work on today?",
          timestamp: new Date(baseTime - 120000),
        },
        {
          id: `msg-${baseTime - 60000}`,
          role: "user" as const,
          content:
            "I have a research paper due Friday and I'm feeling overwhelmed",
          timestamp: new Date(baseTime - 60000),
        },
        {
          id: `msg-${baseTime - 30000}`,
          role: "assistant" as const,
          content:
            "I totally understand! Let's break this down together. 💪\n\nFirst, let's start small:\n1. What's your paper topic?\n2. How many pages do you need?\n3. Have you started any research yet?\n\nWe'll take it one step at a time!",
          timestamp: new Date(baseTime - 30000),
        },
      ];

      dummyMessages.forEach((msg) => addMessage(msg));
      setEmotion("encouraging");
      setTimeout(() => setEmotion("idle"), 2000);
    }
  }, [addMessage, setEmotion]);

  // Debug emotion changes
  useEffect(() => {
    console.log("🎭 Emotion changed to:", emotion);
  }, [emotion]);

  // Speech to text
  const {
    isListening: isListeningState,
    startListening,
    stopListening,
  } = useSpeechToText({
    onFinalTranscript: async (transcript) => {
      if (transcript.trim()) {
        await handleVoiceMessage(transcript);
      }
    },
  });

  useEffect(() => {
    setListening(isListeningState);
  }, [isListeningState, setListening]);

  // Auto-scroll
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleVoiceMessage = async (text: string) => {
    // Stop listening immediately
    stopListening();

    // Show thinking emotion
    think();

    const userMessage = {
      id: `msg-${Date.now()}`,
      role: "user" as const,
      content: text,
      timestamp: new Date(),
      isVoice: true,
    };
    addMessage(userMessage);

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text }),
      });

      if (!response.ok) throw new Error("Failed");

      const data = await response.json();

      const assistantMessage = {
        id: `msg-${Date.now() + 1}`,
        role: "assistant" as const,
        content: data.reply,
        timestamp: new Date(),
      };
      addMessage(assistantMessage);

      // Detect emotion from response BEFORE speaking
      const lowerReply = data.reply.toLowerCase();
      if (
        lowerReply.includes("great") ||
        lowerReply.includes("awesome") ||
        lowerReply.includes("excellent")
      ) {
        setEmotion("celebrating");
      } else if (
        lowerReply.includes("think") ||
        lowerReply.includes("consider")
      ) {
        setEmotion("thinking");
      } else if (
        lowerReply.includes("understand") ||
        lowerReply.includes("help")
      ) {
        setEmotion("encouraging");
      } else {
        setEmotion("happy");
      }

      // Speak response with ElevenLabs
      await speak(data.reply);

      // Return to idle after speaking
      setTimeout(() => {
        setEmotion("idle");
        if (voiceMode) {
          toast("Click mic when ready to speak again", {
            duration: 3000,
            icon: "🎙️",
          });
        }
      }, 1000);
    } catch (err) {
      console.error("Voice message error:", err);
      toast.error("Failed to process message");
      setEmotion("tired");
      setTimeout(() => setEmotion("idle"), 3000);
    }
  };

  const toggleVoiceMode = async () => {
    if (voiceMode) {
      // STOP VOICE MODE
      stopListening();
      stopSpeaking();
      setVoiceMode(false);
      setEmotion("idle");
      toast.success("Voice mode disabled");
    } else {
      // START VOICE MODE
      setVoiceMode(true);
      setEmotion("happy");

      // Speak greeting message
      const greeting = "Hi! I'm ready to help. What would you like to work on?";
      await speak(greeting);

      // Wait for greeting to finish
      setTimeout(() => {
        setEmotion("idle");
        toast.success("Click mic to start talking", { duration: 3000 });
      }, 2000);
    }
  };

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage = {
      id: `msg-${Date.now()}`,
      role: "user" as const,
      content: input.trim(),
      timestamp: new Date(),
    };

    addMessage(userMessage);
    setInput("");
    setIsLoading(true);
    think();

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: userMessage.content }),
      });

      if (!response.ok) throw new Error("Failed");

      const data = await response.json();

      const assistantMessage = {
        id: `msg-${Date.now() + 1}`,
        role: "assistant" as const,
        content: data.reply,
        timestamp: new Date(),
      };

      addMessage(assistantMessage);

      // Change emotion based on response
      const lowerReply = data.reply.toLowerCase();
      if (lowerReply.includes("great") || lowerReply.includes("awesome")) {
        setEmotion("celebrating");
      } else if (
        lowerReply.includes("understand") ||
        lowerReply.includes("help")
      ) {
        setEmotion("encouraging");
      } else {
        setEmotion("happy");
      }

      // Speak response
      await speak(data.reply);

      setTimeout(() => {
        if (!isSpeaking) setEmotion("idle");
      }, 1000);
    } catch (err) {
      console.error("Send message error:", err);
      toast.error("Failed to send message");
      setEmotion("tired");
      setTimeout(() => setEmotion("idle"), 3000);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full w-full bg-gradient-to-br from-gray-50 to-white dark:from-gray-900 dark:to-gray-800 relative">
      {/* Voice Mode - Full Screen Overlay */}
      <AnimatePresence>
        {voiceMode && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 z-50 bg-gradient-to-br from-indigo-50 via-purple-50 to-pink-50 dark:from-gray-900 dark:via-indigo-900 dark:to-purple-900 flex flex-col items-center justify-center"
          >
            {/* Close button */}
            <button
              onClick={toggleVoiceMode}
              className="absolute top-6 right-6 w-10 h-10 rounded-full bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm flex items-center justify-center hover:bg-white dark:hover:bg-gray-800 transition-colors shadow-lg"
              aria-label="Close voice mode"
            >
              <X className="w-5 h-5" />
            </button>

            {/* Large Centered Mascot */}
            <motion.div
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              className="relative"
            >
              {/* Listening pulse effect */}
              {isListeningState && !isSpeaking && (
                <motion.div
                  className="absolute inset-0 rounded-full bg-indigo-400/30"
                  animate={{
                    scale: [1, 1.3, 1],
                    opacity: [0.5, 0, 0.5],
                  }}
                  transition={{
                    duration: 2,
                    repeat: Infinity,
                  }}
                />
              )}

              {/* Speaking wave effect */}
              {isSpeaking && (
                <div className="absolute inset-0">
                  {[0, 1, 2].map((i) => (
                    <motion.div
                      key={i}
                      className="absolute inset-0 rounded-full border-4 border-green-400"
                      animate={{
                        scale: [1, 1.5, 2],
                        opacity: [0.8, 0.4, 0],
                      }}
                      transition={{
                        duration: 2,
                        repeat: Infinity,
                        delay: i * 0.6,
                      }}
                    />
                  ))}
                </div>
              )}

              {/* Mascot */}
              <motion.div
                className="w-64 h-64 rounded-full overflow-hidden bg-white dark:bg-gray-800 shadow-2xl relative z-10"
                animate={{
                  y: isListeningState || isSpeaking ? [0, -10, 0] : 0,
                  scale: isSpeaking ? [1, 1.05, 1] : 1,
                }}
                transition={{
                  duration: 2,
                  repeat: isListeningState || isSpeaking ? Infinity : 0,
                }}
              >
                <Image
                  src={`/mascot/${emotionImageMap[emotion]}`}
                  alt="Chiku"
                  width={256}
                  height={256}
                  className="object-cover"
                  priority
                />
              </motion.div>
            </motion.div>

            {/* Status Text */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="mt-8 text-center"
            >
              <h2 className="text-2xl font-bold text-gray-800 dark:text-white mb-2 flex items-center justify-center gap-2">
                {isSpeaking ? (
                  <>
                    <Volume2 className="w-6 h-6 animate-pulse" />
                    Speaking...
                  </>
                ) : isListeningState ? (
                  <>
                    <Mic className="w-6 h-6 animate-pulse" />I &apos;m
                    listening...
                  </>
                ) : (
                  "Click mic to speak"
                )}
              </h2>
              <p className="text-gray-600 dark:text-gray-300 max-w-md px-4">
                {isSpeaking
                  ? "Please wait while I respond..."
                  : isListeningState
                  ? "Speak naturally - I'm here to help!"
                  : "Ready when you are. Click the mic below."}
              </p>
            </motion.div>

            {/* Voice Button */}
            <motion.button
              onClick={() => {
                if (isSpeaking) {
                  toast("Please wait for me to finish speaking", {
                    icon: "⏳",
                  });
                  return;
                }

                if (isListeningState) {
                  stopListening();
                  setEmotion("idle");
                  toast("Stopped listening", { icon: "🎙️" });
                } else {
                  startListening();
                  setEmotion("happy");
                  toast("Listening... speak now!", { icon: "👂" });
                }
              }}
              disabled={isSpeaking}
              className={`mt-12 w-20 h-20 rounded-full flex items-center justify-center shadow-2xl transition-all ${
                isSpeaking
                  ? "bg-gradient-to-br from-gray-400 to-gray-500 cursor-not-allowed opacity-60"
                  : isListeningState
                  ? "bg-gradient-to-br from-red-500 to-pink-500"
                  : "bg-gradient-to-br from-indigo-500 to-purple-500"
              }`}
              whileHover={!isSpeaking ? { scale: 1.1 } : {}}
              whileTap={!isSpeaking ? { scale: 0.9 } : {}}
              animate={
                isListeningState && !isSpeaking ? { scale: [1, 1.1, 1] } : {}
              }
              transition={{
                duration: 1.5,
                repeat: isListeningState && !isSpeaking ? Infinity : 0,
              }}
            >
              {isSpeaking ? (
                <Volume2 className="w-10 h-10 text-white animate-pulse" />
              ) : isListeningState ? (
                <MicOff className="w-10 h-10 text-white" />
              ) : (
                <Mic className="w-10 h-10 text-white" />
              )}
            </motion.button>

            {/* Helper text */}
            <p className="mt-4 text-sm text-gray-600 dark:text-gray-300">
              {isSpeaking
                ? "Speaking... please wait"
                : isListeningState
                ? "Listening... click to stop"
                : "Click mic to speak"}
            </p>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Normal Chat Mode */}
      <div className="flex-1 flex flex-col min-h-0 overflow-hidden">
        {/* Messages - SCROLLABLE */}
        <div className="flex-1 overflow-y-auto">
          <ScrollArea className="h-full">
            <div className="space-y-4 py-6 px-6 max-w-3xl mx-auto">
              {messages.map((message) => (
                <ChatMessage
                  key={message.id}
                  message={message}
                  isLatest={false}
                />
              ))}

              {/* Loading indicator */}
              {isLoading && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="flex items-center gap-2 text-gray-500 dark:text-gray-400 px-4"
                >
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <span className="text-sm">Thinking...</span>
                </motion.div>
              )}

              {/* Speaking indicator */}
              {isSpeaking && !voiceMode && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="flex items-center gap-2 text-green-600 dark:text-green-400 px-4"
                >
                  <Volume2 className="h-4 w-4 animate-pulse" />
                  <span className="text-sm">Speaking...</span>
                </motion.div>
              )}

              <div ref={messagesEndRef} />
            </div>
          </ScrollArea>
        </div>

        {/* Input Area - FIXED AT BOTTOM */}
        <div className="flex-shrink-0 px-6 py-4 border-t border-gray-200 dark:border-gray-700 bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm">
          <div className="max-w-3xl mx-auto flex items-center gap-3">
            {/* Voice Mode Button */}
            <Button
              onClick={toggleVoiceMode}
              size="icon"
              variant={voiceMode ? "default" : "outline"}
              className="h-11 w-11 rounded-full flex-shrink-0"
              title={voiceMode ? "Exit voice mode" : "Enter voice mode"}
            >
              <Mic className="h-5 w-5" />
            </Button>

            {/* Text Input */}
            <Input
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  handleSend();
                }
              }}
              placeholder={
                voiceMode ? "Voice mode active..." : "Type your message..."
              }
              disabled={isLoading || voiceMode}
              className="flex-1 h-11 bg-white dark:bg-gray-800"
            />

            {/* Send Button */}
            <Button
              onClick={handleSend}
              disabled={!input.trim() || isLoading || voiceMode}
              size="icon"
              className="h-11 w-11 rounded-full flex-shrink-0"
              title="Send message"
            >
              {isLoading ? (
                <Loader2 className="h-5 w-5 animate-spin" />
              ) : (
                <Send className="h-5 w-5" />
              )}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
