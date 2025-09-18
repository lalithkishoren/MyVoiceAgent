// Add these endpoints to your Firebase app

// 1. Add to your main app file (e.g., app.js or index.js)

// Proxy endpoint for Twilio Voice Webhook
app.post('/twilio/voice', async (req, res) => {
  try {
    // Your local server IP (replace with your actual local IP)
    const LOCAL_SERVER = 'http://YOUR_LOCAL_IP:8091';

    const response = await fetch(`${LOCAL_SERVER}/twilio/voice`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: new URLSearchParams(req.body).toString()
    });

    const twimlResponse = await response.text();
    res.set('Content-Type', 'application/xml');
    res.send(twimlResponse);
  } catch (error) {
    console.error('Twilio voice proxy error:', error);
    res.status(500).send('Internal Server Error');
  }
});

// Proxy endpoint for Twilio Status Webhook
app.post('/twilio/status', async (req, res) => {
  try {
    const LOCAL_SERVER = 'http://YOUR_LOCAL_IP:8091';

    const response = await fetch(`${LOCAL_SERVER}/twilio/status`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: new URLSearchParams(req.body).toString()
    });

    const result = await response.json();
    res.json(result);
  } catch (error) {
    console.error('Twilio status proxy error:', error);
    res.status(500).json({status: 'error', message: error.message});
  }
});

// Health check endpoint
app.get('/twilio/health', (req, res) => {
  res.json({
    status: 'healthy',
    message: 'Twilio proxy endpoints active',
    timestamp: new Date().toISOString()
  });
});