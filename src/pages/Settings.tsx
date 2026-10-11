import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import Layout from '@/components/Layout';
import ThemeToggle from '@/components/ThemeToggle';
import { useAuth } from '@/context/AuthContext';
import { useTheme } from '@/context/ThemeContext';
import { profileApi, historyApi } from '@/services/api';
import type { Theme, FontSize } from '@/types';
import { HiDownload, HiTrash, HiSun, HiMoon, HiDesktopComputer } from 'react-icons/hi';

export default function Settings() {
  const { logout } = useAuth();
  const { theme, fontSize, setTheme, setFontSize } = useTheme();
  const navigate = useNavigate();
  const [exporting, setExporting] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const handleExport = async () => {
    setExporting(true);
    try {
      const { data } = await profileApi.export();
      const url = window.URL.createObjectURL(new Blob([data]));
      const a = document.createElement('a');
      a.href = url;
      a.download = `aarogya-chat-history-${new Date().toISOString().split('T')[0]}.json`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch {
      alert('Export failed. Please try again.');
    } finally {
      setExporting(false);
    }
  };

  const handleDeleteAccount = async () => {
    setDeleting(true);
    try {
      await profileApi.delete();
      logout();
      navigate('/');
    } catch {
      alert('Failed to delete account. Please try again.');
    } finally {
      setDeleting(false);
    }
  };

  const handleClearHistory = async () => {
    if (!confirm('Are you sure you want to delete all chat history?')) return;
    try {
      await historyApi.deleteAll();
      alert('Chat history cleared.');
    } catch {
      alert('Failed to clear history.');
    }
  };

  const themeOptions: { value: Theme; label: string; icon: React.ReactNode }[] = [
    { value: 'light', label: 'Light', icon: <HiSun className="w-5 h-5" /> },
    { value: 'dark', label: 'Dark', icon: <HiMoon className="w-5 h-5" /> },
    { value: 'system', label: 'System', icon: <HiDesktopComputer className="w-5 h-5" /> },
  ];

  const fontSizeOptions: { value: FontSize; label: string }[] = [
    { value: 'sm', label: 'Small' },
    { value: 'md', label: 'Medium' },
    { value: 'lg', label: 'Large' },
  ];

  return (
    <Layout>
      <div className="max-w-2xl mx-auto px-4 sm:px-6 py-8">
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
          <h1 className="font-display text-3xl font-bold text-slate-900 dark:text-white mb-8">Settings</h1>

          {/* Appearance */}
          <section className="glass-card p-6 mb-6">
            <h2 className="font-display font-semibold text-lg text-slate-800 dark:text-white mb-4">Appearance</h2>

            <div className="mb-6">
              <label className="block text-sm font-medium text-slate-600 dark:text-slate-400 mb-3">Theme</label>
              <div className="flex gap-2">
                {themeOptions.map((opt) => (
                  <button
                    key={opt.value}
                    onClick={() => setTheme(opt.value)}
                    className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium transition-colors ${
                      theme === opt.value
                        ? 'bg-primary text-white'
                        : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700'
                    }`}
                  >
                    {opt.icon}
                    {opt.label}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-600 dark:text-slate-400 mb-3">Font Size</label>
              <div className="flex gap-2">
                {fontSizeOptions.map((opt) => (
                  <button
                    key={opt.value}
                    onClick={() => setFontSize(opt.value)}
                    className={`px-4 py-2.5 rounded-xl text-sm font-medium transition-colors ${
                      fontSize === opt.value
                        ? 'bg-primary text-white'
                        : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300'
                    }`}
                  >
                    {opt.label}
                  </button>
                ))}
              </div>
            </div>

            <div className="mt-4 flex items-center gap-3">
              <span className="text-sm text-slate-500">Quick toggle:</span>
              <ThemeToggle />
            </div>
          </section>

          {/* Data */}
          <section className="glass-card p-6 mb-6">
            <h2 className="font-display font-semibold text-lg text-slate-800 dark:text-white mb-4">Data & Privacy</h2>
            <div className="space-y-3">
              <button
                onClick={handleExport}
                disabled={exporting}
                className="w-full flex items-center gap-3 px-4 py-3 rounded-xl bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors text-left"
              >
                <HiDownload className="w-5 h-5 text-primary" />
                <div>
                  <p className="font-medium text-slate-800 dark:text-white text-sm">
                    {exporting ? 'Exporting...' : 'Export Chat History'}
                  </p>
                  <p className="text-xs text-slate-500">Download all your conversations as JSON</p>
                </div>
              </button>
              <button
                onClick={handleClearHistory}
                className="w-full flex items-center gap-3 px-4 py-3 rounded-xl bg-slate-100 dark:bg-slate-800 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors text-left group"
              >
                <HiTrash className="w-5 h-5 text-slate-400 group-hover:text-red-500" />
                <div>
                  <p className="font-medium text-slate-800 dark:text-white text-sm group-hover:text-red-500">Clear Chat History</p>
                  <p className="text-xs text-slate-500">Permanently delete all conversations</p>
                </div>
              </button>
            </div>
          </section>

          {/* Danger zone */}
          <section className="glass-card p-6 border border-red-200 dark:border-red-900/50">
            <h2 className="font-display font-semibold text-lg text-red-600 mb-4">Danger Zone</h2>
            {!showDeleteConfirm ? (
              <button
                onClick={() => setShowDeleteConfirm(true)}
                className="px-4 py-2.5 rounded-xl bg-red-50 dark:bg-red-900/20 text-red-600 text-sm font-medium hover:bg-red-100 dark:hover:bg-red-900/40 transition-colors"
              >
                Delete Account
              </button>
            ) : (
              <div className="space-y-3">
                <p className="text-sm text-slate-600 dark:text-slate-400">
                  This will permanently delete your account and all data. This action cannot be undone.
                </p>
                <div className="flex gap-2">
                  <button
                    onClick={handleDeleteAccount}
                    disabled={deleting}
                    className="px-4 py-2.5 rounded-xl bg-red-600 text-white text-sm font-medium hover:bg-red-700 disabled:opacity-50"
                  >
                    {deleting ? 'Deleting...' : 'Yes, Delete My Account'}
                  </button>
                  <button
                    onClick={() => setShowDeleteConfirm(false)}
                    className="px-4 py-2.5 rounded-xl bg-slate-100 dark:bg-slate-800 text-sm font-medium"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            )}
          </section>
        </motion.div>
      </div>
    </Layout>
  );
}
