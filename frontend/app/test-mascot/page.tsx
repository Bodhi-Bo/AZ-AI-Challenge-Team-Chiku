"use client";

import { useState } from "react";
import ChikuMascot from "@/components/ChikuMascot";

type EmotionType =
  | "idle"
  | "happy"
  | "thinking"
  | "celebrating"
  | "tired"
  | "encouraging"
  | "sleeping";

export default function TestMascot() {
  const [emotion, setEmotion] = useState<EmotionType>("idle");

  const emotions: EmotionType[] = [
    "idle",
    "happy",
    "thinking",
    "celebrating",
    "tired",
    "encouraging",
    "sleeping",
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-purple-50 p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-4xl font-bold mb-2 text-center bg-clip-text text-transparent bg-gradient-to-r from-indigo-600 to-purple-600">
          Chiku Emotion Test
        </h1>
        <p className="text-gray-600 text-center mb-8">
          Click on any emotion to see Chiku&apos;s personality shine!
        </p>

        <div className="flex justify-center mb-12">
          <ChikuMascot
            emotion={emotion}
            size={200}
            showMessage
            onClick={() => console.log(`Chiku is ${emotion}!`)}
          />
        </div>

        <div className="bg-white rounded-2xl shadow-xl p-8">
          <h2 className="text-xl font-semibold mb-4 text-gray-800">
            Select an Emotion
          </h2>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {emotions.map((emo) => (
              <button
                key={emo}
                onClick={() => setEmotion(emo)}
                className={`px-6 py-4 rounded-xl font-medium transition-all transform ${
                  emotion === emo
                    ? "bg-gradient-to-r from-indigo-600 to-purple-600 text-white scale-105 shadow-lg"
                    : "bg-gray-50 text-gray-700 hover:bg-gray-100 hover:scale-102"
                }`}
              >
                <div className="flex flex-col items-center gap-2">
                  <span className="text-2xl">{getEmotionEmoji(emo)}</span>
                  <span className="capitalize text-sm">{emo}</span>
                </div>
              </button>
            ))}
          </div>
        </div>

        <div className="mt-8 bg-white rounded-2xl shadow-xl p-6">
          <h2 className="text-xl font-semibold mb-4 text-gray-800">
            Current State
          </h2>
          <div className="bg-gray-50 rounded-lg p-4">
            <p className="text-sm text-gray-600 mb-2">
              <span className="font-semibold">Emotion:</span> {emotion}
            </p>
            <p className="text-sm text-gray-600">
              <span className="font-semibold">Message:</span>{" "}
              {getEmotionMessage(emotion)}
            </p>
          </div>
        </div>

        <div className="mt-8 bg-indigo-50 rounded-2xl p-6 border border-indigo-100">
          <h2 className="text-lg font-semibold mb-3 text-indigo-900">
            💡 Usage Tips
          </h2>
          <ul className="space-y-2 text-sm text-indigo-800">
            <li>
              • <strong>Click the mascot</strong> to trigger onClick handler
            </li>
            <li>
              • <strong>Watch animations</strong> - each emotion has unique
              effects
            </li>
            <li>
              • <strong>Celebrating</strong> shows confetti particles
            </li>
            <li>
              • <strong>Thinking</strong> displays animated dots
            </li>
            <li>
              • <strong>Sleeping</strong> shows floating Z&apos;s
            </li>
            <li>
              • <strong>All emotions</strong> have color-coded glows
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
}

function getEmotionEmoji(emotion: EmotionType): string {
  const emojis = {
    idle: "👋",
    happy: "😊",
    thinking: "🤔",
    celebrating: "🎉",
    tired: "😴",
    encouraging: "💪",
    sleeping: "💤",
  };
  return emojis[emotion];
}

function getEmotionMessage(emotion: EmotionType): string {
  const messages = {
    idle: "Hi! I'm Chiku 👋",
    happy: "Great work! 🎉",
    thinking: "Hmm, let me think... 🤔",
    celebrating: "Amazing! You did it! ✨",
    tired: "Time for a break? 😴",
    encouraging: "You've got this! 💪",
    sleeping: "Rest well! 💤",
  };
  return messages[emotion];
}
