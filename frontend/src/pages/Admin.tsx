import { useEffect, useState, useRef } from 'react';
import { motion } from 'framer-motion';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js';
import { Line, Bar, Doughnut } from 'react-chartjs-2';
import Layout from '@/components/Layout';
import StatCard from '@/components/StatCard';
import LoadingSkeleton from '@/components/LoadingSkeleton';
import { adminApi } from '@/services/api';
import type { AdminStats, AdminLog, User } from '@/types';
import {
  HiUsers,
  HiChatAlt2,
  HiTrendingUp,
  HiDocumentText,
  HiUpload,
  HiExclamation,
} from 'react-icons/hi';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

interface AnalyticsData {
  messages_per_day?: Array<{ date: string; count: number }>;
  categories?: Array<{ name: string; count: number }>;
}

const DEFAULT_STATS: AdminStats = {
  total_users: 128,
  total_chats: 1543,
  total_messages: 8420,
  total_documents: 320,
  emergency_flags: 12,
  active_users_today: 42,
};

export default function Admin() {
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [users, setUsers] = useState<User[]>([]);
  const [logs, setLogs] = useState<AdminLog[]>([]);
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'overview' | 'users' | 'logs'>('overview');
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [statsRes, usersRes, logsRes, analyticsRes] = await Promise.allSettled([
          adminApi.stats(),
          adminApi.users(),
          adminApi.logs(),
          adminApi.analytics(),
        ]);
        if (statsRes.status === 'fulfilled') setStats(statsRes.value.data);
        if (usersRes.status === 'fulfilled') setUsers(usersRes.value.data);
        if (logsRes.status === 'fulfilled') setLogs(logsRes.value.data);
        if (analyticsRes.status === 'fulfilled') setAnalytics(analyticsRes.value.data as AnalyticsData);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const displayStats = stats || DEFAULT_STATS;

  const messagesPerDay = analytics?.messages_per_day;
  const lineData = {
    labels: messagesPerDay?.map((d) => d.date) ?? ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
    datasets: [
      {
        label: 'Messages',
        data: messagesPerDay?.map((d) => d.count) ?? [120, 190, 150, 220, 180, 250, 210],
        borderColor: '#2563EB',
        backgroundColor: 'rgba(37, 99, 235, 0.1)',
        fill: true,
        tension: 0.4,
      },
    ],
  };

  const categoryData = analytics?.categories;
  const barData = {
    labels: categoryData?.map((c) => c.name) ?? ['General', 'Nutrition', 'Mental Health', 'Fitness', 'Medications', 'First Aid'],
    datasets: [
      {
        label: 'Queries by Category',
        data: categoryData?.map((c) => c.count) ?? [320, 250, 180, 210, 150, 90],
        backgroundColor: [
          'rgba(37, 99, 235, 0.8)',
          'rgba(14, 165, 233, 0.8)',
          'rgba(34, 197, 94, 0.8)',
          'rgba(37, 99, 235, 0.6)',
          'rgba(14, 165, 233, 0.6)',
          'rgba(34, 197, 94, 0.6)',
        ],
        borderRadius: 8,
      },
    ],
  };

  const doughnutData = {
    labels: ['Active Today', 'Total Users', 'Emergency Flags'],
    datasets: [
      {
        data: [
          displayStats.active_users_today,
          Math.max(displayStats.total_users - displayStats.active_users_today, 0),
          displayStats.emergency_flags,
        ],
        backgroundColor: ['#2563EB', '#94A3B8', '#EF4444'],
        borderWidth: 0,
      },
    ],
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { position: 'bottom' as const } },
    scales: {
      y: { beginAtZero: true, grid: { color: 'rgba(148, 163, 184, 0.1)' } },
      x: { grid: { display: false } },
    },
  };

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    try {
      await adminApi.uploadDataset(file);
      alert('Dataset uploaded successfully');
    } catch {
      alert('Failed to upload dataset');
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const levelColor = (level: string) => {
    switch (level.toLowerCase()) {
      case 'error':
        return 'text-red-500';
      case 'warning':
        return 'text-yellow-600';
      case 'info':
        return 'text-primary';
      default:
        return 'text-slate-500';
    }
  };

  if (loading) {
    return (
      <Layout>
        <div className="max-w-7xl mx-auto px-4 py-8">
          <LoadingSkeleton variant="card" count={4} />
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
          <h1 className="font-display text-3xl font-bold text-slate-900 dark:text-white mb-2">Admin Dashboard</h1>
          <p className="text-slate-500 mb-8">Monitor platform activity and manage users</p>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4 mb-8">
            <StatCard title="Total Users" value={displayStats.total_users} icon={<HiUsers className="w-6 h-6" />} color="primary" />
            <StatCard title="Total Chats" value={displayStats.total_chats} icon={<HiChatAlt2 className="w-6 h-6" />} color="secondary" />
            <StatCard title="Total Messages" value={displayStats.total_messages} icon={<HiDocumentText className="w-6 h-6" />} color="primary" />
            <StatCard title="Documents" value={displayStats.total_documents} icon={<HiDocumentText className="w-6 h-6" />} color="accent" />
            <StatCard title="Active Today" value={displayStats.active_users_today} icon={<HiTrendingUp className="w-6 h-6" />} color="accent" />
            <StatCard title="Emergency Flags" value={displayStats.emergency_flags} icon={<HiExclamation className="w-6 h-6" />} color="primary" />
          </div>

          <div className="flex gap-2 mb-6">
            {(['overview', 'users', 'logs'] as const).map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-4 py-2 rounded-xl text-sm font-medium capitalize transition-colors ${
                  activeTab === tab
                    ? 'bg-primary text-white'
                    : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300'
                }`}
              >
                {tab}
              </button>
            ))}
          </div>

          {activeTab === 'overview' && (
            <div className="space-y-6">
              <div className="grid lg:grid-cols-2 gap-6">
                <div className="glass-card p-6">
                  <h3 className="font-display font-semibold text-lg mb-4 text-slate-800 dark:text-white">
                    Messages per Day
                  </h3>
                  <div className="h-64">
                    <Line data={lineData} options={chartOptions} />
                  </div>
                </div>
                <div className="glass-card p-6">
                  <h3 className="font-display font-semibold text-lg mb-4 text-slate-800 dark:text-white">Overview</h3>
                  <div className="h-64 flex items-center justify-center">
                    <div className="w-48 h-48">
                      <Doughnut
                        data={doughnutData}
                        options={{ responsive: true, maintainAspectRatio: true, plugins: { legend: { position: 'bottom' } } }}
                      />
                    </div>
                  </div>
                </div>
              </div>

              <div className="glass-card p-6">
                <h3 className="font-display font-semibold text-lg mb-4 text-slate-800 dark:text-white">Queries by Category</h3>
                <div className="h-64">
                  <Bar data={barData} options={chartOptions} />
                </div>
              </div>

              <div className="glass-card p-6 border border-dashed border-primary/30">
                <div className="flex items-start gap-4">
                  <div className="p-3 rounded-xl bg-primary/10">
                    <HiUpload className="w-6 h-6 text-primary" />
                  </div>
                  <div>
                    <h3 className="font-display font-semibold text-lg text-slate-800 dark:text-white mb-1">
                      Medical Dataset Upload
                    </h3>
                    <p className="text-sm text-slate-500 mb-3">
                      Upload medical knowledge datasets (JSON, CSV, PDF) to improve AI response accuracy.
                    </p>
                    <input ref={fileInputRef} type="file" className="hidden" accept=".json,.csv,.pdf,.txt" onChange={handleUpload} />
                    <button
                      onClick={() => fileInputRef.current?.click()}
                      disabled={uploading}
                      className="btn-secondary text-sm py-2 px-4 disabled:opacity-50"
                    >
                      {uploading ? 'Uploading...' : 'Upload Dataset'}
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'users' && (
            <div className="glass-card overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-slate-200 dark:border-slate-700">
                      <th className="text-left p-4 font-medium text-slate-500">Name</th>
                      <th className="text-left p-4 font-medium text-slate-500">Email</th>
                      <th className="text-left p-4 font-medium text-slate-500">Role</th>
                      <th className="text-left p-4 font-medium text-slate-500">Joined</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(users.length > 0 ? users : DEMO_USERS).map((u) => (
                      <tr key={u.id} className="border-b border-slate-100 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800/50">
                        <td className="p-4 font-medium text-slate-800 dark:text-white">{u.name}</td>
                        <td className="p-4 text-slate-500">{u.email}</td>
                        <td className="p-4">
                          <span className="px-2 py-0.5 rounded-full bg-primary/10 text-primary text-xs">
                            {u.is_admin ? 'Admin' : 'User'}
                          </span>
                        </td>
                        <td className="p-4 text-slate-500">{new Date(u.created_at).toLocaleDateString()}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {activeTab === 'logs' && (
            <div className="glass-card p-6">
              <h3 className="font-display font-semibold text-lg mb-4 text-slate-800 dark:text-white">System Logs</h3>
              <div className="space-y-2 max-h-96 overflow-y-auto chat-scrollbar">
                {(logs.length > 0 ? logs : DEMO_LOGS).map((log) => (
                  <div key={log.id} className="flex items-start gap-3 p-3 rounded-xl bg-slate-50 dark:bg-slate-800/50 text-sm">
                    <span className="text-xs text-slate-400 whitespace-nowrap mt-0.5">
                      {new Date(log.created_at).toLocaleString()}
                    </span>
                    <span className={`font-medium uppercase text-xs ${levelColor(log.level)}`}>{log.level}</span>
                    <span className="text-slate-600 dark:text-slate-300 flex-1">{log.message}</span>
                    {log.user_id != null && (
                      <span className="text-xs text-slate-400">User #{log.user_id}</span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </motion.div>
      </div>
    </Layout>
  );
}

const DEMO_USERS: User[] = [
  { id: 1, name: 'Rahul Mehta', email: 'rahul@example.com', is_admin: false, theme: 'system', font_size: 'medium', created_at: '2025-06-15T00:00:00Z' },
  { id: 2, name: 'Priya Sharma', email: 'priya@example.com', is_admin: false, theme: 'light', font_size: 'medium', created_at: '2025-07-01T00:00:00Z' },
  { id: 3, name: 'Admin User', email: 'admin@aarogya.ai', is_admin: true, theme: 'dark', font_size: 'medium', created_at: '2025-01-01T00:00:00Z' },
];

const DEMO_LOGS: AdminLog[] = [
  { id: 1, level: 'info', message: 'User rahul@example.com logged in', user_id: 1, created_at: new Date().toISOString() },
  { id: 2, level: 'info', message: 'New chat session started', user_id: 1, created_at: new Date(Date.now() - 3600000).toISOString() },
  { id: 3, level: 'warning', message: 'Emergency flag triggered in chat #42', user_id: 2, created_at: new Date(Date.now() - 7200000).toISOString() },
  { id: 4, level: 'info', message: 'Dataset v2.1 uploaded', created_at: new Date(Date.now() - 86400000).toISOString() },
];
