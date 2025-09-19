import { useState, useEffect, useRef, useCallback } from 'react';

const useSimplePipecatClient = (serverUrl) => {
  const [connectionState, setConnectionState] = useState('disconnected');
  const [isCallActive, setIsCallActive] = useState(false);
  const [error, setError] = useState(null);

  const websocketRef = useRef(null);
  const localStreamRef = useRef(null);
  const audioContextRef = useRef(null);

  const startCall = useCallback(async () => {
    try {
      setError(null);
      setIsCallActive(true);
      setConnectionState('connecting');

      console.log('Connecting to Pipecat server:', serverUrl);

      // Create WebSocket connection
      const ws = new WebSocket(serverUrl);
      websocketRef.current = ws;

      ws.onopen = async () => {
        console.log('WebSocket connected to Pipecat server');
        setConnectionState('connected');
        // Start audio capture immediately
        await startAudioCapture();
      };

      ws.onmessage = async (event) => {
        try {
          // Handle binary audio data (Pipecat sends binary audio frames)
          if (event.data instanceof ArrayBuffer) {
            console.log('Received binary audio data:', event.data.byteLength, 'bytes');
            await playBinaryAudio(event.data);
            return;
          }

          // Handle Blob data (some WebSocket implementations)
          if (event.data instanceof Blob) {
            console.log('Received blob audio data:', event.data.size, 'bytes');
            const arrayBuffer = await event.data.arrayBuffer();
            await playBinaryAudio(arrayBuffer);
            return;
          }

          // Handle text messages
          const data = JSON.parse(event.data);
          console.log('Received message:', data.type);

          switch (data.type) {
            case 'session-created':
              console.log('Session created');
              await startAudioCapture();
              break;
            case 'error':
              console.error('Server error:', data.message);
              setError(data.message);
              break;
            default:
              console.log('Unknown message type:', data.type);
          }
        } catch (err) {
          console.error('Error processing message:', err);
        }
      };

      ws.onclose = () => {
        console.log('WebSocket disconnected');
        setConnectionState('disconnected');
        setIsCallActive(false);
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setError('Failed to connect to server');
        setConnectionState('failed');
      };

    } catch (err) {
      console.error('Error starting call:', err);
      setError(`Failed to start call: ${err.message}`);
      setIsCallActive(false);
      setConnectionState('disconnected');
    }
  }, [serverUrl]);

  const startAudioCapture = useCallback(async () => {
    try {
      console.log('Starting audio capture...');

      // Get user media
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          sampleRate: 16000
        }
      });

      localStreamRef.current = stream;

      // Set up audio processing
      const audioContext = new (window.AudioContext || window.webkitAudioContext)({
        sampleRate: 16000
      });
      audioContextRef.current = audioContext;

      const source = audioContext.createMediaStreamSource(stream);
      const processor = audioContext.createScriptProcessor(4096, 1, 1);

      processor.onaudioprocess = (event) => {
        if (websocketRef.current?.readyState === WebSocket.OPEN) {
          const inputBuffer = event.inputBuffer;
          const inputData = inputBuffer.getChannelData(0);

          // Convert to 16-bit PCM
          const pcmData = new Int16Array(inputData.length);
          for (let i = 0; i < inputData.length; i++) {
            const sample = Math.max(-1, Math.min(1, inputData[i]));
            pcmData[i] = sample < 0 ? sample * 0x8000 : sample * 0x7FFF;
          }

          // Send binary audio data
          websocketRef.current.send(pcmData.buffer);
        }
      };

      source.connect(processor);
      processor.connect(audioContext.destination);

      console.log('Audio capture started');

    } catch (err) {
      console.error('Error setting up audio:', err);
      setError('Failed to access microphone');
    }
  }, []);

  const playBinaryAudio = useCallback(async (audioData) => {
    try {
      if (!audioContextRef.current) {
        audioContextRef.current = new (window.AudioContext || window.webkitAudioContext)({
          sampleRate: 24000 // Match server output rate
        });
      }

      const audioContext = audioContextRef.current;

      // Try to decode as standard audio format first
      try {
        const audioBuffer = await audioContext.decodeAudioData(audioData.slice());
        const source = audioContext.createBufferSource();
        source.buffer = audioBuffer;
        source.connect(audioContext.destination);
        source.start();
        console.log('Playing decoded audio response');
        return;
      } catch (decodeError) {
        console.log('Standard decode failed, trying raw PCM:', decodeError.message);
      }

      // If standard decode fails, try as raw PCM data
      const pcmData = new Int16Array(audioData);
      console.log('Raw PCM data length:', pcmData.length);

      if (pcmData.length > 0) {
        // Convert Int16 PCM to Float32 for AudioBuffer
        const float32Data = new Float32Array(pcmData.length);
        for (let i = 0; i < pcmData.length; i++) {
          float32Data[i] = pcmData[i] / 32768.0; // Convert from int16 to float32
        }

        // Create AudioBuffer manually
        const audioBuffer = audioContext.createBuffer(1, float32Data.length, 24000);
        audioBuffer.getChannelData(0).set(float32Data);

        // Play the audio
        const source = audioContext.createBufferSource();
        source.buffer = audioBuffer;
        source.connect(audioContext.destination);
        source.start();

        console.log('Playing raw PCM audio response');
      }
    } catch (err) {
      console.error('Error playing binary audio:', err);
    }
  }, []);

  const endCall = useCallback(async () => {
    try {
      setIsCallActive(false);
      setConnectionState('disconnected');

      if (localStreamRef.current) {
        localStreamRef.current.getTracks().forEach(track => track.stop());
        localStreamRef.current = null;
      }

      if (audioContextRef.current) {
        await audioContextRef.current.close();
        audioContextRef.current = null;
      }

      if (websocketRef.current) {
        websocketRef.current.close();
        websocketRef.current = null;
      }

      console.log('Call ended');
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
    startCall,
    endCall
  };
};

export default useSimplePipecatClient;