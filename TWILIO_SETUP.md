# Twilio Voice Integration Setup Guide

## ✅ Completed Steps

1. **Basic Twilio Server**: Created `twilio_server.py` running on port 8091
2. **Webhook Handler**: `/twilio/voice` endpoint for incoming calls
3. **Media Stream Handler**: `/twilio/stream` WebSocket for real-time audio
4. **TwiML Response**: Response with greeting and Media Stream configuration
5. **Environment Configuration**: Twilio credentials added to `.env`
6. **Audio Format Bridge**: Created `audio_bridge.py` for mulaw ↔ PCM conversion
7. **Pipecat Integration**: Connected Twilio audio to Pipecat voice pipeline
8. **WebSocket Testing**: All endpoints tested and working locally

## 🎯 Current Status

**Servers Running:**
- **Port 8090**: Sutherland Voice Agent (Gemini Live with hospital assistant)
- **Port 8091**: Twilio integration server with audio bridge

**Twilio Configuration:**
- **Account SID**: ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
- **Phone Number**: +1xxxxxxxxxx
- **Webhook URL**: `http://localhost:8091/twilio/voice` (needs public URL)
- **Stream URL**: `wss://localhost:8091/twilio/stream` (needs public URL)

**Integration Status:**
- ✅ Audio bridge (mulaw ↔ PCM, 8kHz ↔ 16kHz/24kHz)
- ✅ Pipecat connector for bidirectional audio
- ✅ TwiML with Media Stream configuration
- ✅ All local testing completed

## 🚀 Next Steps

### Step 1: Set Up ngrok (Required for Testing)

Since Twilio needs to reach your localhost server, you need to expose it publicly:

```bash
# Download and install ngrok from https://ngrok.com/
# Then run:
ngrok http 8091
```

This will give you a public URL like: `https://abc123.ngrok.io`

### Step 2: Configure Twilio Phone Number

1. Go to **Twilio Console** → **Phone Numbers** → **Manage** → **Active Numbers**
2. Click on your phone number: `+1xxxxxxxxxx`
3. Set **Webhook URL** to: `https://your-ngrok-url.ngrok.io/twilio/voice`
4. Set **HTTP Method** to: `POST`
5. Save configuration

### Step 3: Update Stream URL

Update `twilio_server.py` to use your ngrok URL:

```python
# Replace this line in twilio_server.py:
stream_url = f"wss://your-ngrok-url.ngrok.io/twilio/stream"
```

### Step 4: Test Basic Call Flow

1. **Call your Twilio number**: `+1xxxxxxxxxx`
2. **Expected behavior**:
   - You should hear: "Hello! Welcome to our AI Voice Assistant..."
   - Call should connect and play test message
   - Server logs should show incoming call

### Step 5: Implement Audio Bridge (Next Phase)

Once basic calls work, we'll implement:

1. **Audio Format Conversion**: mulaw (8kHz) ↔ PCM (16kHz/24kHz)
2. **Pipecat Integration**: Connect phone audio to Gemini Live
3. **Real-time Processing**: Bidirectional audio streaming

## 🔧 Current Server Endpoints

### Twilio Server (Port 8091)
- `GET /` - Server information
- `GET /health` - Health check
- `POST /twilio/voice` - Incoming call webhook
- `POST /twilio/status` - Call status updates
- `WS /twilio/stream` - Media stream WebSocket
- `GET /twilio/calls` - Active calls information

### Pipecat Server (Port 8090)
- `WS /ws` - Voice chat with Gemini Live
- `GET /` - Server status
- `GET /health` - Health check

## 📋 Testing Checklist

- [ ] ngrok tunnel running on port 8091
- [ ] Twilio phone number webhook configured
- [ ] Test call to +1xxxxxxxxxx
- [ ] Incoming call appears in server logs
- [ ] TwiML response plays greeting message
- [ ] WebSocket connection established for media stream

## 🐛 Troubleshooting

**Call doesn't connect:**
- Check ngrok is running and accessible
- Verify webhook URL in Twilio console
- Check server logs for errors

**No audio or media stream issues:**
- Verify WebSocket URL is correct
- Check ngrok supports WebSocket tunneling
- Review media stream logs

**Server errors:**
- Check all environment variables are set
- Verify Twilio credentials are correct
- Ensure ports 8090 and 8091 are available

## 📚 Architecture Overview

```
Phone Call → Twilio → ngrok → localhost:8091 → twilio_server.py
                                    ↓
                            WebSocket Stream
                                    ↓
                            (Future: Audio Bridge)
                                    ↓
                            localhost:8090 → pipecat_server.py → Gemini Live
```

## 🎯 Next Development Phases

1. **Phase 1**: Basic call routing (✅ COMPLETED)
2. **Phase 2**: ngrok setup and testing (🔄 IN PROGRESS)
3. **Phase 3**: Audio format bridge implementation
4. **Phase 4**: Pipecat integration with phone calls
5. **Phase 5**: End-to-end voice conversation testing

---

*Follow this guide step by step to set up phone integration with your Sutherland Voice Agent.*