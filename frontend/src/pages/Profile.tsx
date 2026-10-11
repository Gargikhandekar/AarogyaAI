import { useState, useEffect, FormEvent } from 'react';
import { motion } from 'framer-motion';
import Layout from '@/components/Layout';
import LoadingSkeleton from '@/components/LoadingSkeleton';
import { useAuth } from '@/context/AuthContext';
import { profileApi } from '@/services/api';
import type { ProfileStats } from '@/types';
import { HiCamera, HiSave, HiLockClosed } from 'react-icons/hi';

export default function Profile() {
  const { user, updateUser } = useAuth();
  const [name, setName] = useState(user?.name || '');
  const [email, setEmail] = useState(user?.email || '');
  const [stats, setStats] = useState<ProfileStats | null>(null);
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    profileApi.stats()
      .then(({ data }) => setStats(data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const handleProfileSave = async (e: FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError('');
    setMessage('');
    try {
      const { data } = await profileApi.update({ name, email });
      updateUser(data);
      setMessage('Profile updated successfully');
    } catch {
      setError('Failed to update profile');
    } finally {
      setSaving(false);
    }
  };

  const handlePasswordChange = async (e: FormEvent) => {
    e.preventDefault();
    if (newPassword.length < 6) {
      setError('New password must be at least 6 characters');
      return;
    }
    setSaving(true);
    setError('');
    setMessage('');
    try {
      await profileApi.update({
        current_password: currentPassword,
        new_password: newPassword,
      });
      setMessage('Password changed successfully');
      setCurrentPassword('');
      setNewPassword('');
    } catch {
      setError('Failed to change password. Check your current password.');
    } finally {
      setSaving(false);
    }
  };

  const avgPerChat =
    stats && stats.total_chats > 0
      ? (stats.total_messages / stats.total_chats).toFixed(1)
      : '0';

  if (loading) {
    return (
      <Layout>
        <div className="max-w-3xl mx-auto px-4 py-8">
          <LoadingSkeleton variant="page" />
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="max-w-3xl mx-auto px-4 sm:px-6 py-8">
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
          <h1 className="font-display text-3xl font-bold text-slate-900 dark:text-white mb-8">Profile</h1>

          <div className="glass-card p-8 mb-6 text-center">
            <div className="relative inline-block mb-4">
              {user?.photo_url ? (
                <img
                  src={user.photo_url}
                  alt={user.name}
                  className="w-24 h-24 rounded-2xl object-cover"
                />
              ) : (
                <div className="w-24 h-24 rounded-2xl bg-hero-gradient flex items-center justify-center text-white text-3xl font-display font-bold">
                  {user?.name?.charAt(0).toUpperCase()}
                </div>
              )}
              <button className="absolute -bottom-1 -right-1 p-2 rounded-xl bg-white dark:bg-slate-800 shadow-md text-slate-500 hover:text-primary transition-colors">
                <HiCamera className="w-4 h-4" />
              </button>
            </div>
            <h2 className="font-display text-xl font-semibold text-slate-800 dark:text-white">{user?.name}</h2>
            <p className="text-slate-500">{user?.email}</p>
            <span className="inline-block mt-2 px-3 py-1 rounded-full bg-primary/10 text-primary text-xs font-medium capitalize">
              {user?.is_admin ? 'Admin' : 'User'}
            </span>
          </div>

          {stats && (
            <div className="grid grid-cols-3 gap-4 mb-6">
              {[
                { label: 'Total Chats', value: stats.total_chats },
                { label: 'Messages', value: stats.total_messages },
                { label: 'Avg/Chat', value: avgPerChat },
              ].map((s) => (
                <div key={s.label} className="glass-card p-4 text-center">
                  <p className="text-2xl font-display font-bold text-primary">{s.value}</p>
                  <p className="text-xs text-slate-500 mt-1">{s.label}</p>
                </div>
              ))}
            </div>
          )}

          {message && (
            <div className="mb-4 p-3 rounded-xl bg-accent/10 text-accent-600 text-sm">{message}</div>
          )}
          {error && (
            <div className="mb-4 p-3 rounded-xl bg-red-50 dark:bg-red-900/20 text-red-600 text-sm">{error}</div>
          )}

          <form onSubmit={handleProfileSave} className="glass-card p-6 mb-6 space-y-4">
            <h3 className="font-display font-semibold text-lg text-slate-800 dark:text-white">Edit Profile</h3>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">Name</label>
              <input type="text" value={name} onChange={(e) => setName(e.target.value)} className="input-field" />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">Email</label>
              <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} className="input-field" />
            </div>
            <button type="submit" disabled={saving} className="btn-primary text-sm py-2 px-4">
              <HiSave className="w-4 h-4" /> {saving ? 'Saving...' : 'Save Changes'}
            </button>
          </form>

          <form onSubmit={handlePasswordChange} className="glass-card p-6 space-y-4">
            <h3 className="font-display font-semibold text-lg text-slate-800 dark:text-white flex items-center gap-2">
              <HiLockClosed className="w-5 h-5" /> Change Password
            </h3>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">Current Password</label>
              <input
                type="password"
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                className="input-field"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">New Password</label>
              <input
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                className="input-field"
                minLength={6}
                required
              />
            </div>
            <button type="submit" disabled={saving} className="btn-secondary text-sm py-2 px-4">
              {saving ? 'Updating...' : 'Update Password'}
            </button>
          </form>
        </motion.div>
      </div>
    </Layout>
  );
}
