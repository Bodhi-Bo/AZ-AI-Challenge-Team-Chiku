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

// ✅ SIMPLIFIED - Only 3 emotions
const emotionImageMap: Record<string, string> = {
  idle: "Neutral peaceful,.jpg", // Waving hand
  normal: "Happy.jpg", // Normal conversation (blinking, nodding)
  thinking: "Gentle.jpg", // Thinking/processing
};

// ✅ Dummy responses WITHOUT emotion field
const DUMMY_RESPONSES = [
  {
    text: "[giggles] That's a great question! [thoughtfully] Let me think about that for a moment... 🤔",
  },
  {
    text: "[excitedly] Oh wow! That's awesome! I love how you're thinking about this! 🎉 [happily]",
  },
  {
    text: "[confidently] You've got this! I believe in you! 💪 [encouragingly] Let's break it down into smaller steps.",
  },
  {
    text: "[thoughtfully] Hmm, interesting! Here's what I'm thinking... 🤓 [whispers] This could work really well!",
  },
  {
    text: "[excitedly] Yay! You're making such great progress! Keep it up! ✨ [happily]",
  },
  {
    text: "[empathetically] I totally understand how you feel. [softly] Let's work through this together, okay? 🫂",
  },
  {
    text: "[giggles] That's so relatable! [warmly] Here's what helps me with that... 😊",
  },
  {
    text: "[enthusiastically] Great idea! I think you're onto something really good here! 🌟 [excitedly]",
  },
  {
    text: "[excitedly] Let me help you organize that! [confidently] We can definitely make this work! 📝",
  },
  {
    text: "[thoughtfully] Ooh, I see what you mean! Let me suggest something... 💡 [whispers] This is a good approach.",
  },
  {
    text: "[proudly] You're doing amazing! [happily] Seriously, I'm so impressed with your progress! 🎊",
  },
  {
    text: "[empathetically] That sounds challenging. [encouragingly] But I know you can handle it! Let's plan it out. 💪",
  },
  {
    text: "[giggles softly] I love your creativity! [excitedly] Here's what we could try... ✨",
  },
  {
    text: "[excitedly] Perfect timing! I was just thinking about how to help with that! 🎯 [happily]",
  },
  {
    text: "[warmly] You know what? You're really getting the hang of this! [encouragingly] Keep going! 🌈",
  },
  {
    text: "[whispers] Let me tell you a secret... [giggles] Breaking tasks into tiny pieces makes them way less scary! 🤫",
  },
  {
    text: "[sighs contentedly] I love seeing you make progress like this! [happily] You're doing such a great job! 💝",
  },
  {
    text: "[thoughtfully] Hmm... [whispers] here's an idea that might help... [excitedly] Yes! This could work perfectly! 💡",
  },
  {
    text: "[giggles] Oops, looks like we have a little challenge here! [confidently] But that's totally okay, we'll figure it out together! 🌟",
  },
  {
    text: "[enthusiastically] This is so cool! [excitedly] I can't wait to see what you do with this! 🚀",
  },
];

let responseIndex = 0;

export default function ChatInterface() {
  const { messages, addMessage, setListening, setSpeaking } = useStore();
  const { emotion, setEmotion } = useMascot();
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

  // ✅ SINGLE EMOTION CONTROL - No rapid switching
  useEffect(() => {
    if (isLoading) {
      // Show thinking during API calls
      setEmotion("thinking");
    } else if (isListeningState && !isSpeaking) {
      // Show thinking when listening (before response)
      setEmotion("thinking");
    } else if (isSpeaking) {
      // Show happy when speaking
      setEmotion("happy");
    } else if (messages.length === 0) {
      // Show idle (waving) only on first load
      setEmotion("idle");
    } else {
      // Default to happy after conversation started
      setEmotion("happy");
    }
  }, [isLoading, isSpeaking, isListeningState, messages.length, setEmotion]);

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
    }
  }, [addMessage]);

  // Auto-scroll
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // ✅ Simplified voice message handler - NO manual emotion changes
  const handleVoiceMessage = async (text: string) => {
    console.log("🎤 Voice message received:", text);

    stopListening();
    // Emotion automatically becomes "thinking" via main useEffect

    const userMessage = {
      id: `msg-${Date.now()}`,
      role: "user" as const,
      content: text,
      timestamp: new Date(),
      isVoice: true,
    };
    addMessage(userMessage);

    // Simulate API delay
    await new Promise((resolve) => setTimeout(resolve, 1500));

    // Get dummy response
    const dummyResponse =
      DUMMY_RESPONSES[responseIndex % DUMMY_RESPONSES.length];
    responseIndex++;

    console.log("🤖 Dummy response:", dummyResponse.text);

    const assistantMessage = {
      id: `msg-${Date.now() + 1}`,
      role: "assistant" as const,
      content: dummyResponse.text,
      timestamp: new Date(),
    };
    addMessage(assistantMessage);

    // Speak response - emotion handled by main useEffect
    await speak(dummyResponse.text);

    // Show toast after speaking
    if (voiceMode) {
      toast("Click mic when ready to speak again", {
        duration: 3000,
        icon: "🎙️",
      });
    }
  };

  // ✅ Simplified voice mode toggle
  const toggleVoiceMode = async () => {
    if (voiceMode) {
      // STOP VOICE MODE
      stopListening();
      stopSpeaking();
      setVoiceMode(false);
      toast.success("Voice mode disabled");
    } else {
      // START VOICE MODE
      setVoiceMode(true);

      // Speak greeting message
      const greeting = "Hi! I'm ready to help! What would you like to work on?";
      await speak(greeting);

      // Wait for greeting to finish
      setTimeout(() => {
        toast.success("Click mic to start talking", { duration: 3000 });
      }, 2000);
    }
  };

  // ✅ Simplified text message handler - NO manual emotion changes
  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    console.log("💬 Text message sent:", input);

    const userMessage = {
      id: `msg-${Date.now()}`,
      role: "user" as const,
      content: input.trim(),
      timestamp: new Date(),
    };

    addMessage(userMessage);
    setInput("");
    setIsLoading(true);
    // Emotion automatically becomes "thinking" via main useEffect

    // Simulate API delay
    await new Promise((resolve) => setTimeout(resolve, 1500));

    // Get dummy response
    const dummyResponse =
      DUMMY_RESPONSES[responseIndex % DUMMY_RESPONSES.length];
    responseIndex++;

    console.log("🤖 Dummy response:", dummyResponse.text);

    const assistantMessage = {
      id: `msg-${Date.now() + 1}`,
      role: "assistant" as const,
      content: dummyResponse.text,
      timestamp: new Date(),
    };

    addMessage(assistantMessage);
    setIsLoading(false);

    // Speak response - emotion handled by main useEffect
    await speak(dummyResponse.text);
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
              className="absolute top-6 right-6 w-10 h-10 rounded-full bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm flex items-center justify-center hover:bg-white dark:hover:bg-gray-800 transition-colors shadow-lg z-10"
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
                  className="absolute inset-0 rounded-full bg-indigo-400/30 blur-xl"
                  style={{
                    width: "300px",
                    height: "300px",
                    left: "-18px",
                    top: "-18px",
                  }}
                  animate={{
                    scale: [1, 1.2, 1],
                    opacity: [0.4, 0.6, 0.4],
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
                      className="absolute rounded-full border-4 border-green-400/60"
                      style={{
                        width: "300px",
                        height: "300px",
                        left: "-18px",
                        top: "-18px",
                      }}
                      animate={{
                        scale: [1, 1.4, 1.8],
                        opacity: [0.6, 0.3, 0],
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

              {/* Mascot Image */}
              <motion.div
                className="w-64 h-64 relative z-10"
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
                  className="object-contain drop-shadow-2xl"
                  priority
                  style={{
                    filter: "drop-shadow(0 20px 40px rgba(0,0,0,0.15))",
                  }}
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
                    <Mic className="w-6 h-6 animate-pulse" />I m listening...
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
                  toast("Stopped listening", { icon: "🎙️" });
                } else {
                  startListening();
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
