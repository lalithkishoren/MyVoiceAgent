import React, { useState, useEffect, useRef } from 'react';
import { PipecatClient } from '@pipecat-ai/client-js';
import { WebSocketTransport, ProtobufFrameSerializer } from '@pipecat-ai/websocket-transport';

const PipecatVoiceChat = () => {
  const [connectionState, setConnectionState] = useState('disconnected');
  const [isCallActive, setIsCallActive] = useState(false);
  const [error, setError] = useState(null);
  const [selectedVoice, setSelectedVoice] = useState('Charon');

  const pipecatClientRef = useRef(null);

  // Available Gemini Live voices with descriptions
  const availableVoices = [
    { id: 'Puck', name: 'Puck', description: 'Youthful, energetic voice' },
    { id: 'Charon', name: 'Charon', description: 'Deep, authoritative voice' },
    { id: 'Kore', name: 'Kore', description: 'Warm, friendly voice' },
    { id: 'Fenrir', name: 'Fenrir', description: 'Strong, confident voice' }
  ];

  const startCall = async () => {
    try {
      setError(null);
      setIsCallActive(true);
      setConnectionState('connecting');

      // Create Pipecat client using RECOMMENDED SDK pattern with interruption handling
      const pcClient = new PipecatClient({
        transport: new WebSocketTransport({
          serializer: new ProtobufFrameSerializer(),
          recorderSampleRate: 16000,  // Input from microphone
          playerSampleRate: 24000,    // Higher quality output for natural voice
          // High quality audio settings
          enableAGC: true,
          enableNoiseSuppression: true,
          enableEchoCancellation: true,
          // Better audio processing
          audioOutputBitDepth: 16,
          audioOutputChannels: 1,
        }),
        enableCam: false,  // Camera disabled for voice-only
        enableMic: true,   // Microphone enabled
        // Enhanced callback handling for better interruption
        callbacks: {
          onTransportStateChanged: (state) => {
            console.log('Transport state changed:', state);
            setConnectionState(state);

            if (state === 'connected') {
              setError(null);
            } else if (state === 'failed' || state === 'error') {
              setError('Connection failed');
              setIsCallActive(false);
            }
          },
          onBotReady: () => {
            console.log('Bot is ready');
            setConnectionState('connected');
          },
          onConnected: () => {
            console.log('Connected to Pipecat server');
            setConnectionState('connected');
          },
          onDisconnected: () => {
            console.log('Disconnected from Pipecat server');
            setConnectionState('disconnected');
            setIsCallActive(false);
          },
          onError: (error) => {
            console.error('Pipecat client error:', error);
            setError(error.message || 'Connection error');
            setIsCallActive(false);
          },
          onAudioLevel: (level) => {
            // Handle audio level for better visual feedback and interruption detection
            if (level > 0.3) {
              console.log('User speaking detected, level:', level);
            }
          },
          // Enhanced interruption handling
          onUserSpeaking: () => {
            console.log('User started speaking - interruption detected');
          },
          onUserStoppedSpeaking: () => {
            console.log('User stopped speaking');
          }
        },
      });

      pipecatClientRef.current = pcClient;

      // Connect to our Pipecat server with selected voice
      await pcClient.connect({
        wsUrl: `ws://127.0.0.1:8091/ws?voice_id=${selectedVoice}`, // Pass voice selection
      });

      console.log('Connected to Pipecat voice server');

    } catch (err) {
      console.error('Error starting call:', err);
      setError('Failed to start call: ' + err.message);
      setIsCallActive(false);
      setConnectionState('disconnected');
    }
  };

  const endCall = async () => {
    try {
      setIsCallActive(false);
      setConnectionState('disconnected');

      if (pipecatClientRef.current) {
        await pipecatClientRef.current.disconnect();
        pipecatClientRef.current = null;
      }
    } catch (err) {
      console.error('Error ending call:', err);
      setError('Error ending call: ' + err.message);
    }
  };

  useEffect(() => {
    return () => {
      if (pipecatClientRef.current) {
        pipecatClientRef.current.disconnect();
      }
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
          Sutherland Voice Agent
        </h1>

        <p style={{
          color: 'rgba(255, 255, 255, 0.8)',
          marginBottom: '30px',
          fontSize: '1.1em'
        }}>
          
        </p>

        {/* Voice Selection */}
        <div style={{
          margin: '20px 0',
          padding: '15px',
          background: 'rgba(255, 255, 255, 0.2)',
          borderRadius: '10px',
          border: '1px solid rgba(255, 255, 255, 0.3)'
        }}>
          <div style={{
            color: 'white',
            fontWeight: 'bold',
            marginBottom: '10px',
            textAlign: 'center'
          }}>
            🎭 Voice Selection
          </div>
          <select
            value={selectedVoice}
            onChange={(e) => setSelectedVoice(e.target.value)}
            disabled={isCallActive}
            style={{
              width: '100%',
              padding: '10px',
              borderRadius: '8px',
              border: 'none',
              background: 'rgba(255, 255, 255, 0.9)',
              fontSize: '1em',
              cursor: isCallActive ? 'not-allowed' : 'pointer',
              opacity: isCallActive ? 0.6 : 1
            }}
          >
            {availableVoices.map(voice => (
              <option key={voice.id} value={voice.id}>
                {voice.name} - {voice.description}
              </option>
            ))}
          </select>
        </div>

        {/* Connection Status */}
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
          <strong>Instructions:</strong><br/>
          1. Select your preferred voice from the dropdown<br/>
          2. Click "Start Voice Chat" to connect<br/>
          3. Allow microphone access when prompted<br/>
          4. Start speaking - the AI will respond with natural voice<br/>
          5. You can interrupt the AI anytime by speaking<br/>
          6. Uses Gemini Live for real-time speech processing
        </div>
      </div>
    </div>
  );
};

export default PipecatVoiceChat;