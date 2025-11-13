import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const { message } = await request.json();

    if (!message || message.trim().length === 0) {
      return NextResponse.json(
        { error: 'Message is required' },
        { status: 400 }
      );
    }

    console.log('💬 Voice chat message:', message);

    // TODO: Send to your AI backend (same as text chat)
    // For now, echo back with a friendly response
    const response = `I heard you say: "${message}". How can I help you with that?`;

    return NextResponse.json({
      response,
      shouldSpeak: true // Signal to play this response
    });

  } catch (error) {
    console.error('❌ Voice chat error:', error);
    return NextResponse.json(
      { error: 'Failed to process voice message' },
      { status: 500 }
    );
  }
}
