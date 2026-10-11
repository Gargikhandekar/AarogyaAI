import { useState, useCallback, useRef, useEffect } from 'react';

interface SpeechOptions {
  onResult?: (text: string) => void;
  onError?: (error: string) => void;
  lang?: string;
}

export function useSpeech({ onResult, onError, lang = 'en-US' }: SpeechOptions = {}) {
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [transcript, setTranscript] = useState('');
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const recognitionRef = useRef<any>(null);

  const win = typeof window !== 'undefined' ? (window as unknown as Record<string, unknown>) : null;
  const isSupported = !!win && ('SpeechRecognition' in win || 'webkitSpeechRecognition' in win);

  useEffect(() => {
    if (!isSupported || !win) return;

    const SpeechRecognitionCtor =
      (win.SpeechRecognition as new () => unknown) ||
      (win.webkitSpeechRecognition as new () => unknown);

    const recognition = new SpeechRecognitionCtor() as {
      continuous: boolean;
      interimResults: boolean;
      lang: string;
      start: () => void;
      stop: () => void;
      abort: () => void;
      onresult: ((event: { resultIndex: number; results: ArrayLike<{ isFinal: boolean; 0: { transcript: string } }> }) => void) | null;
      onerror: ((event: { error: string }) => void) | null;
      onend: (() => void) | null;
    };

    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.lang = lang;

    recognition.onresult = (event) => {
      let finalTranscript = '';
      for (let i = event.resultIndex; i < event.results.length; i++) {
        if (event.results[i].isFinal) {
          finalTranscript += event.results[i][0].transcript;
        }
      }
      if (finalTranscript) {
        setTranscript(finalTranscript);
        onResult?.(finalTranscript);
      }
    };

    recognition.onerror = (event) => {
      setIsListening(false);
      onError?.(event.error);
    };

    recognition.onend = () => setIsListening(false);
    recognitionRef.current = recognition;

    return () => recognition.abort();
  }, [isSupported, lang, onResult, onError, win]);

  const startListening = useCallback(() => {
    if (!recognitionRef.current) return;
    setTranscript('');
    setIsListening(true);
    recognitionRef.current.start();
  }, []);

  const stopListening = useCallback(() => {
    recognitionRef.current?.stop();
    setIsListening(false);
  }, []);

  const speak = useCallback(
    (text: string) => {
      if (!('speechSynthesis' in window)) {
        onError?.('Text-to-speech not supported');
        return;
      }
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = lang;
      utterance.onstart = () => setIsSpeaking(true);
      utterance.onend = () => setIsSpeaking(false);
      utterance.onerror = () => setIsSpeaking(false);
      window.speechSynthesis.speak(utterance);
    },
    [lang, onError]
  );

  const stopSpeaking = useCallback(() => {
    window.speechSynthesis.cancel();
    setIsSpeaking(false);
  }, []);

  return {
    isSupported,
    isListening,
    isSpeaking,
    transcript,
    startListening,
    stopListening,
    speak,
    stopSpeaking,
  };
}
