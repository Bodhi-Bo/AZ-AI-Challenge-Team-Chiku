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

    console.log('📝 Text to convert:', text.substring(0, 100) + '...');

    const apiKey = process.env.ELEVENLABS_API_KEY;

    if (!apiKey || apiKey === 'your_api_key_here') {
      console.error('❌ ElevenLabs API key not configured');
      return NextResponse.json(
        { error: 'Text-to-speech service not configured' },
        { status: 500 }
      );
    }

    console.log('✅ API key found, calling ElevenLabs...');

    // ✅ Sarah voice - supports emotions
    const VOICE_ID = 'EXAVITQu4vr4xnSDxMaL';

    // ✅ CRITICAL: Use this exact model for emotion support
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
          model_id: 'eleven_v3', // ✅ THIS MODEL SUPPORTS [giggles]
          voice_settings: {
            stability: 0.5,
            similarity_boost: 0.8,
            style: 0.7, // ✅ Higher = stronger emotions
            use_speaker_boost: true
          }
        }),
      }
    );

    console.log('📡 ElevenLabs response status:', response.status);

    if (!response.ok) {
      const errorText = await response.text();
      console.error('❌ ElevenLabs API error:', errorText);
      throw new Error(`ElevenLabs API failed: ${response.status}`);
    }

    const audioBuffer = await response.arrayBuffer();
    console.log('✅ Audio generated, size:', audioBuffer.byteLength, 'bytes');
    console.log('🎭 Model used: eleven_multilingual_v2 (supports emotions)');

    return new NextResponse(audioBuffer, {
      headers: {
        'Content-Type': 'audio/mpeg',
        'Content-Length': audioBuffer.byteLength.toString(),
      },
    });

  } catch (error) {
    console.error('❌ Text-to-speech error:', error);
    return NextResponse.json(
      { error: 'Failed to generate speech' },
      { status: 500 }
    );
  }
}
