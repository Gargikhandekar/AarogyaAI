import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import Layout from '@/components/Layout';
import StatCard from '@/components/StatCard';
import BMIWidget from '@/components/BMIWidget';
import LoadingSkeleton from '@/components/LoadingSkeleton';
import { useAuth } from '@/context/AuthContext';
import { contentApi, profileApi } from '@/services/api';
import type { HealthTip, NewsItem, ProfileStats } from '@/types';
import {
  HiChatAlt2,
  HiDocumentText,
  HiClock,
  HiLightBulb,
  HiArrowRight,
  HiNewspaper,
  HiHeart,
} from 'react-icons/hi';

const CATEGORY_ICONS: Record<string, string> = {
  'General Health': '🏥',
  Nutrition: '🥗',
  'Mental Health': '🧠',
  Fitness: '💪',
  Medications: '💊',
  'First Aid': '🩹',
};

const DEFAULT_CATEGORIES = [
  'General Health',
  'Nutrition',
  'Mental Health',
  'Fitness',
  'Medications',
  'First Aid',
];

const DEFAULT_SUGGESTIONS = [
  'What are the symptoms of diabetes?',
  'How can I improve my sleep quality?',
  'What foods are good for heart health?',
  'How much water should I drink daily?',
  'What exercises help with back pain?',
  'When should I see a doctor for a fever?',
];

const DEFAULT_NEWS: NewsItem[] = [
  {
    title: 'New Study Links Regular Exercise to Improved Mental Health',
    summary: 'Researchers find 30 minutes of daily activity significantly reduces anxiety and depression symptoms.',
    tag: 'Research',
  },
  {
    title: 'WHO Updates Global Nutrition Guidelines',
    summary: 'Updated recommendations emphasize plant-based diets and reduced processed food consumption.',
    tag: 'Nutrition',
  },
  {
    title: 'Breakthrough in Early Cancer Detection Technology',
    summary: 'New blood test can detect multiple cancer types at early stages with high accuracy.',
    tag: 'Innovation',
  },
];

export default function Dashboard() {
  const { user } = useAuth();
  const [tip, setTip] = useState<HealthTip | null>(null);
  const [news, setNews] = useState<NewsItem[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [stats, setStats] = useState<ProfileStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [tipRes, newsRes, catRes, sugRes, statsRes] = await Promise.allSettled([
          contentApi.healthTip(),
          contentApi.news(),
          contentApi.categories(),
          contentApi.suggestions(),
          profileApi.stats(),
        ]);

        if (tipRes.status === 'fulfilled') setTip(tipRes.value.data);
        if (newsRes.status === 'fulfilled') setNews(newsRes.value.data.articles.slice(0, 3));
        if (catRes.status === 'fulfilled') setCategories(catRes.value.data.categories);
        if (sugRes.status === 'fulfilled') setSuggestions(sugRes.value.data.suggestions.slice(0, 6));
        if (statsRes.status === 'fulfilled') setStats(statsRes.value.data);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const displayCategories = categories.length > 0 ? categories : DEFAULT_CATEGORIES;
  const displaySuggestions = suggestions.length > 0 ? suggestions : DEFAULT_SUGGESTIONS;
  const displayNews = news.length > 0 ? news : DEFAULT_NEWS;

  const avgPerChat =
    stats && stats.total_chats > 0
      ? (stats.total_messages / stats.total_chats).toFixed(1)
      : '0';

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
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="mb-8">
          <h1 className="font-display text-3xl font-bold text-slate-900 dark:text-white">
            Good {getGreeting()}, {user?.name?.split(' ')[0]} 👋
          </h1>
          <p className="text-slate-500 mt-1">Here's your health overview for today</p>
        </motion.div>

        {tip && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="glass-card p-6 mb-8 bg-gradient-to-r from-accent/5 to-primary/5 border border-accent/20"
          >
            <div className="flex items-start gap-4">
              <div className="p-3 rounded-xl bg-accent/10">
                <HiLightBulb className="w-6 h-6 text-accent-600" />
              </div>
              <div>
                <h3 className="font-display font-semibold text-lg text-slate-800 dark:text-white mb-1">
                  Tip of the Day
                  {tip.category && (
                    <span className="ml-2 text-xs font-normal text-slate-400">· {tip.category}</span>
                  )}
                </h3>
                <p className="text-slate-600 dark:text-slate-300">{tip.tip}</p>
              </div>
            </div>
          </motion.div>
        )}

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <StatCard
            title="Total Chats"
            value={stats?.total_chats ?? 0}
            icon={<HiChatAlt2 className="w-6 h-6" />}
            color="primary"
          />
          <StatCard
            title="Messages"
            value={stats?.total_messages ?? 0}
            icon={<HiDocumentText className="w-6 h-6" />}
            color="secondary"
          />
          <StatCard
            title="Avg. per Chat"
            value={avgPerChat}
            icon={<HiClock className="w-6 h-6" />}
            color="accent"
          />
          <StatCard
            title="Favorites"
            value={stats?.favorite_count ?? 0}
            icon={<HiHeart className="w-6 h-6" />}
            color="primary"
          />
        </div>

        <div className="grid lg:grid-cols-3 gap-8">
          <div className="lg:col-span-2 space-y-8">
            <section>
              <h2 className="font-display text-xl font-semibold text-slate-800 dark:text-white mb-4">
                Health Categories
              </h2>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                {displayCategories.map((cat) => (
                  <Link
                    key={cat}
                    to={`/chat?category=${encodeURIComponent(cat)}`}
                    className="glass-card p-4 hover:shadow-card transition-all hover:-translate-y-0.5 text-center"
                  >
                    <span className="text-2xl mb-2 block">{CATEGORY_ICONS[cat] || '🏥'}</span>
                    <p className="text-sm font-medium text-slate-700 dark:text-slate-200">{cat}</p>
                  </Link>
                ))}
              </div>
            </section>

            <section>
              <div className="flex items-center justify-between mb-4">
                <h2 className="font-display text-xl font-semibold text-slate-800 dark:text-white">
                  Suggested Questions
                </h2>
                <Link to="/chat" className="text-primary text-sm font-medium flex items-center gap-1 hover:underline">
                  Start Chat <HiArrowRight className="w-4 h-4" />
                </Link>
              </div>
              <div className="grid sm:grid-cols-2 gap-3">
                {displaySuggestions.map((text) => (
                  <Link
                    key={text}
                    to={`/chat?q=${encodeURIComponent(text)}`}
                    className="glass-card p-4 text-sm text-slate-600 dark:text-slate-300 hover:text-primary hover:border-primary/30 transition-colors"
                  >
                    {text}
                  </Link>
                ))}
              </div>
            </section>

            <section>
              <h2 className="font-display text-xl font-semibold text-slate-800 dark:text-white mb-4 flex items-center gap-2">
                <HiNewspaper className="w-5 h-5 text-primary" />
                Health News
              </h2>
              <div className="space-y-3">
                {displayNews.map((item, i) => (
                  <div key={`${item.title}-${i}`} className="glass-card p-4">
                    <div className="flex items-start justify-between gap-2">
                      <h4 className="font-medium text-slate-800 dark:text-white mb-1">{item.title}</h4>
                      {item.tag && (
                        <span className="flex-shrink-0 px-2 py-0.5 rounded-full bg-primary/10 text-primary text-xs">
                          {item.tag}
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-slate-500 line-clamp-2">{item.summary}</p>
                  </div>
                ))}
              </div>
            </section>
          </div>

          <div className="space-y-6">
            <BMIWidget />
            <Link to="/chat" className="block glass-card p-6 text-center hover:shadow-card transition-shadow">
              <HiChatAlt2 className="w-10 h-10 text-primary mx-auto mb-3" />
              <h3 className="font-display font-semibold text-lg mb-1">Start a Chat</h3>
              <p className="text-sm text-slate-500">Ask anything about your health</p>
            </Link>
            <Link to="/tools" className="block glass-card p-6 text-center hover:shadow-card transition-shadow">
              <span className="text-3xl mb-3 block">🛠️</span>
              <h3 className="font-display font-semibold text-lg mb-1">Health Tools</h3>
              <p className="text-sm text-slate-500">BMI, symptoms, reminders & more</p>
            </Link>
          </div>
        </div>
      </div>
    </Layout>
  );
}

function getGreeting() {
  const hour = new Date().getHours();
  if (hour < 12) return 'morning';
  if (hour < 17) return 'afternoon';
  return 'evening';
}
