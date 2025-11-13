# Voice Flow Debugging Guide

## Check Console Logs in This Order:

### 1. User Speech Captured ✅
```
🎤 [Voice] Starting to listen...
✅ [Voice] User said: "your message here"
```

### 2. Server Query ✅
```
💬 [Voice] Querying server: your message here
📦 [Voice] Server response data: { response: "..." }
💬 [Voice] Extracted reply: "server response text"
📏 [Voice] Response length: 123
```
**⚠️ If empty or missing:** Check backend is running and /api/voice-stream endpoint

### 3. TTS Preparation ✅
```
🎙️ [Voice] About to call speak() with: "server response text"
🔊 [TTS] speak() called with: { text: "...", length: 123, trimmed: 123 }
🔊 [TTS] Starting speech: "server response text..."
🔑 [TTS] Config: { voiceId: '✅ Set', modelId: '✅ Set', apiKey: '✅ Set' }
```
**⚠️ If missing API keys:** Check `.env.local` file

### 4. WebSocket Connection ✅
```
🔗 [TTS] WebSocket URL ready
✅ [WebSocket] Connected to ElevenLabs
```
**⚠️ If connection fails:** Check internet connection and API key validity

### 5. Audio Reception ✅
```
🎵 [TTS] Received audio chunk
✅ [TTS] Audio decoded, queue size: 1
▶️ [TTS] Starting playback
```
**⚠️ If no audio chunks:** ElevenLabs API issue or text too short

### 6. Playback Complete ✅
```
🏁 [TTS] Received isFinal signal
🔌 [WebSocket] Connection closed
✅ [TTS] Playback complete - resolving
✅ [Voice] Finished speaking
```

## Common Issues:

### Issue: No audio plays but logs show chunks received
- Check browser audio permissions
- Check system volume/muting
- Try clicking page first (browsers require user interaction for audio)

### Issue: "Empty text provided, skipping"
- Server returned empty response
- Check backend logs
- Verify `/api/voice-stream` returns correct format: `{ response: "text" }`

### Issue: "Missing API key"
- Create/check `.env.local` in frontend folder
- Ensure `NEXT_PUBLIC_ELEVENLABS_API_KEY` is set
- Restart dev server after adding env vars

### Issue: WebSocket fails to connect
- Verify API key is valid
- Check ElevenLabs account status
- Test API key with curl:
  ```bash
  curl -X GET "https://api.elevenlabs.io/v1/voices" \
    -H "xi-api-key: YOUR_API_KEY"
  ```

## Quick Test Without Voice:

Test TTS directly in browser console:
```javascript
fetch('/api/voice-stream', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ message: 'test message' })
})
.then(r => r.json())
.then(d => console.log('Response:', d))
```

Expected output:
```json
{
  "response": "Your backend's response text",
  "shouldSpeak": true
}
```
