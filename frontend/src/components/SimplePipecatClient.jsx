import React, { useState, useEffect, useRef } from 'react';

const SimplePipecatClient = () => {
  const [connectionState, setConnectionState] = useState('disconnected');
  const [isCallActive, setIsCallActive] = useState(false);
  const [error, setError] = useState(null);

  const websocketRef = useRef(null);
  const audioContextRef = useRef(null);
  const mediaStreamRef = useRef(null);
  const processorRef = useRef(null);

  const startCall = async () => {
    try {
      setError(null);
      setIsCallActive(true);
      setConnectionState('connecting');

      // Get microphone access
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          sampleRate: 16000,
        }
      });

      mediaStreamRef.current = stream;

      // Connect to Pipecat WebSocket server
      const ws = new WebSocket('ws://localhost:8090/ws');
      websocketRef.current = ws;

      ws.onopen = () => {
        console.log('Connected to Pipecat server');
        setConnectionState('connected');
        startAudioProcessing(stream, ws);
      };

      ws.onmessage = (event) => {
        // Handle Pipecat server messages
        if (event.data instanceof ArrayBuffer) {
          // Binary audio data from server
          console.log('Received binary audio data:', event.data.byteLength, 'bytes');
          playAudioData(event.data);
        } else {
          // Text message
          console.log('Received message:', event.data);
        }
      };

      ws.onclose = () => {
        console.log('WebSocket connection closed');
        setConnectionState('disconnected');
        setIsCallActive(false);
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setError('Connection failed');
        setConnectionState('disconnected');
        setIsCallActive(false);
      };

    } catch (err) {
      console.error('Error starting call:', err);
      setError('Failed to start call: ' + err.message);
      setIsCallActive(false);
      setConnectionState('disconnected');
    }
  };

  const startAudioProcessing = (stream, websocket) => {
    try {
      // Create audio context for processing
      audioContextRef.current = new (window.AudioContext || window.webkitAudioContext)({
        sampleRate: 16000
      });

      const source = audioContextRef.current.createMediaStreamSource(stream);

      // Use ScriptProcessor for audio processing (deprecated but works)
      const processor = audioContextRef.current.createScriptProcessor(4096, 1, 1);
      processorRef.current = processor;

      processor.onaudioprocess = (event) => {
        if (websocket.readyState === WebSocket.OPEN) {
          const inputBuffer = event.inputBuffer;
          const inputData = inputBuffer.getChannelData(0);

          // Convert float32 to int16 (16-bit PCM)
          const pcmData = new Int16Array(inputData.length);
          for (let i = 0; i < inputData.length; i++) {
            const sample = Math.max(-1, Math.min(1, inputData[i]));
            pcmData[i] = sample < 0 ? sample * 0x8000 : sample * 0x7FFF;
          }

          // Send raw binary PCM data to Pipecat server
          // This matches the expected format for Pipecat's FastAPIWebsocketTransport
          websocket.send(pcmData.buffer);
        }
      };

      source.connect(processor);
      processor.connect(audioContextRef.current.destination);

      console.log('Audio processing started - sending PCM data to Pipecat server');

    } catch (error) {
      console.error('Error setting up audio processing:', error);
      setError('Failed to setup audio processing');
    }
  };

  const playAudioData = async (audioBuffer) => {
    try {
      if (!audioContextRef.current) {
        audioContextRef.current = new (window.AudioContext || window.webkitAudioContext)();
      }

      // Convert received binary data to audio
      const audioData = await audioContextRef.current.decodeAudioData(audioBuffer.slice());

      const source = audioContextRef.current.createBufferSource();
      source.buffer = audioData;
      source.connect(audioContextRef.current.destination);
      source.start();

      console.log('Playing received audio from Pipecat server');
    } catch (error) {
      console.error('Error playing audio:', error);
      // Fallback: try to play as raw PCM
      try {
        playRawPCM(audioBuffer);
      } catch (pcmError) {
        console.error('Error playing raw PCM:', pcmError);
      }
    }
  };

  const playRawPCM = (arrayBuffer) => {
    try {
      const pcmData = new Int16Array(arrayBuffer);
      const float32Data = new Float32Array(pcmData.length);

      // Convert int16 to float32
      for (let i = 0; i < pcmData.length; i++) {
        float32Data[i] = pcmData[i] / 32768.0;
      }

      const audioBuffer = audioContextRef.current.createBuffer(1, float32Data.length, 16000);
      audioBuffer.getChannelData(0).set(float32Data);

      const source = audioContextRef.current.createBufferSource();
      source.buffer = audioBuffer;
      source.connect(audioContextRef.current.destination);
      source.start();

      console.log('Playing raw PCM audio from Pipecat server');
    } catch (error) {
      console.error('Error playing raw PCM:', error);
    }
  };

  const endCall = async () => {
    try {
      setIsCallActive(false);
      setConnectionState('disconnected');

      // Stop audio processing
      if (processorRef.current) {
        processorRef.current.disconnect();
        processorRef.current = null;
      }

      if (audioContextRef.current) {
        await audioContextRef.current.close();
        audioContextRef.current = null;
      }

      // Stop media stream
      if (mediaStreamRef.current) {
        mediaStreamRef.current.getTracks().forEach(track => track.stop());
        mediaStreamRef.current = null;
      }

      // Close WebSocket
      if (websocketRef.current) {
        websocketRef.current.close();
        websocketRef.current = null;
      }

    } catch (err) {
      console.error('Error ending call:', err);
      setError('Error ending call: ' + err.message);
    }
  };

  useEffect(() => {
    return () => {
      endCall();
    };
  }, []);

  const getConnectionStateColor = () => {
    switch (connectionState) {
      case 'connected': return 'green';
      case 'connecting': return 'yellow';
      case 'disconnected': return 'red';
      default: return 'gray';
    }
  };

  return (
    <div style={{
      maxWidth: '600px',
      margin: '0 auto',
      padding: '20px',
      fontFamily: 'Arial, sans-serif',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      minHeight: '100vh',
      display: 'flex',
      flexDirection: 'column',
      justifyContent: 'center',
      alignItems: 'center'
    }}>
      <div style={{
        background: 'rgba(255, 255, 255, 0.1)',
        backdropFilter: 'blur(10px)',
        borderRadius: '20px',
        padding: '40px',
        boxShadow: '0 8px 32px rgba(31, 38, 135, 0.37)',
        border: '1px solid rgba(255, 255, 255, 0.18)',
        textAlign: 'center',
        width: '100%',
        maxWidth: '500px'
      }}>
        <h1 style={{
          color: 'white',
          marginBottom: '20px',
          fontSize: '2.5em',
          fontWeight: 'bold',
          textShadow: '2px 2px 4px rgba(0,0,0,0.3)'
        }}>
          Sutherland Voice Agent Sutherland Voice Agent
        </h1>

        <p style={{
          color: 'rgba(255, 255, 255, 0.8)',
          marginBottom: '30px',
          fontSize: '1.1em'
        }}>
          Direct connection to Pipecat FastAPIWebsocketTransport
        </p>

        <div style={{
          margin: '20px 0',
          padding: '15px',
          background: 'rgba(255, 255, 255, 0.2)',
          borderRadius: '10px',
          border: '1px solid rgba(255, 255, 255, 0.3)'
        }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            marginBottom: '10px'
          }}>
            <div style={{
              width: '12px',
              height: '12px',
              borderRadius: '50%',
              backgroundColor: getConnectionStateColor(),
              marginRight: '10px',
              boxShadow: `0 0 10px ${getConnectionStateColor()}`
            }}></div>
            <span style={{ color: 'white', fontWeight: 'bold' }}>
              Status: {connectionState}
            </span>
          </div>

          {error && (
            <div style={{
              color: '#ff6b6b',
              background: 'rgba(255, 107, 107, 0.2)',
              padding: '10px',
              borderRadius: '5px',
              margin: '10px 0',
              fontSize: '0.9em'
            }}>
              {error}
            </div>
          )}
        </div>

        <div style={{ marginTop: '30px' }}>
          {!isCallActive ? (
            <button
              onClick={startCall}
              style={{
                background: 'linear-gradient(45deg, #ff6b6b, #ee5a52)',
                color: 'white',
                border: 'none',
                borderRadius: '50px',
                padding: '15px 30px',
                fontSize: '1.2em',
                fontWeight: 'bold',
                cursor: 'pointer',
                boxShadow: '0 4px 15px rgba(255, 107, 107, 0.4)',
                transition: 'all 0.3s ease',
                minWidth: '200px'
              }}
              onMouseOver={(e) => {
                e.target.style.transform = 'translateY(-2px)';
                e.target.style.boxShadow = '0 6px 20px rgba(255, 107, 107, 0.6)';
              }}
              onMouseOut={(e) => {
                e.target.style.transform = 'translateY(0)';
                e.target.style.boxShadow = '0 4px 15px rgba(255, 107, 107, 0.4)';
              }}
            >
              🎤 Start Voice Chat
            </button>
          ) : (
            <button
              onClick={endCall}
              style={{
                background: 'linear-gradient(45deg, #333, #555)',
                color: 'white',
                border: 'none',
                borderRadius: '50px',
                padding: '15px 30px',
                fontSize: '1.2em',
                fontWeight: 'bold',
                cursor: 'pointer',
                boxShadow: '0 4px 15px rgba(0, 0, 0, 0.4)',
                transition: 'all 0.3s ease',
                minWidth: '200px'
              }}
              onMouseOver={(e) => {
                e.target.style.transform = 'translateY(-2px)';
                e.target.style.boxShadow = '0 6px 20px rgba(0, 0, 0, 0.6)';
              }}
              onMouseOut={(e) => {
                e.target.style.transform = 'translateY(0)';
                e.target.style.boxShadow = '0 4px 15px rgba(0, 0, 0, 0.4)';
              }}
            >
              🔇 End Call
            </button>
          )}
        </div>

        <div style={{
          marginTop: '30px',
          padding: '15px',
          background: 'rgba(255, 255, 255, 0.1)',
          borderRadius: '10px',
          fontSize: '0.9em',
          color: 'rgba(255, 255, 255, 0.7)'
        }}>
          <strong>How it works:</strong><br/>
          • Connects directly to Pipecat server (ws://localhost:8090/ws)<br/>
          • Sends 16-bit PCM audio via WebSocket<br/>
          • Receives processed audio from Gemini AI<br/>
          • Uses FastAPIWebsocketTransport protocol
        </div>
      </div>
    </div>
  );
};

export default SimplePipecatClient;