import { useState, useCallback, useRef, useEffect } from 'react';
import { chatApi, historyApi } from '@/services/api';
import type { Message, Conversation, SourceDocument } from '@/types';

interface UseChatOptions {
  conversationId?: string;
  onConversationCreated?: (id: string) => void;
}

function normalizeMessages(raw: Message[] | undefined): Message[] {
  if (!raw) return [];
  return raw.map((m) => ({
    ...m,
    timestamp: m.created_at || m.timestamp || new Date().toISOString(),
    isEmergency: m.is_emergency ?? m.isEmergency,
  }));
}

export function useChat({ conversationId, onConversationCreated }: UseChatOptions = {}) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [currentConversationId, setCurrentConversationId] = useState<number | undefined>(
    conversationId ? Number(conversationId) : undefined
  );
  const abortControllerRef = useRef<AbortController | null>(null);

  useEffect(() => {
    if (conversationId) {
      const id = Number(conversationId);
      setCurrentConversationId(id);
      loadConversation(id);
    } else {
      setMessages([]);
      setCurrentConversationId(undefined);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [conversationId]);

  const loadConversation = async (id: number | string) => {
    try {
      setIsLoading(true);
      const { data } = await historyApi.getById(id);
      setMessages(normalizeMessages(data.messages));
    } catch {
      setError('Failed to load conversation');
    } finally {
      setIsLoading(false);
    }
  };

  const stopGeneration = useCallback(() => {
    abortControllerRef.current?.abort();
    setIsStreaming(false);
  }, []);

  const applyAssistant = (
    tempId: string,
    payload: {
      id: number;
      content: string;
      confidence?: number;
      sources?: SourceDocument[];
      is_emergency?: boolean;
      disclaimer?: string;
    }
  ) => {
    setMessages((prev) =>
      prev.map((m) =>
        m.id === tempId
          ? {
              ...m,
              id: payload.id,
              content: payload.content,
              confidence: payload.confidence,
              sources: payload.sources,
              is_emergency: payload.is_emergency,
              isEmergency: payload.is_emergency,
              disclaimer: payload.disclaimer,
            }
          : m
      )
    );
  };

  const sendMessage = useCallback(
    async (content: string, useStream = true) => {
      if (!content.trim() || isStreaming) return;

      const userMessage: Message = {
        id: crypto.randomUUID(),
        role: 'user',
        content: content.trim(),
        timestamp: new Date().toISOString(),
      };

      setMessages((prev) => [...prev, userMessage]);
      setError(null);
      setIsStreaming(true);

      const tempAssistantId = crypto.randomUUID();
      const assistantMessage: Message = {
        id: tempAssistantId,
        role: 'assistant',
        content: '',
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, assistantMessage]);
      abortControllerRef.current = new AbortController();

      const request = {
        message: content.trim(),
        chat_id: currentConversationId ?? null,
      };

      try {
        if (useStream) {
          try {
            let fullContent = '';
            let meta: {
              chat_id: number;
              message_id?: number | null;
              confidence: number;
              sources: SourceDocument[];
              is_emergency: boolean;
              disclaimer: string;
            } | null = null;
            let doneMessageId: number | undefined;

            for await (const evt of chatApi.stream(request, abortControllerRef.current.signal)) {
              if (evt.kind === 'meta') {
                meta = evt.meta;
                if (!currentConversationId) {
                  setCurrentConversationId(evt.meta.chat_id);
                  onConversationCreated?.(String(evt.meta.chat_id));
                }
              } else if (evt.kind === 'token') {
                fullContent += evt.content;
                setMessages((prev) =>
                  prev.map((m) =>
                    m.id === tempAssistantId ? { ...m, content: fullContent } : m
                  )
                );
              } else if (evt.kind === 'done') {
                doneMessageId = evt.message_id;
              }
            }

            if (meta) {
              applyAssistant(tempAssistantId, {
                id: doneMessageId ?? meta.message_id ?? Date.now(),
                content: fullContent,
                confidence: meta.confidence,
                sources: meta.sources,
                is_emergency: meta.is_emergency,
                disclaimer: meta.disclaimer,
              });
            }
          } catch (streamErr) {
            if ((streamErr as Error).name === 'AbortError') return;
            const { data } = await chatApi.send(request);
            applyAssistant(tempAssistantId, {
              id: data.message_id,
              content: data.answer,
              confidence: data.confidence,
              sources: data.sources,
              is_emergency: data.is_emergency,
              disclaimer: data.disclaimer,
            });
            if (!currentConversationId) {
              setCurrentConversationId(data.chat_id);
              onConversationCreated?.(String(data.chat_id));
            }
          }
        } else {
          const { data } = await chatApi.send(request);
          applyAssistant(tempAssistantId, {
            id: data.message_id,
            content: data.answer,
            confidence: data.confidence,
            sources: data.sources,
            is_emergency: data.is_emergency,
            disclaimer: data.disclaimer,
          });
          if (!currentConversationId) {
            setCurrentConversationId(data.chat_id);
            onConversationCreated?.(String(data.chat_id));
          }
        }
      } catch {
        setError('Failed to send message. Please try again.');
        setMessages((prev) => prev.filter((m) => m.id !== tempAssistantId));
      } finally {
        setIsStreaming(false);
      }
    },
    [currentConversationId, isStreaming, onConversationCreated]
  );

  const regenerate = useCallback(async () => {
    const lastUserMsg = [...messages].reverse().find((m) => m.role === 'user');
    if (!lastUserMsg) return;
    setMessages((prev) => {
      const lastAssistantIdx = prev.map((m) => m.role).lastIndexOf('assistant');
      return lastAssistantIdx >= 0 ? prev.slice(0, lastAssistantIdx) : prev;
    });
    await sendMessage(lastUserMsg.content);
  }, [messages, sendMessage]);

  const setFeedback = useCallback(async (messageId: string | number, feedback: 'like' | 'dislike') => {
    setMessages((prev) =>
      prev.map((m) =>
        m.id === messageId ? { ...m, feedback: m.feedback === feedback ? null : feedback } : m
      )
    );
    if (typeof messageId === 'number') {
      try {
        const next = feedback;
        await chatApi.feedback(messageId, next);
      } catch {
        /* ignore */
      }
    }
  }, []);

  const newChat = useCallback(() => {
    stopGeneration();
    setMessages([]);
    setCurrentConversationId(undefined);
    setError(null);
  }, [stopGeneration]);

  return {
    messages,
    isLoading,
    isStreaming,
    error,
    currentConversationId,
    sendMessage,
    stopGeneration,
    regenerate,
    setFeedback,
    newChat,
    loadConversation,
  };
}

export function useConversations() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const fetchConversations = useCallback(async (search?: string) => {
    try {
      setIsLoading(true);
      const { data } = await historyApi.getAll(search);
      setConversations(data);
    } catch {
      setConversations([]);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const deleteConversation = useCallback(async (id: number | string) => {
    await historyApi.delete(id);
    setConversations((prev) => prev.filter((c) => String(c.id) !== String(id)));
  }, []);

  const renameConversation = useCallback(async (id: number | string, title: string) => {
    const { data } = await historyApi.update(id, { title });
    setConversations((prev) => prev.map((c) => (c.id === data.id ? data : c)));
  }, []);

  useEffect(() => {
    fetchConversations();
  }, [fetchConversations]);

  return { conversations, isLoading, fetchConversations, deleteConversation, renameConversation };
}
