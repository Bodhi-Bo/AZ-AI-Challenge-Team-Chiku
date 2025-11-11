import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    console.log('🎤 Text-to-speech API called');
    const { text } = await request.json();

    if (!text || text.trim().length === 0) {
      console.log('❌ No text provided');
      return NextResponse.json(
        { error: 'Text is required' },
        { status: 400 }
      );
    }

    console.log('📝 Text to convert:', text.substring(0, 50) + '...');

    // Check if ElevenLabs is enabled
    const apiKey = process.env.ELEVENLABS_API_KEY;

    if (!apiKey || apiKey === 'your_api_key_here') {
      console.error('❌ ElevenLabs API key not configured properly');
      console.error('Current key:', apiKey ? 'Set but invalid' : 'Not set');
      return NextResponse.json(
        { error: 'Text-to-speech service not configured. Please add your ElevenLabs API key to .env.local' },
        { status: 500 }
      );
    }

    console.log('✅ API key found, calling ElevenLabs...');

    // Choose voice (Sarah - friendly female voice)
    const VOICE_ID = 'EXAVITQu4vr4xnSDxMaL';

    // Call ElevenLabs API
    const response = await fetch(
      `https://api.elevenlabs.io/v1/text-to-speech/${VOICE_ID}`,
      {
        method: 'POST',
        headers: {
          'Accept': 'audio/mpeg',
          'Content-Type': 'application/json',
          'xi-api-key': apiKey,
        },
        body: JSON.stringify({
          text: text,
          model_id: 'eleven_turbo_v2_5',
          voice_settings: {
            stability: 0.5,
            similarity_boost: 0.75,
            style: 0.5,
            use_speaker_boost: true
          }
        }),
      }
    );

    console.log('📡 ElevenLabs response status:', response.status);

    if (!response.ok) {
      const errorText = await response.text();
      console.error('❌ ElevenLabs API error:', response.status, errorText);
      throw new Error(`ElevenLabs API failed: ${response.status}`);
    }

    // Get audio data
    const audioBuffer = await response.arrayBuffer();
    console.log('✅ Audio generated, size:', audioBuffer.byteLength, 'bytes');

    // Return audio as response
    return new NextResponse(audioBuffer, {
      headers: {
        'Content-Type': 'audio/mpeg',
        'Content-Length': audioBuffer.byteLength.toString(),
      },
    });

  } catch (error) {
    console.error('❌ Text-to-speech error:', error);
    return NextResponse.json(
      { error: 'Failed to generate speech. Check server logs for details.' },
      { status: 500 }
    );
  }
}
