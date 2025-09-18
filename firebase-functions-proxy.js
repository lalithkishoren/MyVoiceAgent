// Firebase Functions for Twilio Proxy
// Deploy this to your Firebase project

const functions = require('firebase-functions');
const cors = require('cors')({origin: true});

// Proxy for Twilio Voice Webhook
exports.twilioVoice = functions.https.onRequest(async (req, res) => {
  cors(req, res, async () => {
    if (req.method !== 'POST') {
      return res.status(405).send('Method Not Allowed');
    }

    try {
      // Your local server URL - you'll need to expose this via ngrok or similar
      const localServerUrl = 'http://YOUR_LOCAL_IP:8091';

      const response = await fetch(`${localServerUrl}/twilio/voice`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams(req.body).toString()
      });

      const twimlResponse = await response.text();

      res.set('Content-Type', 'application/xml');
      res.status(200).send(twimlResponse);
    } catch (error) {
      console.error('Proxy error:', error);
      res.status(500).send('Internal Server Error');
    }
  });
});

// Proxy for Twilio Status Webhook
exports.twilioStatus = functions.https.onRequest(async (req, res) => {
  cors(req, res, async () => {
    if (req.method !== 'POST') {
      return res.status(405).send('Method Not Allowed');
    }

    try {
      const localServerUrl = 'http://YOUR_LOCAL_IP:8091';

      const response = await fetch(`${localServerUrl}/twilio/status`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams(req.body).toString()
      });

      const result = await response.json();
      res.status(200).json(result);
    } catch (error) {
      console.error('Status proxy error:', error);
      res.status(500).json({status: 'error', message: error.message});
    }
  });
});

// Note: WebSocket proxying is more complex in Firebase Functions
// You might need to use a different approach for the /twilio/stream endpoint