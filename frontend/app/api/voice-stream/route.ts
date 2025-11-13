import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_API_URL;
const DEFAULT_USER_ID = process.env.NEXT_PUBLIC_USER_ID || 'user_123';

export async function POST(request: NextRequest) {
  try {
    const { message } = await request.json();

    if (
      !message ||
      typeof message !== 'string' ||
      message.trim().length === 0
    ) {
      return NextResponse.json(
        { error: 'Message is required and must be a non-empty string.' },
        { status: 400 }
      );
    }

    if (!BACKEND_URL) {
      console.error(
        'VoiceStream error: NEXT_PUBLIC_BACKEND_API_URL is not set'
      );
      return NextResponse.json(
        { error: 'Backend URL not configured.' },
        { status: 500 }
      );
    }

    console.log('💬 Voice chat message:', message);

    // Send to FastAPI backend /chat
    const resp = await fetch(`${BACKEND_URL}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_id: DEFAULT_USER_ID,
        text: message,
      }),
    });

    if (!resp.ok) {
      const errText = await resp.text().catch(() => '');
      console.error('Backend /chat error:', resp.status, errText);
      return NextResponse.json(
        { error: 'Backend chat request failed.' },
        { status: 502 }
      );
    }

    const data = await resp.json();
    const reply = data?.reply ?? data?.response ?? data?.text;

    if (!reply || typeof reply !== 'string') {
      return NextResponse.json(
        { error: 'Invalid response from backend.' },
        { status: 502 }
      );
    }

    // Return in the shape VoiceMode expects
    return NextResponse.json({
      response: reply,
      shouldSpeak: true,
    });
  } catch (error) {
    console.error('❌ Voice chat error:', error);
    return NextResponse.json(
      { error: 'Failed to process voice message.' },
      { status: 500 }
    );
  }
}
