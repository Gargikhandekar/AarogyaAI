import { motion } from 'framer-motion';
import { ReactNode } from 'react';

interface StatCardProps {
  title: string;
  value: string | number;
  icon: ReactNode;
  trend?: string;
  color?: 'primary' | 'secondary' | 'accent';
}

const colorMap = {
  primary: 'from-primary/10 to-primary/5 text-primary',
  secondary: 'from-secondary/10 to-secondary/5 text-secondary',
  accent: 'from-accent/10 to-accent/5 text-accent-600',
};

export default function StatCard({ title, value, icon, trend, color = 'primary' }: StatCardProps) {
  return (
    <motion.div
      whileHover={{ y: -2 }}
      className="glass-card p-6"
    >
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-slate-500 dark:text-slate-400 mb-1">{title}</p>
          <p className="text-3xl font-display font-bold text-slate-800 dark:text-white">{value}</p>
          {trend && (
            <p className="text-xs text-accent-600 mt-1">{trend}</p>
          )}
        </div>
        <div className={`p-3 rounded-xl bg-gradient-to-br ${colorMap[color]}`}>
          {icon}
        </div>
      </div>
    </motion.div>
  );
}
