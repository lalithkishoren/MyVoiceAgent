# 🚀 Quick Phone Setup Guide

## Ready to Go Live! 📞

Your Twilio phone integration is **99% complete**. Here's how to make it live in 5 minutes:

### Step 1: Install ngrok (2 minutes)
1. Go to https://ngrok.com/download
2. Download the Windows version
3. Extract `ngrok.exe` to your project folder or add to PATH

### Step 2: Start ngrok tunnel (30 seconds)
```bash
# Open a new terminal and run:
ngrok http 8091
```

You'll see output like:
```
Session Status: online
Forwarding: https://abc123-def456.ngrok.io -> http://localhost:8091
```

### Step 3: Update your configuration (1 minute)
1. Copy the `https://...ngrok.io` URL from ngrok
2. Update your `.env` file:
```bash
NGROK_URL=https://abc123-def456.ngrok.io
```

### Step 4: Restart your servers (1 minute)
```bash
# Stop current servers (Ctrl+C) then restart:
cd "D:\LalithAI\MyVoiceAgent\server"
"venv\Scripts\python.exe" "src\pipecat_server.py"  # Terminal 1
"venv\Scripts\python.exe" "src\twilio_server.py"   # Terminal 2
```

### Step 5: Configure Twilio (1 minute)
1. Go to [Twilio Console](https://console.twilio.com/)
2. Navigate to: **Phone Numbers** → **Manage** → **Active Numbers**
3. Click your number: **+1xxxxxxxxxx**
4. Set **Webhook URL** to: `https://your-ngrok-url.ngrok.io/twilio/voice`
5. Set **HTTP Method** to: **POST**
6. **Save Configuration**

### Step 6: Test Your Phone! 📱
Call **+1xxxxxxxxxx** and you should hear:
> "Hello! Connecting you to our AI assistant."

Then you'll be connected to **Archana**, your Renova Hospital voice assistant!

---

## 🎯 What Happens During a Call:

```
Your Phone → Twilio → ngrok → localhost:8091 → Audio Bridge → localhost:8090 → Gemini Live → Archana
```

## 🔧 Troubleshooting:

**Call doesn't connect:**
- Check ngrok is running: `ngrok http 8091`
- Verify webhook URL in Twilio console
- Check both servers are running (ports 8090 & 8091)

**No audio:**
- Verify ngrok URL in `.env` file
- Check WebSocket URL in server logs
- Ensure both Pipecat and Twilio servers are running

**Server errors:**
- Check all environment variables are set
- Verify Gemini API key is valid
- Ensure ports 8090 and 8091 are available

## 🎉 Success Indicators:

✅ **ngrok shows**: `Forwarding https://...ngrok.io -> http://localhost:8091`
✅ **Twilio webhook configured**: `https://your-ngrok-url.ngrok.io/twilio/voice`
✅ **Both servers running**: Ports 8090 (Pipecat) and 8091 (Twilio)
✅ **Call connects**: You hear the greeting message
✅ **AI responds**: Archana speaks with Gemini Live voice

---

**You're about to have a voice conversation with AI through your phone! 🤖📞**