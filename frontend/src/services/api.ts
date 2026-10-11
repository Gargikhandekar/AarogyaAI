import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';
import type {
  AuthResponse,
  LoginCredentials,
  RegisterCredentials,
  User,
  ChatRequest,
  ChatResponse,
  Conversation,
  ProfileStats,
  HealthTip,
  NewsItem,
  BMIRequest,
  BMIResult,
  SymptomCheckRequest,
  SymptomCheckResult,
  Reminder,
  Hospital,
  AdminStats,
  AdminLog,
  AnswerStatus,
  SourceDocument,
} from '@/types';

// An empty VITE_API_URL means same origin (Docker: nginx proxies /api to the API).
const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';

const api = axios.create({
  baseURL: API_URL,
  headers: { 'Content-Type': 'application/json' },
  timeout: 120000,
});

api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = localStorage.getItem('token');
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error: AxiosError<{ detail?: string }>) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      if (!window.location.pathname.includes('/login')) {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export const authApi = {
  register: (data: RegisterCredentials) => api.post<AuthResponse>('/api/auth/register', data),
  login: (data: LoginCredentials) => api.post<AuthResponse>('/api/auth/login', data),
  me: () => api.get<User>('/api/auth/me'),
};

/** An error the server reported (e.g. 503 "knowledge base not loaded"); shown as-is. */
export class ServerError extends Error {}

/** Pull the FastAPI `detail` message out of an axios error, if there is one. */
export function errorDetail(err: unknown): string | undefined {
  if (err instanceof ServerError) return err.message;
  const detail = (err as AxiosError<{ detail?: unknown }>)?.response?.data?.detail;
  return typeof detail === 'string' ? detail : undefined;
}

export type StreamMeta = {
  type: 'meta';
  chat_id: number;
  message_id?: number | null;
  status: AnswerStatus;
  confidence: number;
  sources: ChatResponse['sources'];
  category?: string | null;
  is_emergency: boolean;
  disclaimer: string;
};

export const chatApi = {
  send: (data: ChatRequest) => api.post<ChatResponse>('/api/chat', data),
  stream: async function* (
    data: ChatRequest,
    signal?: AbortSignal
  ): AsyncGenerator<
    | { kind: 'meta'; meta: StreamMeta }
    | { kind: 'token'; content: string }
    | { kind: 'done'; message_id?: number; status?: AnswerStatus; sources?: SourceDocument[] },
    void,
    unknown
  > {
    const token = localStorage.getItem('token');
    const response = await fetch(`${API_URL}/api/chat/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify(data),
      signal,
    });

    if (!response.ok) {
      const body = await response.json().catch(() => null);
      if (typeof body?.detail === 'string') throw new ServerError(body.detail);
      throw new Error(`Stream failed: ${response.statusText}`);
    }
    const reader = response.body?.getReader();
    if (!reader) throw new Error('No response body');

    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (!line.startsWith('data: ')) continue;
        const payload = line.slice(6);
        let parsed;
        try {
          parsed = JSON.parse(payload);
        } catch {
          continue; /* ignore partial JSON */
        }
        if (parsed.type === 'meta') yield { kind: 'meta', meta: parsed };
        else if (parsed.type === 'token' && parsed.content) {
          yield { kind: 'token', content: parsed.content };
        } else if (parsed.type === 'error') {
          throw new ServerError(parsed.detail || 'Something went wrong while answering.');
        } else if (parsed.type === 'done') {
          yield {
            kind: 'done',
            message_id: parsed.message_id,
            status: parsed.status,
            sources: parsed.sources,
          };
          return;
        }
      }
    }
  },
  feedback: (messageId: number, feedback: 'like' | 'dislike' | 'none') =>
    api.post(`/api/messages/${messageId}/feedback`, { feedback }),
};

export const historyApi = {
  getAll: (search?: string) =>
    api.get<Conversation[]>('/api/history', { params: search ? { search } : undefined }),
  getById: (id: number | string) => api.get<Conversation>(`/api/history/${id}`),
  update: (id: number | string, data: { title: string }) =>
    api.put<Conversation>(`/api/history/${id}`, data),
  delete: (id: number | string) => api.delete(`/api/history/${id}`),
  deleteAll: () => api.delete('/api/history'),
};

export const profileApi = {
  get: () => api.get<User>('/api/profile'),
  update: (data: Record<string, unknown>) => api.put<User>('/api/profile', data),
  delete: () => api.delete('/api/profile'),
  stats: () => api.get<ProfileStats>('/api/profile/stats'),
  export: () => api.get('/api/profile/export', { responseType: 'blob' }),
};

export const contentApi = {
  suggestions: () => api.get<{ suggestions: string[] }>('/api/suggestions'),
  categories: () => api.get<{ categories: string[] }>('/api/categories'),
  healthTip: () => api.get<HealthTip>('/api/health-tip'),
  news: () => api.get<{ articles: NewsItem[] }>('/api/news'),
};

export const toolsApi = {
  bmi: (data: BMIRequest) => api.post<BMIResult>('/api/bmi', data),
  symptomChecker: (data: SymptomCheckRequest) =>
    api.post<SymptomCheckResult>('/api/symptom-checker', data),
  voice: (data: { text?: string; language?: string }) => api.post('/api/voice', data),
  reminders: {
    getAll: () => api.get<Reminder[]>('/api/reminders'),
    create: (data: {
      medicine_name: string;
      dosage: string;
      schedule_time: string;
      notes?: string;
    }) => api.post<Reminder>('/api/reminders', data),
    delete: (id: number) => api.delete(`/api/reminders/${id}`),
  },
  hospitals: (city?: string) =>
    api.get<Hospital[]>('/api/hospitals', { params: city ? { city } : undefined }),
};

export const adminApi = {
  stats: () => api.get<AdminStats>('/api/admin/dashboard'),
  users: () => api.get<User[]>('/api/admin/users'),
  chats: () => api.get('/api/admin/chats'),
  logs: () => api.get<AdminLog[]>('/api/admin/logs'),
  analytics: () => api.get('/api/admin/analytics'),
  uploadDataset: (file: File) => {
    const form = new FormData();
    form.append('file', file);
    return api.post('/api/admin/dataset/upload', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
};

export default api;
