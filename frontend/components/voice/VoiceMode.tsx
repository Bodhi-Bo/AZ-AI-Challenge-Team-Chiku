'use client';

import { AnimatePresence } from 'framer-motion';
import VoiceTransition from './VoiceTransition';
import VoiceMascot from './VoiceMascot';
import WaveformVisualizer from './WaveformVisualizer';
import TranscriptionDisplay from './TranscriptionDisplay';
import VoiceControls from './VoiceControls';

import { useVoiceConversation } from '@/hooks/useVoiceConversation';
import { useEffect } from 'react';
import VoiceBackground from '../backgrounds/VoiceBackground';

interface VoiceModeProps {
  isActive: boolean;
  onClose: () => void;
}

export default function VoiceMode({ isActive, onClose }: VoiceModeProps) {
  const { phase, transcription, isListening, isSpeaking, start, stop } =
    useVoiceConversation();

  // Auto-start/stop with lifecycle
  useEffect(() => {
    if (isActive) {
      start();
    } else {
      stop();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isActive]);

  const handleClose = () => {
    stop();
    onClose();
  };

  return (
    <AnimatePresence>
      {isActive && (
        <VoiceTransition isAnimating={isActive}>
          <div className='fixed inset-0 z-50 flex'>
            {/* Voice Experience Area */}
            <div className='flex-1 relative'>
              <VoiceBackground />

              <div className='relative z-10 h-full flex flex-col items-center justify-center p-8'>
                {/* Animated Mascot */}
                <VoiceMascot
                  status={
                    isSpeaking ? 'speaking' : isListening ? 'listening' : 'idle'
                  }
                  className='mb-12'
                />

                {/* Waveform Visualization */}
                <WaveformVisualizer
                  audioStream={null}
                  isActive={isListening || isSpeaking}
                  className='mb-8'
                />

                {/* Live Transcription */}
                <TranscriptionDisplay
                  text={transcription}
                  isListening={isListening}
                  className='mb-12'
                />

                {/* Controls */}
                <VoiceControls
                  isListening={isListening}
                  onToggle={isListening ? stop : start}
                  onEnd={handleClose}
                />

                <div className='text-xs text-muted-foreground mt-4'>
                  Phase: {phase}
                </div>
              </div>
            </div>
          </div>
        </VoiceTransition>
      )}
    </AnimatePresence>
  );
}
