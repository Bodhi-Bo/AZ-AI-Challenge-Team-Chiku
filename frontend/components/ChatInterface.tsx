"use client";

import { useState, useRef, useEffect, KeyboardEvent } from "react";
import { Send, Trash2, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useStore } from "@/lib/store";
import { useTextToSpeech } from "@/lib/textToSpeech";
import { useMascot } from "@/lib/mascotStore";
import { useSpeechToText } from "@/lib/speechToText";
import ChatMessage from "./ChatMessage";
import ChikuMascot from "./ChikuMascot";
import { toast } from "sonner";
import { motion, AnimatePresence } from "framer-motion";

export default function ChatInterface() {
  const {
    messages,
    isSpeaking,
    isListening,
    setListening,
    addMessage,
    clearMessages,
  } = useStore();
  const { emotion, think, setEmotion } = useMascot();
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [voiceMode, setVoiceMode] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const { speak, stop: stopSpeaking } = useTextToSpeech();

  // Speech to text for voice mode
  const {
    isListening: isListeningState,
    startListening,
    stopListening,
  } = useSpeechToText({
    onFinalTranscript: async (finalTranscript) => {
      if (finalTranscript.trim() && voiceMode) {
        think();

        const userMessage = {
          id: Date.now().toString(),
          role: "user" as const,
          content: finalTranscript,
          timestamp: new Date(),
          isVoice: true,
        };
        addMessage(userMessage);

        try {
          const response = await fetch("/api/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              message: finalTranscript,
              conversationHistory: messages.slice(-5),
            }),
          });

          if (!response.ok) throw new Error("Failed to get response");

          const data = await response.json();

          const assistantMessage = {
            id: (Date.now() + 1).toString(),
            role: "assistant" as const,
            content: data.reply,
            timestamp: new Date(),
          };
          addMessage(assistantMessage);

          setEmotion("happy");

          // Speak response in voice mode
          if (voiceMode && data.reply) {
            await speak(data.reply);
          }

          setTimeout(() => setEmotion("idle"), 2000);

          // Continue listening in voice mode
          if (voiceMode) {
            setTimeout(() => startListening(), 500);
          }
        } catch (err) {
          console.error("Error:", err);
          toast.error("Failed to process message");
          setEmotion("tired");
          setTimeout(() => setEmotion("idle"), 3000);
        }
      }
    },
    autoStopTimeout: 10000,
  });

  // Auto-scroll
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Sync listening state
  useEffect(() => {
    setListening(isListeningState);
  }, [isListeningState, setListening]);

  // Handle mascot emotions
  useEffect(() => {
    if (isListening) {
      setEmotion("thinking");
    } else if (!isLoading && !isSpeaking && messages.length > 0) {
      const timer = setTimeout(() => setEmotion("idle"), 1000);
      return () => clearTimeout(timer);
    }
  }, [isListening, isLoading, isSpeaking, messages.length, setEmotion]);

  useEffect(() => {
    if (isSpeaking && !isLoading) {
      setEmotion("happy");
    }
  }, [isSpeaking, isLoading, setEmotion]);

  // Toggle voice mode
  const handleMascotClick = () => {
    if (voiceMode) {
      // Stop voice mode
      stopListening();
      stopSpeaking();
      setVoiceMode(false);
      setEmotion("idle");
      toast.success("Voice mode disabled");
    } else {
      // Start voice mode
      setVoiceMode(true);
      setEmotion("thinking");
      startListening();
      toast.success("Voice mode enabled - Click mascot again to stop");
    }
  };

  const handleSend = async () => {
    if (!input.trim() || isLoading || voiceMode) return;

    const userMessage = {
      id: Date.now().toString(),
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
        body: JSON.stringify({
          message: userMessage.content,
          conversationHistory: messages.slice(-5),
        }),
      });

      if (!response.ok) throw new Error("Failed to get response");

      const data = await response.json();

      const assistantMessage = {
        id: (Date.now() + 1).toString(),
        role: "assistant" as const,
        content: data.reply,
        timestamp: new Date(),
      };

      addMessage(assistantMessage);
      setEmotion("happy");

      if (!isSpeaking && data.reply) {
        speak(data.reply);
      }

      setTimeout(() => setEmotion("idle"), 3000);
    } catch (err) {
      console.error("Error sending message:", err);
      toast.error("Failed to send message. Please try again.");
      setEmotion("tired");
      setTimeout(() => setEmotion("idle"), 3000);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleClear = () => {
    if (confirm("Are you sure you want to clear all messages?")) {
      clearMessages();
      toast.success("Chat cleared");
    }
  };

  return (
    <div className="flex flex-col h-full bg-white dark:bg-gray-900">
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100 dark:border-gray-800 shrink-0">
        <div className="flex items-center gap-3">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
            Chiku
          </h2>
          <div className="flex items-center gap-2">
            <div className="h-2 w-2 rounded-full bg-green-500" />
            <span className="text-sm text-gray-500 dark:text-gray-400">
              {voiceMode ? "Voice Mode" : "Online"}
            </span>
          </div>
        </div>
        <Button
          variant="ghost"
          size="icon"
          onClick={handleClear}
          className="h-9 w-9"
          aria-label="Clear chat"
        >
          <Trash2 className="h-4 w-4" />
        </Button>
      </div>

      {/* Mascot Section - Clean White Background */}
      <div className="flex justify-center items-center py-8 shrink-0">
        <motion.div
          whileHover={{ scale: voiceMode ? 1 : 1.05 }}
          animate={voiceMode ? { scale: [1, 1.05, 1] } : {}}
          transition={voiceMode ? { duration: 2, repeat: Infinity } : {}}
        >
          <ChikuMascot
            emotion={emotion}
            size={160}
            showMessage={false}
            onClick={handleMascotClick}
          />
        </motion.div>
      </div>

      {/* Voice Mode Indicator */}
      <AnimatePresence>
        {voiceMode && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="px-6 pb-4 shrink-0"
          >
            <div className="bg-gradient-to-r from-indigo-50 to-purple-50 dark:from-indigo-900/20 dark:to-purple-900/20 rounded-xl p-4 border border-indigo-100 dark:border-indigo-800">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="h-3 w-3 rounded-full bg-red-500 animate-pulse" />
                  <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    Voice-to-Voice Active
                  </span>
                </div>
                <span className="text-xs text-gray-500 dark:text-gray-400">
                  Click mascot to stop
                </span>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Messages area - Scrollable */}
      <ScrollArea className="flex-1 px-6">
        <div className="space-y-4 py-4">
          {messages.map((message, index) => (
            <ChatMessage
              key={message.id}
              message={message}
              isLatest={index === messages.length - 1}
            />
          ))}

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

          <div ref={messagesEndRef} />
        </div>
      </ScrollArea>

      {/* Input area - Only show when not in voice mode */}
      <AnimatePresence>
        {!voiceMode && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 20 }}
            className="px-6 py-4 border-t border-gray-100 dark:border-gray-800 shrink-0"
          >
            <div className="flex items-center gap-3">
              <Input
                ref={inputRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Type your message..."
                disabled={isLoading}
                className="flex-1 h-11"
                aria-label="Message input"
              />
              <Button
                onClick={handleSend}
                disabled={!input.trim() || isLoading}
                size="icon"
                className="h-11 w-11 shrink-0"
                aria-label="Send message"
              >
                {isLoading ? (
                  <Loader2 className="h-5 w-5 animate-spin" />
                ) : (
                  <Send className="h-5 w-5" />
                )}
              </Button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
