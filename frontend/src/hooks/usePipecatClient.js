import { useState, useEffect, useRef, useCallback } from 'react';
import { RTVIClientTransportFactory } from '@pipecat-ai/client-js';

const usePipecatClient = (serverUrl) => {
  const [connectionState, setConnectionState] = useState('disconnected');
  const [isCallActive, setIsCallActive] = useState(false);
  const [error, setError] = useState(null);
  const [botReady, setBotReady] = useState(false);

  const clientRef = useRef(null);
  const localStreamRef = useRef(null);

  const startCall = useCallback(async () => {
    try {
      setError(null);
      setIsCallActive(true);
      setConnectionState('connecting');

      console.log('Connecting to Pipecat server:', serverUrl);

      // Get user media
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          sampleRate: 16000
        },
        video: false
      });

      localStreamRef.current = stream;

      // Create RTVI client for Pipecat
      const transportFactory = new RTVIClientTransportFactory();
      const client = transportFactory.createTransport({
        baseUrl: serverUrl.replace('ws://', 'http://').replace('/ws', ''),
        enableMic: true,
        enableCam: false,
        mic: {
          sampleRate: 16000,
          echoCancellation: true,
          noiseSuppression: true
        }
      });

      clientRef.current = client;

      // Set up event handlers
      client.on('connected', () => {
        console.log('Connected to Pipecat server');
        setConnectionState('connected');
        setBotReady(true);
      });

      client.on('disconnected', () => {
        console.log('Disconnected from Pipecat server');
        setConnectionState('disconnected');
        setBotReady(false);
        setIsCallActive(false);
      });

      client.on('error', (error) => {
        console.error('Pipecat client error:', error);
        setError(`Connection error: ${error.message || error}`);
        setConnectionState('failed');
      });

      client.on('botReady', () => {
        console.log('Bot is ready');
        setBotReady(true);
      });

      // Connect to the server
      await client.connect();

    } catch (err) {
      console.error('Error starting call:', err);
      setError(`Failed to start call: ${err.message}`);
      setIsCallActive(false);
      setConnectionState('disconnected');
    }
  }, [serverUrl]);

  const endCall = useCallback(async () => {
    try {
      setIsCallActive(false);
      setConnectionState('disconnected');
      setBotReady(false);

      if (localStreamRef.current) {
        localStreamRef.current.getTracks().forEach(track => track.stop());
        localStreamRef.current = null;
      }

      if (clientRef.current) {
        await clientRef.current.disconnect();
        clientRef.current = null;
      }

      console.log('Call ended successfully');
    } catch (err) {
      console.error('Error ending call:', err);
      setError(`Error ending call: ${err.message}`);
    }
  }, []);

  useEffect(() => {
    return () => {
      endCall();
    };
  }, [endCall]);

  return {
    connectionState,
    isCallActive,
    error,
    botReady,
    startCall,
    endCall
  };
};

export default usePipecatClient;