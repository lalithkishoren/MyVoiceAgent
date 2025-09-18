import { useState, useEffect, useRef, useCallback } from 'react';

const useWebRTCClient = (signalingServerUrl) => {
  const [connectionState, setConnectionState] = useState('disconnected');
  const [isCallActive, setIsCallActive] = useState(false);
  const [error, setError] = useState(null);
  const [remoteAudioStream, setRemoteAudioStream] = useState(null);

  const websocketRef = useRef(null);
  const peerConnectionRef = useRef(null);
  const localStreamRef = useRef(null);
  const sessionIdRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const reconnectAttemptsRef = useRef(0);
  const maxReconnectAttempts = 5;
  const reconnectDelayMs = 2000;

  const setupPeerConnection = useCallback(() => {
    const peerConnection = new RTCPeerConnection({
      iceServers: [
        { urls: 'stun:stun.l.google.com:19302' },
        { urls: 'stun:stun1.l.google.com:19302' }
      ]
    });

    peerConnection.onicecandidate = (event) => {
      if (event.candidate && websocketRef.current?.readyState === WebSocket.OPEN) {
        websocketRef.current.send(JSON.stringify({
          type: 'ice-candidate',
          candidate: event.candidate,
          sessionId: sessionIdRef.current
        }));
      }
    };

    peerConnection.ontrack = (event) => {
      const [remoteStream] = event.streams;
      setRemoteAudioStream(remoteStream);
    };

    peerConnection.onconnectionstatechange = () => {
      const state = peerConnection.connectionState;
      setConnectionState(state);

      if (state === 'connected') {
        setError(null);
        reconnectAttemptsRef.current = 0;
      } else if (state === 'failed' || state === 'disconnected') {
        if (isCallActive) {
          setError('Connection lost. Attempting to reconnect...');
          handleReconnect();
        }
      }
    };

    return peerConnection;
  }, [isCallActive]);

  const setupWebSocket = useCallback(() => {
    if (!signalingServerUrl) return null;

    const ws = new WebSocket(signalingServerUrl);

    ws.onopen = () => {
      setConnectionState('connected');
      setError(null);
      reconnectAttemptsRef.current = 0;
    };

    ws.onmessage = async (event) => {
      try {
        const data = JSON.parse(event.data);

        switch (data.type) {
          case 'session-created':
            sessionIdRef.current = data.sessionId;
            // Start audio streaming through this signaling WebSocket instead
            console.log('Session created, starting audio streaming');
            startAudioStreaming(ws);
            break;

          case 'offer':
            if (peerConnectionRef.current) {
              await peerConnectionRef.current.setRemoteDescription(new RTCSessionDescription(data.offer));
              const answer = await peerConnectionRef.current.createAnswer();
              await peerConnectionRef.current.setLocalDescription(answer);

              ws.send(JSON.stringify({
                type: 'answer',
                answer: answer,
                sessionId: sessionIdRef.current
              }));
            }
            break;

          case 'answer':
            if (peerConnectionRef.current) {
              await peerConnectionRef.current.setRemoteDescription(new RTCSessionDescription(data.answer));
            }
            break;

          case 'ice-candidate':
            if (peerConnectionRef.current) {
              await peerConnectionRef.current.addIceCandidate(new RTCIceCandidate(data.candidate));
            }
            break;

          case 'session-ended':
            await endCall();
            break;

          case 'audio-response':
            // Handle audio response from server
            if (data.audio) {
              console.log('Received audio response from server');
              playAudioFromArray(data.audio, data.sampleRate || 16000);
            }
            break;

          case 'error':
            setError(data.message || 'Server error occurred');
            break;

          default:
            console.warn('Unknown message type:', data.type);
        }
      } catch (err) {
        console.error('Error processing WebSocket message:', err);
        setError('Failed to process server message');
      }
    };

    ws.onclose = () => {
      setConnectionState('disconnected');
      if (isCallActive && reconnectAttemptsRef.current < maxReconnectAttempts) {
        setError('Connection lost. Attempting to reconnect...');
        handleReconnect();
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      setError('Failed to connect to signaling server');
    };

    return ws;
  }, [signalingServerUrl, isCallActive]);

  const handleReconnect = useCallback(() => {
    if (reconnectAttemptsRef.current >= maxReconnectAttempts) {
      setError('Failed to reconnect after multiple attempts');
      setIsCallActive(false);
      return;
    }

    reconnectAttemptsRef.current++;

    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }

    reconnectTimeoutRef.current = setTimeout(() => {
      if (isCallActive) {
        websocketRef.current = setupWebSocket();
      }
    }, reconnectDelayMs * reconnectAttemptsRef.current);
  }, [isCallActive, setupWebSocket]);

  const startAudioStreaming = useCallback((websocket) => {
    try {
      console.log('Starting audio streaming through signaling WebSocket');
      setConnectionState('connected');

      let audioContext = null;
      let processor = null;
      let source = null;

      const setupAudio = async () => {
        try {
          if (localStreamRef.current) {
            audioContext = new (window.AudioContext || window.webkitAudioContext)({
              sampleRate: 16000
            });

            source = audioContext.createMediaStreamSource(localStreamRef.current);
            processor = audioContext.createScriptProcessor(4096, 1, 1);

            processor.onaudioprocess = (event) => {
              if (websocket.readyState === WebSocket.OPEN) {
                const inputBuffer = event.inputBuffer;
                const inputData = inputBuffer.getChannelData(0);

                // Convert to base64 for JSON transmission
                const pcmData = new Int16Array(inputData.length);
                for (let i = 0; i < inputData.length; i++) {
                  const sample = Math.max(-1, Math.min(1, inputData[i]));
                  pcmData[i] = sample < 0 ? sample * 0x8000 : sample * 0x7FFF;
                }

                const audioMessage = {
                  type: 'audio-data',
                  sessionId: sessionIdRef.current,
                  audio: Array.from(pcmData),
                  sampleRate: 16000
                };

                websocket.send(JSON.stringify(audioMessage));
              }
            };

            source.connect(processor);
            processor.connect(audioContext.destination);

            const audioTrack = localStreamRef.current.getAudioTracks()[0];
            if (audioTrack) {
              audioTrack.enabled = true;
              console.log('Audio streaming started');
            }
          }
        } catch (error) {
          console.error('Error setting up audio processing:', error);
          setError('Failed to setup audio processing');
        }
      };

      setupAudio();

    } catch (error) {
      console.error('Error starting audio streaming:', error);
      setError('Failed to start audio streaming');
    }
  }, []);

  const playAudioBuffer = useCallback(async (audioData) => {
    try {
      // Create audio context for playback
      const audioContext = new (window.AudioContext || window.webkitAudioContext)();

      // Convert received audio data to AudioBuffer
      const audioBuffer = await audioContext.decodeAudioData(audioData);

      // Create source and play
      const source = audioContext.createBufferSource();
      source.buffer = audioBuffer;
      source.connect(audioContext.destination);
      source.start();

      console.log('Playing audio response from Pipecat');
    } catch (error) {
      console.error('Error playing audio buffer:', error);
    }
  }, []);

  const playAudioFromArray = useCallback(async (audioArray, sampleRate = 16000) => {
    try {
      const audioContext = new (window.AudioContext || window.webkitAudioContext)();

      // Convert array to Float32Array
      const float32Array = new Float32Array(audioArray.length);
      for (let i = 0; i < audioArray.length; i++) {
        float32Array[i] = audioArray[i] / 32768.0; // Convert from int16 to float32
      }

      // Create AudioBuffer
      const audioBuffer = audioContext.createBuffer(1, float32Array.length, sampleRate);
      audioBuffer.getChannelData(0).set(float32Array);

      // Play the audio
      const source = audioContext.createBufferSource();
      source.buffer = audioBuffer;
      source.connect(audioContext.destination);
      source.start();

      console.log('Playing audio response from server');
    } catch (error) {
      console.error('Error playing audio from array:', error);
    }
  }, []);

  const startCall = useCallback(async () => {
    try {
      setError(null);
      setIsCallActive(true);
      setConnectionState('connecting');

      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true
        }
      });

      stream.getAudioTracks().forEach(track => {
        track.enabled = false;
      });

      localStreamRef.current = stream;

      peerConnectionRef.current = setupPeerConnection();

      stream.getTracks().forEach(track => {
        peerConnectionRef.current.addTrack(track, stream);
      });

      websocketRef.current = setupWebSocket();

      const offer = await peerConnectionRef.current.createOffer({
        offerToReceiveAudio: true
      });

      await peerConnectionRef.current.setLocalDescription(offer);

      const checkConnection = () => {
        if (websocketRef.current?.readyState === WebSocket.OPEN) {
          websocketRef.current.send(JSON.stringify({
            type: 'start-session',
            offer: offer
          }));
        } else {
          setTimeout(checkConnection, 100);
        }
      };

      checkConnection();

    } catch (err) {
      console.error('Error starting call:', err);
      setError('Failed to start call: ' + err.message);
      setIsCallActive(false);
      setConnectionState('disconnected');
    }
  }, [setupPeerConnection, setupWebSocket]);

  const endCall = useCallback(async () => {
    try {
      setIsCallActive(false);
      setConnectionState('disconnected');
      setRemoteAudioStream(null);
      sessionIdRef.current = null;

      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
        reconnectTimeoutRef.current = null;
      }

      if (localStreamRef.current) {
        localStreamRef.current.getTracks().forEach(track => track.stop());
        localStreamRef.current = null;
      }

      if (peerConnectionRef.current) {
        peerConnectionRef.current.close();
        peerConnectionRef.current = null;
      }

      if (websocketRef.current && websocketRef.current.readyState === WebSocket.OPEN) {
        websocketRef.current.send(JSON.stringify({
          type: 'end-session',
          sessionId: sessionIdRef.current
        }));
        websocketRef.current.close();
      }

      websocketRef.current = null;
    } catch (err) {
      console.error('Error ending call:', err);
      setError('Error ending call: ' + err.message);
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
    remoteAudioStream,
    startCall,
    endCall
  };
};

export default useWebRTCClient;