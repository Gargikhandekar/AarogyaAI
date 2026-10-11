// Shared API types. These mirror the Pydantic schemas in backend/app/schemas.

export type Theme = 'light' | 'dark' | 'system';
export type FontSize = 'sm' | 'md' | 'lg' | 'small' | 'medium' | 'large';

// ── Auth ────────────────────────────────────────────────────────────────────

export interface User {
  id: number;
  name: string;
  email: string;
  photo_url?: string | null;
  is_admin: boolean;
  theme: string;
  font_size: string;
  created_at: string;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterCredentials {
  name: string;
  email: string;
  password: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

// ── Chat ────────────────────────────────────────────────────────────────────

export interface SourceDocument {
  id?: number; // citation number used as [n] in the answer
  question: string;
  answer: string;
  category?: string | null;
  source?: string | null;
  source_url?: string | null;
  score: number;
}

export interface Message {
  id: string | number;
  role: 'user' | 'assistant';
  content: string;
  timestamp?: string;
  created_at?: string;
  sources?: SourceDocument[] | null;
  confidence?: number | null;
  category?: string | null;
  is_emergency?: boolean;
  isEmergency?: boolean;
  feedback?: 'like' | 'dislike' | null;
  disclaimer?: string;
}

export interface ChatRequest {
  message: string;
  chat_id?: number | null;
  category?: string | null;
}

export interface ChatResponse {
  chat_id: number;
  message_id: number;
  answer: string;
  confidence: number;
  sources: SourceDocument[];
  category?: string | null;
  is_emergency: boolean;
  disclaimer: string;
  timestamp: string;
}

export interface Conversation {
  id: number;
  title: string;
  category?: string | null;
  created_at: string;
  updated_at: string;
  message_count: number;
  messages?: Message[];
}

// ── Profile & content ───────────────────────────────────────────────────────

export interface ProfileStats {
  total_chats: number;
  total_messages: number;
  favorite_count: number;
  member_since: string;
}

export interface HealthTip {
  tip: string;
  category: string;
  date: string;
}

export interface NewsItem {
  title: string;
  summary: string;
  tag: string;
}

// ── Tools ───────────────────────────────────────────────────────────────────

export interface BMIRequest {
  height_cm: number;
  weight_kg: number;
}

export interface BMIResult {
  bmi: number;
  category: string;
  advice: string;
}

export interface SymptomCheckRequest {
  symptoms: string[];
  duration_days?: number;
  severity?: string;
}

export interface SymptomCheckResult {
  symptoms: string[];
  summary: string;
  urgency: string;
  advice: string;
  disclaimer: string;
}

export interface Reminder {
  id: number;
  medicine_name: string;
  dosage: string;
  schedule_time: string;
  notes?: string | null;
  is_active: boolean;
  created_at: string;
}

export interface Hospital {
  name: string;
  address: string;
  phone: string;
  distance_km: number;
  specialties: string[];
}

// ── Admin ───────────────────────────────────────────────────────────────────

export interface AdminStats {
  total_users: number;
  total_chats: number;
  total_messages: number;
  total_documents: number;
  emergency_flags: number;
  active_users_today: number;
}

export interface AdminLog {
  id: number;
  level: string;
  message: string;
  user_id?: number | null;
  created_at: string;
}
