import React, { useEffect, useRef } from 'react';
import useWebRTCClient from '../hooks/useWebRTCClient';

const VoiceChat = () => {
  const signalingServerUrl = 'ws://127.0.0.1:8091/ws'; // Hardcoded for now
  const audioRef = useRef(null);

  const {
    connectionState,
    isCallActive,
    error,
    remoteAudioStream,
    startCall,
    endCall
  } = useWebRTCClient(signalingServerUrl);

  useEffect(() => {
    if (audioRef.current && remoteAudioStream) {
      audioRef.current.srcObject = remoteAudioStream;
      audioRef.current.play().catch(err => {
        console.error('Error playing remote audio:', err);
      });
    }
  }, [remoteAudioStream]);

  const getConnectionStateDisplay = () => {
    switch (connectionState) {
      case 'connecting':
        return { text: 'Connecting...', className: 'status-connecting' };
      case 'connected':
        return { text: 'Connected', className: 'status-connected' };
      case 'failed':
        return { text: 'Connection Failed', className: 'status-error' };
      case 'disconnected':
        return { text: 'Disconnected', className: 'status-disconnected' };
      default:
        return { text: 'Unknown', className: 'status-disconnected' };
    }
  };

  const getCallButtonText = () => {
    if (connectionState === 'connecting') return 'Connecting...';
    if (isCallActive) return 'End Call';
    return 'Start Call';
  };

  const handleCallToggle = () => {
    if (isCallActive) {
      endCall();
    } else {
      startCall();
    }
  };

  const statusDisplay = getConnectionStateDisplay();

  return (
    <div className="voice-chat-container">
      <div className="voice-chat-card">
        <div className="header">
          <h1>Sutherland Voice Agent</h1>
          <div className={`status-indicator ${statusDisplay.className}`}>
            <span className="status-dot"></span>
            <span className="status-text">{statusDisplay.text}</span>
          </div>
        </div>

        <div className="content">
          <div className="audio-controls">
            <button
              className={`call-button ${isCallActive ? 'end-call' : 'start-call'}`}
              onClick={handleCallToggle}
              disabled={connectionState === 'connecting'}
            >
              <span className="button-icon">
                {isCallActive ? '📞' : '🎤'}
              </span>
              <span className="button-text">{getCallButtonText()}</span>
            </button>
          </div>

          {error && (
            <div className="error-message">
              <span className="error-icon">⚠️</span>
              <span className="error-text">{error}</span>
            </div>
          )}

          <div className="info-section">
            <div className="info-item">
              <span className="info-label">Server:</span>
              <span className="info-value">{signalingServerUrl}</span>
            </div>
            <div className="info-item">
              <span className="info-label">Audio Status:</span>
              <span className="info-value">
                {remoteAudioStream ? 'Receiving' : 'No Audio'}
              </span>
            </div>
          </div>
        </div>

        <audio
          ref={audioRef}
          autoPlay
          playsInline
          style={{ display: 'none' }}
        />
      </div>
    </div>
  );
};

export default VoiceChat;