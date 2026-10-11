import { useEffect, useRef, useState } from 'react';
import { useParams, useSearchParams, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import Layout from '@/components/Layout';
import Sidebar from '@/components/Sidebar';
import ChatBubble from '@/components/ChatBubble';
import MessageInput from '@/components/MessageInput';
import LoadingSkeleton from '@/components/LoadingSkeleton';
import { useChat, useConversations } from '@/hooks/useChat';
import { useSpeech } from '@/hooks/useSpeech';
import { HiMenu, HiSparkles } from 'react-icons/hi';

const STARTER_PROMPTS = [
  'What are common symptoms of the flu?',
  'How can I manage stress naturally?',
  'What is a healthy BMI range?',
  'Tips for better sleep hygiene',
];

export default function Chat() {
  const { conversationId } = useParams();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const { conversations, fetchConversations, deleteConversation } = useConversations();
  const {
    messages,
    isLoading,
    isStreaming,
    error,
    sendMessage,
    stopGeneration,
    regenerate,
    setFeedback,
    newChat,
    loadConversation,
  } = useChat({
    conversationId,
    onConversationCreated: (id) => {
      navigate(`/chat/${id}`, { replace: true });
      fetchConversations();
    },
  });

  const { speak } = useSpeech();

  // Auto-scroll
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isStreaming]);

  // Handle query params
  useEffect(() => {
    const q = searchParams.get('q');
    if (q && messages.length === 0) {
      sendMessage(q);
    }
  }, [searchParams]);

  const handleNewChat = () => {
    newChat();
    navigate('/chat');
  };

  const handleSelectConversation = (id: number) => {
    navigate(`/chat/${id}`);
    loadConversation(id);
  };

  const handleDeleteConversation = async (id: number) => {
    await deleteConversation(id);
    if (conversationId === String(id)) handleNewChat();
  };

  return (
    <Layout fullWidth>
      <div className="flex h-[calc(100vh-4rem)]">
        <Sidebar
          conversations={conversations}
          activeId={conversationId}
          onSelect={handleSelectConversation}
          onNewChat={handleNewChat}
          onDelete={handleDeleteConversation}
          onSearch={fetchConversations}
          isOpen={sidebarOpen}
          onClose={() => setSidebarOpen(false)}
        />

        <div className="flex-1 flex flex-col min-w-0">
          {/* Chat header */}
          <div className="flex items-center gap-3 px-4 py-3 border-b border-slate-200 dark:border-slate-700 bg-white/80 dark:bg-slate-900/80 backdrop-blur-xl">
            <button
              onClick={() => setSidebarOpen(true)}
              className="md:hidden p-2 rounded-xl hover:bg-slate-100 dark:hover:bg-slate-800"
            >
              <HiMenu className="w-5 h-5" />
            </button>
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-hero-gradient flex items-center justify-center">
                <HiSparkles className="w-4 h-4 text-white" />
              </div>
              <div>
                <h2 className="font-semibold text-slate-800 dark:text-white text-sm">Aarogya AI</h2>
                <p className="text-xs text-slate-400">Medical Assistant</p>
              </div>
            </div>
          </div>

          {/* Messages area */}
          <div className="flex-1 overflow-y-auto chat-scrollbar px-4 py-6">
            {isLoading ? (
              <LoadingSkeleton variant="chat" />
            ) : messages.length === 0 ? (
              <div className="max-w-2xl mx-auto text-center py-12">
                <motion.div
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  className="mb-8"
                >
                  <div className="w-16 h-16 rounded-2xl bg-hero-gradient flex items-center justify-center mx-auto mb-4 shadow-glow">
                    <HiSparkles className="w-8 h-8 text-white" />
                  </div>
                  <h2 className="font-display text-2xl font-bold text-slate-800 dark:text-white mb-2">
                    How can I help you today?
                  </h2>
                  <p className="text-slate-500 text-sm">
                    Ask me about symptoms, medications, nutrition, or general health topics.
                  </p>
                </motion.div>

                <div className="grid sm:grid-cols-2 gap-3">
                  {STARTER_PROMPTS.map((prompt) => (
                    <button
                      key={prompt}
                      onClick={() => sendMessage(prompt)}
                      className="glass-card p-4 text-sm text-slate-600 dark:text-slate-300 hover:text-primary hover:border-primary/30 transition-colors text-left"
                    >
                      {prompt}
                    </button>
                  ))}
                </div>

                <p className="text-xs text-slate-400 mt-8 italic">
                  ⚕️ For emergencies, call your local emergency number immediately. This AI is not a substitute for professional medical care.
                </p>
              </div>
            ) : (
              <div className="max-w-4xl mx-auto space-y-6">
                {messages.map((msg, i) => (
                  <ChatBubble
                    key={msg.id}
                    message={msg}
                    isStreaming={isStreaming && i === messages.length - 1 && msg.role === 'assistant'}
                    onFeedback={setFeedback}
                    onRegenerate={
                      msg.role === 'assistant' && i === messages.length - 1 && !isStreaming
                        ? regenerate
                        : undefined
                    }
                    onSpeak={speak}
                  />
                ))}
                <div ref={messagesEndRef} />
              </div>
            )}

            {error && (
              <div className="max-w-4xl mx-auto mt-4 p-3 rounded-xl bg-red-50 dark:bg-red-900/20 text-red-600 text-sm text-center">
                {error}
              </div>
            )}
          </div>

          <MessageInput
            onSend={sendMessage}
            onStop={stopGeneration}
            isStreaming={isStreaming}
          />
        </div>
      </div>
    </Layout>
  );
}
