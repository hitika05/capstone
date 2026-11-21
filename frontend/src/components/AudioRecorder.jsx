import React, { useState, useRef } from 'react';
import { Mic, Square } from 'lucide-react';

const AudioRecorder = ({ onComplete, onStart, onStop, isProcessing, uiText }) => {
  const [isRecording, setIsRecording] = useState(false);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

  const text = uiText || {
    start: 'Start Recording',
    stop: 'Stop Recording',
    processing: 'Processing audio...',
    recording: 'Recording! Click to stop.',
    idle: 'Click mic to record your prompt',
    micError: 'Microphone access denied or not available. Please allow microphone permissions and try again.'
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorderRef.current = new MediaRecorder(stream);
      audioChunksRef.current = [];

      mediaRecorderRef.current.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorderRef.current.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        onStop?.();
        onComplete(audioBlob);
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorderRef.current.start();
      onStart?.();
      setIsRecording(true);
    } catch (error) {
      console.error("Error accessing microphone:", error);
      alert(text.micError);
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  return (
    <div style={{display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '1.5rem', width: '100%'}}>
      <button 
        className={`mic-btn ${isRecording ? 'recording' : ''}`}
        onClick={isRecording ? stopRecording : startRecording}
        disabled={isProcessing}
        title={isRecording ? text.stop : text.start}
      >
        {isRecording ? <Square size={40} fill="white" /> : <Mic size={40} />}
      </button>
      <p style={{color: 'var(--text-muted)', fontSize: '0.9rem', textAlign: 'center'}}>
        {isProcessing ? text.processing :
         isRecording ? text.recording : text.idle}
      </p>
    </div>
  );
};

export default AudioRecorder;
