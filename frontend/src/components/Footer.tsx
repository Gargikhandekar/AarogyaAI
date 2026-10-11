import { Link } from 'react-router-dom';
import { HiHeart } from 'react-icons/hi';

export default function Footer() {
  return (
    <footer className="bg-slate-900 text-slate-300 py-12">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-8">
          <div className="md:col-span-2">
            <div className="flex items-center gap-2 mb-4">
              <div className="w-8 h-8 rounded-lg bg-hero-gradient flex items-center justify-center">
                <span className="text-white font-display font-bold">A</span>
              </div>
              <span className="font-display font-bold text-xl text-white">Aarogya AI</span>
            </div>
            <p className="text-slate-400 text-sm leading-relaxed max-w-sm">
              Your intelligent medical companion. Get health guidance, symptom insights, and wellness tips powered by AI.
            </p>
          </div>
          <div>
            <h4 className="font-semibold text-white mb-4">Product</h4>
            <ul className="space-y-2 text-sm">
              <li><Link to="/chat" className="hover:text-white transition-colors">Chat</Link></li>
              <li><Link to="/tools" className="hover:text-white transition-colors">Health Tools</Link></li>
              <li><Link to="/dashboard" className="hover:text-white transition-colors">Dashboard</Link></li>
            </ul>
          </div>
          <div>
            <h4 className="font-semibold text-white mb-4">Legal</h4>
            <ul className="space-y-2 text-sm">
              <li><span className="text-slate-400">Privacy Policy</span></li>
              <li><span className="text-slate-400">Terms of Service</span></li>
              <li><span className="text-slate-400">Medical Disclaimer</span></li>
            </ul>
          </div>
        </div>
        <div className="border-t border-slate-800 pt-8 flex flex-col sm:flex-row items-center justify-between gap-4">
          <p className="text-sm text-slate-500">
            © {new Date().getFullYear()} Aarogya AI. All rights reserved.
          </p>
          <p className="text-xs text-slate-500 flex items-center gap-1">
            Made with <HiHeart className="text-red-400 w-3 h-3" /> for better health
          </p>
        </div>
        <p className="text-xs text-slate-600 mt-4 text-center max-w-2xl mx-auto">
          ⚕️ Medical Disclaimer: Aarogya AI is not a substitute for professional medical advice, diagnosis, or treatment. Always seek the advice of your physician or qualified health provider.
        </p>
      </div>
    </footer>
  );
}
