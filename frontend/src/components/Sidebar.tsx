import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import type { Conversation } from '@/types';
import {
  HiPlus,
  HiSearch,
  HiCog,
  HiTrash,
  HiChatAlt2,
  HiX,
} from 'react-icons/hi';
import { useState, useEffect } from 'react';
import { useDebounce } from '@/hooks/useLocalStorage';

interface SidebarProps {
  conversations: Conversation[];
  activeId?: string | number;
  onSelect: (id: number) => void;
  onNewChat: () => void;
  onDelete: (id: number) => void;
  onSearch?: (query: string) => void;
  isOpen: boolean;
  onClose: () => void;
}

function formatDate(iso: string) {
  try {
    return new Date(iso).toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
  } catch {
    return '';
  }
}

export default function Sidebar({
  conversations,
  activeId,
  onSelect,
  onNewChat,
  onDelete,
  onSearch,
  isOpen,
  onClose,
}: SidebarProps) {
  const [search, setSearch] = useState('');
  const debouncedSearch = useDebounce(search, 300);

  useEffect(() => {
    onSearch?.(debouncedSearch);
  }, [debouncedSearch, onSearch]);

  const sidebarContent = (
    <div className="flex flex-col h-full">
      <div className="p-4 space-y-3">
        <button
          onClick={() => { onNewChat(); onClose(); }}
          className="w-full flex items-center gap-2 px-4 py-3 rounded-xl bg-primary text-white font-medium hover:bg-primary-600 transition-colors"
        >
          <HiPlus className="w-5 h-5" />
          New Chat
        </button>

        <div className="relative">
          <HiSearch className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search conversations..."
            className="w-full pl-9 pr-4 py-2.5 rounded-xl bg-slate-100 dark:bg-slate-800 text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
          />
        </div>
      </div>

      <div className="flex-1 overflow-y-auto chat-scrollbar px-2 pb-2">
        {conversations.length === 0 ? (
          <p className="text-center text-sm text-slate-400 py-8">No conversations yet</p>
        ) : (
          conversations.map((conv) => (
            <div
              key={conv.id}
              className={`group flex items-center gap-2 px-3 py-2.5 rounded-xl cursor-pointer mb-1 transition-colors ${
                String(activeId) === String(conv.id)
                  ? 'bg-primary/10 text-primary'
                  : 'hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-600 dark:text-slate-300'
              }`}
              onClick={() => { onSelect(conv.id); onClose(); }}
            >
              <HiChatAlt2 className="w-4 h-4 flex-shrink-0" />
              <div className="flex-1 min-w-0">
                <span className="block text-sm truncate">{conv.title || 'New conversation'}</span>
                <span className="block text-[10px] text-slate-400 truncate">
                  {formatDate(conv.updated_at || conv.created_at)}
                  {conv.message_count != null ? ` · ${conv.message_count} msgs` : ''}
                </span>
              </div>
              <button
                onClick={(e) => { e.stopPropagation(); onDelete(conv.id); }}
                className="opacity-0 group-hover:opacity-100 p-1 rounded-lg hover:bg-red-100 hover:text-red-500 dark:hover:bg-red-900/30 transition-all"
              >
                <HiTrash className="w-3.5 h-3.5" />
              </button>
            </div>
          ))
        )}
      </div>

      <div className="p-4 border-t border-slate-200 dark:border-slate-700">
        <Link
          to="/settings"
          className="flex items-center gap-2 px-3 py-2.5 rounded-xl text-sm text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
        >
          <HiCog className="w-4 h-4" />
          Settings
        </Link>
      </div>
    </div>
  );

  return (
    <>
      <aside className="hidden md:flex flex-col w-72 border-r border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900">
        {sidebarContent}
      </aside>

      {isOpen && (
        <div className="md:hidden fixed inset-0 z-40">
          <div className="absolute inset-0 bg-black/50" onClick={onClose} />
          <motion.aside
            initial={{ x: -300 }}
            animate={{ x: 0 }}
            exit={{ x: -300 }}
            className="absolute left-0 top-0 bottom-0 w-72 bg-white dark:bg-slate-900 shadow-xl"
          >
            <button
              onClick={onClose}
              className="absolute top-4 right-4 p-2 rounded-xl hover:bg-slate-100 dark:hover:bg-slate-800"
            >
              <HiX className="w-5 h-5" />
            </button>
            {sidebarContent}
          </motion.aside>
        </div>
      )}
    </>
  );
}
