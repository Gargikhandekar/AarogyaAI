import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import Layout from '@/components/Layout';
import Footer from '@/components/Footer';
import HeroIllustration from '@/components/HeroIllustration';
import {
  HiChatAlt2,
  HiShieldCheck,
  HiLightningBolt,
  HiHeart,
  HiChevronDown,
} from 'react-icons/hi';
import { useState } from 'react';

const features = [
  {
    icon: HiChatAlt2,
    title: 'Intelligent Chat',
    description: 'Ask health questions and get AI-powered responses with medical source references and confidence scores.',
  },
  {
    icon: HiShieldCheck,
    title: 'Symptom Checker',
    description: 'Describe your symptoms and receive guided insights on possible conditions and recommended next steps.',
  },
  {
    icon: HiLightningBolt,
    title: 'Instant Answers',
    description: 'Get fast, evidence-based health information available 24/7 whenever you need guidance.',
  },
  {
    icon: HiHeart,
    title: 'Wellness Tracking',
    description: 'Monitor BMI, set medication reminders, and stay on top of your daily health goals.',
  },
];

const testimonials = [
  {
    name: 'Dr. Priya Sharma',
    role: 'General Physician',
    text: 'Aarogya AI helps my patients get preliminary health information between appointments. A valuable companion tool.',
    avatar: 'P',
  },
  {
    name: 'Rahul Mehta',
    role: 'Patient',
    text: 'The symptom checker gave me clarity when I was unsure about my fever. Easy to use and very informative.',
    avatar: 'R',
  },
  {
    name: 'Ananya Patel',
    role: 'Wellness Enthusiast',
    text: 'Love the daily health tips and BMI tracker. It keeps me motivated to maintain a healthy lifestyle.',
    avatar: 'A',
  },
];

const faqs = [
  {
    q: 'Is Aarogya AI a replacement for a doctor?',
    a: 'No. Aarogya AI provides general health information and guidance. It is not a substitute for professional medical advice, diagnosis, or treatment. Always consult a qualified healthcare provider.',
  },
  {
    q: 'How accurate is the AI?',
    a: 'Our AI is trained on medical literature and provides confidence scores with each response. However, AI can make mistakes. Use responses as informational starting points, not definitive diagnoses.',
  },
  {
    q: 'Is my health data secure?',
    a: 'Yes. We use industry-standard encryption and never share your personal health conversations with third parties without your consent.',
  },
  {
    q: 'Can I use voice input?',
    a: 'Yes! Our chat supports voice input via Web Speech API for hands-free health queries, plus text-to-speech to hear responses aloud.',
  },
];

export default function Landing() {
  const [openFaq, setOpenFaq] = useState<number | null>(null);

  return (
    <Layout transparentNav>
      {/* Hero */}
      <section className="relative min-h-screen flex items-center overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-background to-secondary/5 dark:from-primary/10 dark:via-dark dark:to-secondary/10" />
        <div className="absolute top-20 left-10 w-72 h-72 bg-primary/10 rounded-full blur-3xl" />
        <div className="absolute bottom-20 right-10 w-96 h-96 bg-secondary/10 rounded-full blur-3xl" />

        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-24 grid lg:grid-cols-2 gap-12 items-center">
          <motion.div
            initial={{ opacity: 0, x: -30 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.7 }}
          >
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full glass text-sm font-medium text-primary mb-6">
              <span className="w-2 h-2 rounded-full bg-accent animate-pulse" />
              AI-Powered Health Assistant
            </div>

            <h1 className="font-display text-5xl sm:text-6xl lg:text-7xl font-bold text-slate-900 dark:text-white leading-tight mb-6">
              <span className="gradient-text">Aarogya AI</span>
            </h1>

            <p className="text-xl text-slate-600 dark:text-slate-300 mb-4 text-balance leading-relaxed">
              Your intelligent medical companion for health guidance, symptom insights, and wellness support — available anytime you need it.
            </p>

            <p className="text-sm text-slate-500 dark:text-slate-400 mb-8 italic">
              ⚕️ Not a substitute for professional medical advice. Always consult a healthcare provider for medical decisions.
            </p>

            <div className="flex flex-wrap gap-4">
              <Link to="/register" className="btn-primary text-lg px-8 py-4">
                Get Started Free
              </Link>
              <Link to="/login" className="btn-secondary text-lg px-8 py-4">
                Open Chat
              </Link>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, x: 30 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.7, delay: 0.2 }}
          >
            <HeroIllustration />
          </motion.div>
        </div>

        <motion.div
          animate={{ y: [0, 8, 0] }}
          transition={{ repeat: Infinity, duration: 2 }}
          className="absolute bottom-8 left-1/2 -translate-x-1/2 text-slate-400"
        >
          <HiChevronDown className="w-6 h-6" />
        </motion.div>
      </section>

      {/* Features */}
      <section className="py-24 bg-white dark:bg-slate-900/50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="font-display text-4xl font-bold text-slate-900 dark:text-white mb-4">
              Everything you need for better health
            </h2>
            <p className="text-lg text-slate-600 dark:text-slate-400 max-w-2xl mx-auto">
              Comprehensive AI-powered tools designed to help you understand and manage your health.
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {features.map((feature, i) => (
              <motion.div
                key={feature.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1 }}
                className="glass-card p-6 hover:shadow-card transition-shadow"
              >
                <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center mb-4">
                  <feature.icon className="w-6 h-6 text-primary" />
                </div>
                <h3 className="font-display font-semibold text-lg mb-2 text-slate-800 dark:text-white">
                  {feature.title}
                </h3>
                <p className="text-sm text-slate-600 dark:text-slate-400 leading-relaxed">
                  {feature.description}
                </p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Testimonials */}
      <section className="py-24">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="font-display text-4xl font-bold text-center text-slate-900 dark:text-white mb-16">
            Trusted by patients & professionals
          </h2>
          <div className="grid md:grid-cols-3 gap-8">
            {testimonials.map((t, i) => (
              <motion.div
                key={t.name}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1 }}
                className="glass-card p-6"
              >
                <p className="text-slate-600 dark:text-slate-300 mb-6 leading-relaxed italic">
                  "{t.text}"
                </p>
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-primary/20 flex items-center justify-center text-primary font-bold">
                    {t.avatar}
                  </div>
                  <div>
                    <p className="font-semibold text-slate-800 dark:text-white">{t.name}</p>
                    <p className="text-sm text-slate-500">{t.role}</p>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* FAQ */}
      <section className="py-24 bg-white dark:bg-slate-900/50">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="font-display text-4xl font-bold text-center text-slate-900 dark:text-white mb-12">
            Frequently Asked Questions
          </h2>
          <div className="space-y-4">
            {faqs.map((faq, i) => (
              <div key={i} className="glass-card overflow-hidden">
                <button
                  onClick={() => setOpenFaq(openFaq === i ? null : i)}
                  className="w-full flex items-center justify-between p-5 text-left"
                >
                  <span className="font-semibold text-slate-800 dark:text-white">{faq.q}</span>
                  <HiChevronDown
                    className={`w-5 h-5 text-slate-400 transition-transform ${
                      openFaq === i ? 'rotate-180' : ''
                    }`}
                  />
                </button>
                {openFaq === i && (
                  <motion.div
                    initial={{ height: 0 }}
                    animate={{ height: 'auto' }}
                    className="px-5 pb-5 text-slate-600 dark:text-slate-400 text-sm leading-relaxed"
                  >
                    {faq.a}
                  </motion.div>
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-24">
        <div className="max-w-4xl mx-auto px-4 text-center">
          <div className="glass-card p-12 bg-hero-gradient relative overflow-hidden">
            <div className="absolute inset-0 bg-white/90 dark:bg-dark/90" />
            <div className="relative">
              <h2 className="font-display text-4xl font-bold text-slate-900 dark:text-white mb-4">
                Start your health journey today
              </h2>
              <p className="text-lg text-slate-600 dark:text-slate-300 mb-8">
                Join thousands using Aarogya AI for smarter health decisions.
              </p>
              <Link to="/register" className="btn-primary text-lg px-8 py-4">
                Create Free Account
              </Link>
            </div>
          </div>
        </div>
      </section>

      <Footer />
    </Layout>
  );
}
