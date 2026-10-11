import { motion } from 'framer-motion';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import ThemeToggle from './ThemeToggle';
import {
  HiMenu,
  HiX,
  HiChatAlt2,
  HiViewGrid,
  HiUser,
  HiCog,
  HiShieldCheck,
  HiLogout,
} from 'react-icons/hi';
import { useState } from 'react';

interface NavbarProps {
  transparent?: boolean;
}

export default function Navbar({ transparent = false }: NavbarProps) {
  const { isAuthenticated, user, logout } = useAuth();
  const location = useLocation();
  const [mobileOpen, setMobileOpen] = useState(false);

  const navLinks = isAuthenticated
    ? [
        { to: '/dashboard', label: 'Dashboard', icon: HiViewGrid },
        { to: '/chat', label: 'Chat', icon: HiChatAlt2 },
        { to: '/tools', label: 'Tools', icon: HiShieldCheck },
        ...(user?.is_admin ? [{ to: '/admin', label: 'Admin', icon: HiShieldCheck }] : []),
      ]
    : [];

  const isActive = (path: string) => location.pathname === path;

  return (
    <nav
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
        transparent && !mobileOpen
          ? 'bg-transparent'
          : 'glass border-b border-white/10 dark:border-slate-700/50'
      }`}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <Link to="/" className="flex items-center gap-2 group">
            <div className="w-9 h-9 rounded-xl bg-hero-gradient flex items-center justify-center shadow-glow">
              <span className="text-white font-display font-bold text-lg">A</span>
            </div>
            <span className="font-display font-bold text-xl text-slate-800 dark:text-white group-hover:text-primary transition-colors">
              Aarogya AI
            </span>
          </Link>

          {/* Desktop nav */}
          <div className="hidden md:flex items-center gap-1">
            {navLinks.map(({ to, label, icon: Icon }) => (
              <Link
                key={to}
                to={to}
                className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition-colors ${
                  isActive(to)
                    ? 'bg-primary/10 text-primary'
                    : 'text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800'
                }`}
              >
                <Icon className="w-4 h-4" />
                {label}
              </Link>
            ))}
          </div>

          <div className="flex items-center gap-2">
            <ThemeToggle />
            {isAuthenticated ? (
              <div className="hidden md:flex items-center gap-2">
                <Link
                  to="/profile"
                  className="flex items-center gap-2 px-3 py-2 rounded-xl hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
                >
                  <div className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center text-primary font-semibold text-sm">
                    {user?.name?.charAt(0).toUpperCase()}
                  </div>
                  <span className="text-sm font-medium hidden lg:block">{user?.name}</span>
                </Link>
                <Link
                  to="/settings"
                  className="p-2 rounded-xl hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
                >
                  <HiCog className="w-5 h-5 text-slate-500" />
                </Link>
                <button
                  onClick={logout}
                  className="p-2 rounded-xl hover:bg-red-50 dark:hover:bg-red-900/20 text-slate-500 hover:text-red-500 transition-colors"
                >
                  <HiLogout className="w-5 h-5" />
                </button>
              </div>
            ) : (
              <div className="hidden md:flex items-center gap-2">
                <Link to="/login" className="btn-secondary text-sm py-2 px-4">
                  Sign In
                </Link>
                <Link to="/register" className="btn-primary text-sm py-2 px-4">
                  Get Started
                </Link>
              </div>
            )}
            <button
              className="md:hidden p-2 rounded-xl hover:bg-slate-100 dark:hover:bg-slate-800"
              onClick={() => setMobileOpen(!mobileOpen)}
            >
              {mobileOpen ? <HiX className="w-6 h-6" /> : <HiMenu className="w-6 h-6" />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile menu */}
      {mobileOpen && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="md:hidden glass border-t border-white/10 dark:border-slate-700/50 px-4 py-4 space-y-2"
        >
          {navLinks.map(({ to, label, icon: Icon }) => (
            <Link
              key={to}
              to={to}
              onClick={() => setMobileOpen(false)}
              className={`flex items-center gap-3 px-4 py-3 rounded-xl ${
                isActive(to) ? 'bg-primary/10 text-primary' : 'text-slate-600 dark:text-slate-300'
              }`}
            >
              <Icon className="w-5 h-5" />
              {label}
            </Link>
          ))}
          {isAuthenticated ? (
            <>
              <Link
                to="/profile"
                onClick={() => setMobileOpen(false)}
                className="flex items-center gap-3 px-4 py-3 rounded-xl text-slate-600 dark:text-slate-300"
              >
                <HiUser className="w-5 h-5" /> Profile
              </Link>
              <Link
                to="/settings"
                onClick={() => setMobileOpen(false)}
                className="flex items-center gap-3 px-4 py-3 rounded-xl text-slate-600 dark:text-slate-300"
              >
                <HiCog className="w-5 h-5" /> Settings
              </Link>
              <button
                onClick={() => { logout(); setMobileOpen(false); }}
                className="flex items-center gap-3 px-4 py-3 rounded-xl text-red-500 w-full"
              >
                <HiLogout className="w-5 h-5" /> Sign Out
              </button>
            </>
          ) : (
            <div className="flex flex-col gap-2 pt-2">
              <Link to="/login" onClick={() => setMobileOpen(false)} className="btn-secondary text-center">
                Sign In
              </Link>
              <Link to="/register" onClick={() => setMobileOpen(false)} className="btn-primary text-center">
                Get Started
              </Link>
            </div>
          )}
        </motion.div>
      )}
    </nav>
  );
}
