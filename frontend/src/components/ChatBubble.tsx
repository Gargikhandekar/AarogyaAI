import { motion } from 'framer-motion';
import type { Message } from '@/types';
import MarkdownRenderer from './MarkdownRenderer';
import {
  HiClipboardCopy,
  HiThumbUp,
  HiThumbDown,
  HiRefresh,
  HiVolumeUp,
  HiExclamation,
} from 'react-icons/hi';
import { useState } from 'react';

interface ChatBubbleProps {
  message: Message;
  isStreaming?: boolean;
  onFeedback?: (id: string | number, feedback: 'like' | 'dislike') => void;
  onRegenerate?: () => void;
  onSpeak?: (text: string) => void;
  showActions?: boolean;
}

export default function ChatBubble({
  message,
  isStreaming = false,
  onFeedback,
  onRegenerate,
  onSpeak,
  showActions = true,
}: ChatBubbleProps) {
  const [copied, setCopied] = useState(false);
  const isUser = message.role === 'user';
  const isAssistant = message.role === 'assistant';
  const isEmergency = message.is_emergency ?? message.isEmergency;
  const confidence = message.confidence ?? null;

  const handleCopy = async () => {
    await navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={`flex gap-3 ${isUser ? 'flex-row-reverse' : 'flex-row'} group`}
    >
      <div
        className={`flex-shrink-0 w-8 h-8 rounded-xl flex items-center justify-center text-sm font-bold ${
          isUser
            ? 'bg-primary text-white'
            : 'bg-gradient-to-br from-primary to-secondary text-white'
        }`}
      >
        {isUser ? 'U' : 'A'}
      </div>

      <div className={`flex flex-col max-w-[85%] sm:max-w-[75%] ${isUser ? 'items-end' : 'items-start'}`}>
        <div
          className={`rounded-2xl px-4 py-3 ${
            isUser
              ? 'bg-primary text-white rounded-tr-sm'
              : isEmergency
              ? 'bg-red-50 dark:bg-red-900/20 border-2 border-red-300 dark:border-red-700 text-slate-800 dark:text-slate-100 rounded-tl-sm'
              : 'glass-card rounded-tl-sm text-slate-800 dark:text-slate-100'
          }`}
        >
          {isAssistant ? (
            <>
              {isEmergency && (
                <div className="flex items-center gap-2 text-red-600 dark:text-red-400 font-semibold mb-2 text-sm">
                  <HiExclamation className="w-4 h-4" />
                  Emergency Alert – Seek immediate medical attention
                </div>
              )}
              <MarkdownRenderer content={message.content || (isStreaming ? '▋' : '')} />
              {isStreaming && message.content && (
                <span className="inline-block w-2 h-4 bg-primary animate-pulse ml-0.5" />
              )}
            </>
          ) : (
            <p className="whitespace-pre-wrap">{message.content}</p>
          )}
        </div>

        {isAssistant && !isStreaming && message.content && (
          <>
            {message.sources && message.sources.length > 0 && (
              <div className="mt-2 space-y-2 w-full">
                <p className="text-xs font-medium text-slate-500">
                  Sources (MedQuAD passages{confidence !== null ? `, best match score ${confidence.toFixed(2)}` : ''}):
                </p>
                {message.sources.map((source, i) => (
                  <div
                    key={source.id ?? i}
                    className={`text-xs p-2 rounded-lg border ${
                      source.cited === false
                        ? 'bg-transparent border-dashed border-slate-200 dark:border-slate-700 opacity-70'
                        : 'bg-slate-50 dark:bg-slate-800/50 border-slate-200 dark:border-slate-700'
                    }`}
                  >
                    <p className="font-medium text-slate-700 dark:text-slate-200 truncate">
                      [{source.id ?? i + 1}] {source.question}
                    </p>
                    <p className="text-slate-500 mt-0.5 truncate">
                      {source.source_url ? (
                        <a
                          href={source.source_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-primary hover:underline"
                        >
                          {source.source || 'Source'}
                        </a>
                      ) : (
                        source.source
                      )}
                      {' · '}score {source.score.toFixed(2)}
                      {source.cited === false && ' · retrieved, not cited'}
                    </p>
                  </div>
                ))}
              </div>
            )}

            <p className="mt-2 text-xs text-slate-400 italic">
              ⚕️ {message.disclaimer || 'This is AI-generated health information, not medical advice. Consult a healthcare professional.'}
            </p>

            {showActions && (
              <div className="mt-2 flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                <ActionButton
                  icon={<HiClipboardCopy className="w-4 h-4" />}
                  label={copied ? 'Copied!' : 'Copy'}
                  onClick={handleCopy}
                />
                <ActionButton
                  icon={<HiThumbUp className="w-4 h-4" />}
                  label="Like"
                  active={message.feedback === 'like'}
                  onClick={() => onFeedback?.(message.id, 'like')}
                />
                <ActionButton
                  icon={<HiThumbDown className="w-4 h-4" />}
                  label="Dislike"
                  active={message.feedback === 'dislike'}
                  onClick={() => onFeedback?.(message.id, 'dislike')}
                />
                {onRegenerate && (
                  <ActionButton
                    icon={<HiRefresh className="w-4 h-4" />}
                    label="Regenerate"
                    onClick={onRegenerate}
                  />
                )}
                {onSpeak && (
                  <ActionButton
                    icon={<HiVolumeUp className="w-4 h-4" />}
                    label="Read aloud"
                    onClick={() => onSpeak(message.content)}
                  />
                )}
              </div>
            )}
          </>
        )}
      </div>
    </motion.div>
  );
}

function ActionButton({
  icon,
  label,
  onClick,
  active = false,
}: {
  icon: React.ReactNode;
  label: string;
  onClick: () => void;
  active?: boolean;
}) {
  return (
    <button
      onClick={onClick}
      title={label}
      className={`p-1.5 rounded-lg text-xs transition-colors ${
        active
          ? 'bg-primary/10 text-primary'
          : 'text-slate-400 hover:text-slate-600 hover:bg-slate-100 dark:hover:bg-slate-800 dark:hover:text-slate-300'
      }`}
    >
      {icon}
    </button>
  );
}
