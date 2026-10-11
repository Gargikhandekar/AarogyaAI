import { useState, useRef, useEffect, KeyboardEvent } from 'react';
import { motion } from 'framer-motion';
import { HiPaperAirplane, HiMicrophone, HiStop, HiPaperClip } from 'react-icons/hi';
import { useSpeech } from '@/hooks/useSpeech';

interface MessageInputProps {
  onSend: (message: string) => void;
  onStop?: () => void;
  isStreaming?: boolean;
  disabled?: boolean;
  placeholder?: string;
}

export default function MessageInput({
  onSend,
  onStop,
  isStreaming = false,
  disabled = false,
  placeholder = 'Ask about your health...',
}: MessageInputProps) {
  const [input, setInput] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const { isListening, isSupported, startListening, stopListening } = useSpeech({
    onResult: (text) => {
      setInput((prev) => (prev ? `${prev} ${text}` : text));
    },
  });

  useEffect(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      textarea.style.height = `${Math.min(textarea.scrollHeight, 200)}px`;
    }
  }, [input]);

  const handleSend = () => {
    if (!input.trim() || disabled || isStreaming) return;
    onSend(input.trim());
    setInput('');
    if (textareaRef.current) textareaRef.current.style.height = 'auto';
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const toggleVoice = () => {
    if (isListening) stopListening();
    else startListening();
  };

  return (
    <div className="border-t border-slate-200 dark:border-slate-700 bg-white/80 dark:bg-slate-900/80 backdrop-blur-xl p-4">
      <div className="max-w-4xl mx-auto">
        <div className="flex items-end gap-2 glass-card p-2">
          <button
            disabled
            title="Attachments coming soon"
            className="flex-shrink-0 p-2.5 rounded-xl text-slate-300 dark:text-slate-600 cursor-not-allowed"
          >
            <HiPaperClip className="w-5 h-5" />
          </button>

          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={isListening ? 'Listening...' : placeholder}
            disabled={disabled || isStreaming}
            rows={1}
            className="flex-1 resize-none bg-transparent px-2 py-2.5 text-slate-800 dark:text-slate-100 placeholder:text-slate-400 focus:outline-none max-h-[200px] chat-scrollbar"
          />

          {isSupported && (
            <motion.button
              whileTap={{ scale: 0.9 }}
              onClick={toggleVoice}
              disabled={disabled || isStreaming}
              className={`flex-shrink-0 p-2.5 rounded-xl transition-colors ${
                isListening
                  ? 'bg-red-100 text-red-500 dark:bg-red-900/30 animate-pulse'
                  : 'text-slate-400 hover:text-primary hover:bg-primary/10'
              }`}
              title={isListening ? 'Stop listening' : 'Voice input'}
            >
              <HiMicrophone className="w-5 h-5" />
            </motion.button>
          )}

          {isStreaming ? (
            <motion.button
              whileTap={{ scale: 0.9 }}
              onClick={onStop}
              className="flex-shrink-0 p-2.5 rounded-xl bg-red-500 text-white hover:bg-red-600 transition-colors"
              title="Stop generating"
            >
              <HiStop className="w-5 h-5" />
            </motion.button>
          ) : (
            <motion.button
              whileTap={{ scale: 0.9 }}
              onClick={handleSend}
              disabled={!input.trim() || disabled}
              className="flex-shrink-0 p-2.5 rounded-xl bg-primary text-white hover:bg-primary-600 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
              title="Send message"
            >
              <HiPaperAirplane className="w-5 h-5" />
            </motion.button>
          )}
        </div>
        <p className="text-center text-xs text-slate-400 mt-2">
          Aarogya AI may produce inaccurate information. Not a substitute for professional medical advice.
        </p>
      </div>
    </div>
  );
}
