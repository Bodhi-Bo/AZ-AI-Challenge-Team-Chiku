import { NextRequest, NextResponse } from "next/server";
import type { Message } from "@/types";

// Simple rate limiting (in-memory, for MVP)
const requestCounts = new Map<string, { count: number; resetTime: number }>();
const RATE_LIMIT = 60; // 60 requests per minute
const RATE_LIMIT_WINDOW = 60000; // 1 minute

function checkRateLimit(ip: string): boolean {
  const now = Date.now();
  const record = requestCounts.get(ip);

  if (!record || now > record.resetTime) {
    requestCounts.set(ip, { count: 1, resetTime: now + RATE_LIMIT_WINDOW });
    return true;
  }

  if (record.count >= RATE_LIMIT) {
    return false;
  }

  record.count++;
  return true;
}

// Simple intent detection
function detectIntent(message: string): string {
  const lowerMessage = message.toLowerCase();

  // Task creation
  if (
    lowerMessage.includes("add task") ||
    lowerMessage.includes("remind me") ||
    lowerMessage.includes("schedule") ||
    lowerMessage.includes("create event") ||
    lowerMessage.includes("set reminder")
  ) {
    return "task_creation";
  }

  // Calendar query
  if (
    lowerMessage.includes("what's next") ||
    lowerMessage.includes("what is next") ||
    lowerMessage.includes("free time") ||
    lowerMessage.includes("when is") ||
    lowerMessage.includes("when do i have")
  ) {
    return "calendar_query";
  }

  // Encouragement
  if (
    lowerMessage.includes("help") ||
    lowerMessage.includes("overwhelmed") ||
    lowerMessage.includes("stuck") ||
    lowerMessage.includes("can't focus") ||
    lowerMessage.includes("distracted")
  ) {
    return "encouragement";
  }

  return "general";
}

// Simple response generation (MVP - replace with OpenAI API later)
function generateResponse(message: string, intent: string): string {
  const lowerMessage = message.toLowerCase();

  switch (intent) {
    case "task_creation":
      return "I'd be happy to help you create a task! What would you like to schedule, and when? I can add it to your calendar.";

    case "calendar_query":
      return "Let me check your calendar for you. You can view your upcoming events in the calendar on the right. Is there something specific you're looking for?";

    case "encouragement":
      return "You've got this! 🦉 Take a deep breath. Break your task into smaller steps. I'm here to help you stay organized and focused. What would you like to tackle first?";

    default:
      // General responses
      if (lowerMessage.includes("hello") || lowerMessage.includes("hi")) {
        return "Hello! I'm Chiku, your ADHD-friendly assistant. How can I help you today?";
      }
      if (lowerMessage.includes("thank")) {
        return "You're welcome! I'm here whenever you need me. 😊";
      }
      if (lowerMessage.includes("how are you")) {
        return "I'm doing great! Ready to help you stay organized and focused. What can I do for you?";
      }
      return "I understand. Let me help you with that! Could you tell me a bit more about what you need?";
  }
}

export async function POST(request: NextRequest) {
  try {
    // Rate limiting
    const ip = request.headers.get("x-forwarded-for") || "unknown";
    if (!checkRateLimit(ip)) {
      return NextResponse.json(
        { error: "Too many requests. Please try again later." },
        { status: 429 }
      );
    }

    const body = await request.json();
    const { message, conversationHistory } = body;

    // Validate input
    if (!message || typeof message !== "string" || message.trim().length === 0) {
      return NextResponse.json(
        { error: "Message is required and must be a non-empty string." },
        { status: 400 }
      );
    }

    // Detect intent
    const intent = detectIntent(message);

    // Generate response
    const reply = generateResponse(message, intent);

    // Return response
    return NextResponse.json({
      reply,
      timestamp: new Date().toISOString(),
      intent,
    });
  } catch (error) {
    console.error("Chat API error:", error);
    return NextResponse.json(
      { error: "An error occurred while processing your request." },
      { status: 500 }
    );
  }
}

