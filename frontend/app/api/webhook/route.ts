import { NextRequest, NextResponse } from 'next/server';

// Dummy responses for testing
const DUMMY_RESPONSES = [
  {
    message: "Sure! Let me help you organize your study schedule. I've added some tasks to your calendar.",
    openCalendar: true,
    tasks: [
      {
        id: Date.now().toString(),
        title: "Math Study Session",
        startTime: new Date(new Date().setHours(14, 0, 0, 0)).toISOString(),
        endTime: new Date(new Date().setHours(15, 30, 0, 0)).toISOString(),
        category: "study",
      },
      {
        id: (Date.now() + 1).toString(),
        title: "Take a Break",
        startTime: new Date(new Date().setHours(15, 30, 0, 0)).toISOString(),
        endTime: new Date(new Date().setHours(16, 0, 0, 0)).toISOString(),
        category: "break",
      },
    ],
  },
  {
    message: "That's a great question! Let me break it down for you into smaller, manageable steps.",
    openCalendar: false,
  },
  {
    message: "I'd be happy to help! What specific topic would you like to focus on?",
    openCalendar: false,
  },
];

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { message } = body;

    console.log('📨 Webhook received:', message);

    // Simulate processing delay
    await new Promise((resolve) => setTimeout(resolve, 1000));

    // Check if user is asking about calendar/schedule
    const shouldOpenCalendar =
      message.toLowerCase().includes('calendar') ||
      message.toLowerCase().includes('schedule') ||
      message.toLowerCase().includes('plan');

    // Select appropriate response
    const response = shouldOpenCalendar
      ? DUMMY_RESPONSES[0]
      : DUMMY_RESPONSES[Math.floor(Math.random() * (DUMMY_RESPONSES.length - 1)) + 1];

    console.log('✅ Webhook response:', response);

    return NextResponse.json(response);
  } catch (error) {
    console.error('❌ Webhook error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
