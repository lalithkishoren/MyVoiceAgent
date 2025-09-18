# Gmail Integration Setup Guide

## Overview

This guide will help you set up Gmail API integration for your Pipecat Voice Agent. The integration allows the voice assistant to send emails on behalf of users through voice commands.

## Features

✅ **Voice Email Commands** - Send emails through voice conversation
✅ **OAuth2 Authentication** - Secure Google account integration
✅ **Smart Email Parsing** - Extract recipient, subject, and body from natural speech
✅ **Context Management** - Handle partial email requests across conversation turns
✅ **Notification Emails** - Send automated notifications (call summaries, appointment requests)
✅ **REST API** - HTTP endpoints for programmatic email sending

## Prerequisites

1. **Google Cloud Project** with Gmail API enabled
2. **OAuth2 Credentials** (client_secrets.json file)
3. **Gmail Account** with appropriate permissions
4. **Python Dependencies** (automatically installed)

## Step 1: Google Cloud Setup

### 1.1 Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable the **Gmail API**:
   - Go to "APIs & Services" → "Library"
   - Search for "Gmail API"
   - Click "Enable"

### 1.2 Create OAuth2 Credentials

1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "OAuth client ID"
3. Select "Desktop application"
4. Name it "Voice Agent Gmail Integration"
5. Download the JSON file
6. Rename it to `client_secrets.json`
7. Place it in your server directory: `D:\LalithAI\MyVoiceAgent\server\`

### 1.3 OAuth2 Consent Screen

1. Go to "APIs & Services" → "OAuth consent screen"
2. Choose "External" (for personal use) or "Internal" (for organization)
3. Fill in application information:
   - App name: "Renova Voice Agent"
   - User support email: your email
   - Developer contact: your email
4. Add scopes:
   - `https://www.googleapis.com/auth/gmail.send`
   - `https://www.googleapis.com/auth/gmail.readonly`
5. Add test users (if external)

## Step 2: Environment Configuration

### 2.1 Update .env File

Add the following to your `.env` file:

```bash
# Gmail API Configuration
GOOGLE_CLIENT_SECRETS_FILE=client_secrets.json

# Optional: Gmail-specific settings
GMAIL_USER_EMAIL=your-email@gmail.com
GMAIL_SEND_NOTIFICATIONS=true
```

### 2.2 File Structure

Ensure your server directory looks like this:

```
server/
├── src/
│   ├── gmail_service.py          # Gmail API service
│   ├── voice_email_handler.py    # Voice command processing
│   ├── gmail_routes.py           # FastAPI routes
│   ├── email_enhanced_pipeline.py # Enhanced pipeline
│   ├── googel_auth_manger.py     # Authentication manager
│   └── pipecat_server.py         # Main server (updated)
├── client_secrets.json           # OAuth2 credentials
├── google_token.pickle          # Auto-generated token storage
├── requirements.txt             # Updated dependencies
├── .env                         # Environment variables
└── GMAIL_SETUP.md              # This setup guide
```

## Step 3: Installation & Dependencies

### 3.1 Install Dependencies

```bash
cd server
pip install -r requirements.txt
```

This will install:
- `google-api-python-client` - Gmail API client
- `google-auth-httplib2` - HTTP transport for authentication
- `google-auth-oauthlib` - OAuth2 flow handling

### 3.2 First-Time Authentication

Run the server for the first time:

```bash
python src/pipecat_server.py
```

The authentication flow will:
1. Open a browser window
2. Ask you to sign in to Google
3. Request permission for Gmail access
4. Save credentials to `google_token.pickle`

**Important**: This is a one-time setup. The token file will be reused for future runs.

## Step 4: Testing the Integration

### 4.1 Test Authentication

```bash
curl http://localhost:8090/gmail/health
```

Expected response:
```json
{
  "status": "healthy",
  "authenticated": true,
  "user_email": "your-email@gmail.com",
  "service": "Gmail API v1"
}
```

### 4.2 Test Email Sending

```bash
curl -X POST "http://localhost:8090/gmail/send-simple" \
  -H "Content-Type: application/json" \
  -d '{
    "to": "recipient@example.com",
    "subject": "Test from Voice Agent",
    "body": "Hello from Renova Voice Agent!",
    "is_html": false
  }'
```

### 4.3 Test Voice Email Command

```bash
curl -X POST "http://localhost:8090/gmail/voice-email" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Send an email to doctor@hospital.com with subject appointment request and message I need to reschedule my appointment",
    "session_id": "test-session-123"
  }'
```

## Step 5: Voice Commands

### Supported Voice Patterns

The system recognizes these natural speech patterns:

#### Complete Email Command
"Send an email to doctor@hospital.com about appointment rescheduling saying I need to change my appointment time"

#### Partial Email Commands
- "Send an email to john@example.com" *(system will ask for subject and message)*
- "Email the doctor about my test results" *(system will ask for recipient and message)*
- "Write an email saying thank you for the consultation" *(system will ask for recipient and subject)*

#### Email Components
- **Recipients**: Any text with @ symbol
- **Subject**: "subject is...", "regarding...", "about...", "concerning..."
- **Body**: "message is...", "tell them...", "write...", "saying..."

### Example Voice Interactions

**User**: "Send an email to dr.smith@hospital.com"
**Archana**: "I'd be happy to help you send that email. What would you like the subject to be, and what message would you like to include?"

**User**: "Subject is follow-up appointment and message is I wanted to follow up on our consultation yesterday"
**Archana**: "I'll send an email to dr.smith@hospital.com with the subject 'follow-up appointment' and your message. The email has been sent successfully."

## Step 6: API Endpoints

### Available Endpoints

- `GET /gmail/health` - Check Gmail service status
- `POST /gmail/send` - Send full-featured email
- `POST /gmail/send-simple` - Send simple email
- `POST /gmail/voice-email` - Process voice email command
- `POST /gmail/send-notification` - Send notification email
- `GET /gmail/profile` - Get Gmail user profile
- `DELETE /gmail/email-context/{session_id}` - Clear email context
- `POST /gmail/cleanup-contexts` - Cleanup old contexts

### Request/Response Examples

#### Send Simple Email
```bash
POST /gmail/send-simple
{
  "to": "patient@example.com",
  "subject": "Appointment Confirmation",
  "body": "Your appointment has been confirmed for tomorrow at 2 PM.",
  "is_html": false
}
```

#### Voice Email Processing
```bash
POST /gmail/voice-email
{
  "text": "Send an email to nurse@hospital.com about medication refill",
  "session_id": "session-123"
}
```

#### Notification Email
```bash
POST /gmail/send-notification
{
  "to": "admin@hospital.com",
  "event_type": "call_summary",
  "details": {
    "caller": "+1234567890",
    "duration": "5 minutes",
    "summary": "Patient called to reschedule appointment"
  }
}
```

## Step 7: Security & Production

### Security Best Practices

1. **Protect Credentials**:
   - Keep `client_secrets.json` secure
   - Don't commit it to version control
   - Use proper file permissions (600)

2. **Token Management**:
   - `google_token.pickle` contains access tokens
   - Backup this file for production deployments
   - Monitor token refresh cycles

3. **Email Validation**:
   - The system validates email format
   - Add domain allowlists for production
   - Log all email activities

### Production Deployment

1. **Environment Variables**:
   ```bash
   GOOGLE_CLIENT_SECRETS_FILE=/secure/path/client_secrets.json
   GMAIL_SEND_NOTIFICATIONS=true
   LOG_LEVEL=INFO
   ```

2. **Service Account** (Optional):
   - Consider using service accounts for server-to-server
   - Requires domain-wide delegation setup
   - Better for production environments

3. **Rate Limiting**:
   - Gmail API has quotas (1 billion quota units per day)
   - Monitor usage in Google Cloud Console
   - Implement rate limiting if needed

## Troubleshooting

### Common Issues

#### Authentication Failed
```bash
Error: Failed to initialize Gmail service
```
**Solution**: Re-run authentication flow, check `client_secrets.json` format

#### Token Expired
```bash
Error: The credentials do not contain the necessary fields
```
**Solution**: Delete `google_token.pickle` and re-authenticate

#### Permission Denied
```bash
Error: insufficient permission
```
**Solution**: Check OAuth2 scopes, re-create credentials with proper scopes

#### API Not Enabled
```bash
Error: Gmail API has not been used
```
**Solution**: Enable Gmail API in Google Cloud Console

### Debug Commands

```bash
# Test authentication
curl http://localhost:8090/gmail/health

# Test email extraction
curl -X POST "http://localhost:8090/gmail/test-email-extraction" \
  -H "Content-Type: application/json" \
  -d '{"text": "send email to test@example.com about meeting"}'

# Check server logs
python src/pipecat_server.py --log-level=DEBUG
```

### Log Files

Monitor these log entries:
```
INFO: Gmail service initialized successfully for user@gmail.com
INFO: Email sent successfully. Message ID: 1234567890abcdef
ERROR: Gmail API HTTP error: 403 Forbidden
```

## Integration with Voice Pipeline

### Automatic Email Processing

When integrated with your voice pipeline, the system:

1. **Listens** for email-related commands in conversation
2. **Extracts** email components from natural speech
3. **Manages** context across conversation turns
4. **Sends** emails when complete information is available
5. **Confirms** successful sending to the user

### Hospital-Specific Features

The integration is optimized for hospital use cases:

- **Appointment Confirmations**: Automatic email confirmations
- **Call Summaries**: Email summaries to staff after calls
- **Patient Notifications**: Medication reminders, test results
- **Staff Communication**: Internal notifications and updates

### Voice Agent Enhancements

The email capability enhances Archana's abilities:
- Send appointment confirmations
- Forward patient inquiries to appropriate departments
- Email test results or reports
- Notify staff about urgent requests

## Support & Maintenance

### Regular Maintenance

1. **Token Refresh**: Tokens refresh automatically, but monitor for failures
2. **Quota Monitoring**: Check Gmail API usage in Google Cloud Console
3. **Log Review**: Review email sending logs for errors or abuse
4. **Context Cleanup**: Old email contexts auto-cleanup after 30 minutes

### Updates & Monitoring

- Monitor Gmail API announcements for changes
- Update dependencies regularly for security
- Review email sending patterns for anomalies
- Backup authentication tokens for disaster recovery

---

**Congratulations!** Your Gmail integration is now ready. The voice agent can send emails through natural conversation, making it even more helpful for hospital staff and patients.