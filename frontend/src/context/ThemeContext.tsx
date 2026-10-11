import { createContext, useContext, useEffect, useState, useCallback, ReactNode } from 'react';
import { useAuth } from './AuthContext';
import { profileApi } from '@/services/api';
import type { Theme, FontSize } from '@/types';

interface ThemeContextType {
  theme: Theme;
  resolvedTheme: 'light' | 'dark';
  fontSize: FontSize;
  setTheme: (theme: Theme) => void;
  setFontSize: (size: FontSize) => void;
  toggleTheme: () => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

const FONT_SIZE_MAP: Record<string, string> = {
  sm: '14px',
  md: '16px',
  lg: '18px',
  small: '14px',
  medium: '16px',
  large: '18px',
};

function normalizeTheme(value?: string): Theme {
  if (value === 'light' || value === 'dark' || value === 'system') return value;
  return 'system';
}

function normalizeFontSize(value?: string): FontSize {
  const map: Record<string, FontSize> = {
    sm: 'sm',
    md: 'md',
    lg: 'lg',
    small: 'sm',
    medium: 'md',
    large: 'lg',
  };
  return (value && map[value]) || 'md';
}

function toApiFontSize(size: FontSize): string {
  const map: Record<FontSize, string> = {
    sm: 'small',
    md: 'medium',
    lg: 'large',
    small: 'small',
    medium: 'medium',
    large: 'large',
  };
  return map[size] || 'medium';
}

function getSystemTheme(): 'light' | 'dark' {
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}

export function ThemeProvider({ children }: { children: ReactNode }) {
  const { user, updateUser } = useAuth();

  const [theme, setThemeState] = useState<Theme>(() => {
    const stored = localStorage.getItem('theme');
    return normalizeTheme(stored || undefined);
  });

  const [fontSize, setFontSizeState] = useState<FontSize>(() => {
    const stored = localStorage.getItem('fontSize');
    return normalizeFontSize(stored || undefined);
  });

  const resolvedTheme: 'light' | 'dark' =
    theme === 'system' ? getSystemTheme() : theme;

  const setTheme = useCallback(
    async (newTheme: Theme) => {
      setThemeState(newTheme);
      localStorage.setItem('theme', newTheme);
      if (user) {
        try {
          await profileApi.update({ theme: newTheme });
          updateUser({ theme: newTheme });
        } catch {
          /* local preference still applied */
        }
      }
    },
    [user, updateUser]
  );

  const setFontSize = useCallback(
    async (size: FontSize) => {
      const normalized = normalizeFontSize(size);
      setFontSizeState(normalized);
      localStorage.setItem('fontSize', normalized);
      if (user) {
        try {
          const apiSize = toApiFontSize(normalized);
          await profileApi.update({ font_size: apiSize });
          updateUser({ font_size: apiSize });
        } catch {
          /* local preference still applied */
        }
      }
    },
    [user, updateUser]
  );

  const toggleTheme = useCallback(() => {
    setTheme(resolvedTheme === 'dark' ? 'light' : 'dark');
  }, [resolvedTheme, setTheme]);

  useEffect(() => {
    if (user?.theme) setThemeState(normalizeTheme(user.theme));
    if (user?.font_size) setFontSizeState(normalizeFontSize(user.font_size));
  }, [user?.theme, user?.font_size]);

  useEffect(() => {
    const root = document.documentElement;
    root.classList.remove('light', 'dark');
    root.classList.add(resolvedTheme);
    root.style.fontSize = FONT_SIZE_MAP[fontSize] || FONT_SIZE_MAP.md;
  }, [resolvedTheme, fontSize]);

  useEffect(() => {
    if (theme !== 'system') return;
    const mq = window.matchMedia('(prefers-color-scheme: dark)');
    const handler = () => {
      document.documentElement.classList.remove('light', 'dark');
      document.documentElement.classList.add(getSystemTheme());
    };
    mq.addEventListener('change', handler);
    return () => mq.removeEventListener('change', handler);
  }, [theme]);

  return (
    <ThemeContext.Provider
      value={{ theme, resolvedTheme, fontSize, setTheme, setFontSize, toggleTheme }}
    >
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (!context) throw new Error('useTheme must be used within ThemeProvider');
  return context;
}
