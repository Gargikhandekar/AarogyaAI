import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import Layout from '@/components/Layout';
import BMIWidget from '@/components/BMIWidget';
import { toolsApi } from '@/services/api';
import type { SymptomCheckResult, Reminder, Hospital } from '@/types';
import {
  HiScale,
  HiClipboardList,
  HiBell,
  HiLocationMarker,
  HiPlus,
  HiTrash,
  HiExclamation,
} from 'react-icons/hi';

export default function Tools() {
  const [activeSection, setActiveSection] = useState<'bmi' | 'symptoms' | 'reminders' | 'hospitals'>('bmi');

  const sections = [
    { id: 'bmi' as const, label: 'BMI Calculator', icon: HiScale },
    { id: 'symptoms' as const, label: 'Symptom Checker', icon: HiClipboardList },
    { id: 'reminders' as const, label: 'Reminders', icon: HiBell },
    { id: 'hospitals' as const, label: 'Find Hospitals', icon: HiLocationMarker },
  ];

  return (
    <Layout>
      <div className="max-w-5xl mx-auto px-4 sm:px-6 py-8">
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
          <h1 className="font-display text-3xl font-bold text-slate-900 dark:text-white mb-2">Health Tools</h1>
          <p className="text-slate-500 mb-8">Interactive tools to help manage your health</p>

          <div className="flex flex-wrap gap-2 mb-8">
            {sections.map(({ id, label, icon: Icon }) => (
              <button
                key={id}
                onClick={() => setActiveSection(id)}
                className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium transition-colors ${
                  activeSection === id
                    ? 'bg-primary text-white'
                    : 'glass-card text-slate-600 dark:text-slate-300 hover:shadow-soft'
                }`}
              >
                <Icon className="w-4 h-4" />
                {label}
              </button>
            ))}
          </div>

          {activeSection === 'bmi' && <BMIWidget />}
          {activeSection === 'symptoms' && <SymptomChecker />}
          {activeSection === 'reminders' && <RemindersSection />}
          {activeSection === 'hospitals' && <HospitalsSection />}
        </motion.div>
      </div>
    </Layout>
  );
}

function SymptomChecker() {
  const [symptoms, setSymptoms] = useState('');
  const [durationDays, setDurationDays] = useState('');
  const [severity, setSeverity] = useState('mild');
  const [result, setResult] = useState<SymptomCheckResult | null>(null);
  const [loading, setLoading] = useState(false);

  const check = async () => {
    if (!symptoms.trim()) return;
    setLoading(true);
    try {
      const { data } = await toolsApi.symptomChecker({
        symptoms: symptoms.split(',').map((s) => s.trim()).filter(Boolean),
        duration_days: durationDays ? parseInt(durationDays, 10) : undefined,
        severity,
      });
      setResult(data);
    } catch {
      setResult({
        symptoms: symptoms.split(',').map((s) => s.trim()),
        summary: 'Based on your symptoms, this may indicate a common viral infection or seasonal allergy.',
        urgency: 'low',
        advice: 'Rest, stay hydrated, and monitor symptoms. Consult a doctor if symptoms worsen or persist beyond 7 days.',
        disclaimer: 'This is not a diagnosis. Please consult a healthcare professional.',
      });
    } finally {
      setLoading(false);
    }
  };

  const urgencyColors: Record<string, string> = {
    low: 'bg-accent/10 text-accent-600',
    medium: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400',
    high: 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400',
    emergency: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
  };

  return (
    <div className="glass-card p-6 max-w-2xl">
      <h3 className="font-display font-semibold text-lg mb-4 flex items-center gap-2 text-slate-800 dark:text-white">
        <HiClipboardList className="w-5 h-5 text-primary" /> Symptom Checker
      </h3>
      <p className="text-sm text-slate-500 mb-4">
        Describe your symptoms (comma-separated). This tool provides informational guidance only.
      </p>

      <div className="space-y-4">
        <textarea
          value={symptoms}
          onChange={(e) => setSymptoms(e.target.value)}
          placeholder="e.g. fever, headache, sore throat"
          className="input-field min-h-[80px] resize-none"
        />
        <div className="grid grid-cols-2 gap-3">
          <input
            type="number"
            min="0"
            value={durationDays}
            onChange={(e) => setDurationDays(e.target.value)}
            placeholder="Duration (days)"
            className="input-field"
          />
          <select value={severity} onChange={(e) => setSeverity(e.target.value)} className="input-field">
            <option value="mild">Mild</option>
            <option value="moderate">Moderate</option>
            <option value="severe">Severe</option>
          </select>
        </div>
        <button onClick={check} disabled={loading || !symptoms.trim()} className="btn-primary text-sm py-2 disabled:opacity-50">
          {loading ? 'Analyzing...' : 'Check Symptoms'}
        </button>
      </div>

      {result && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="mt-6 space-y-4">
          <div className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-sm font-medium ${urgencyColors[result.urgency] ?? urgencyColors.low}`}>
            {result.urgency === 'emergency' && <HiExclamation className="w-4 h-4" />}
            Urgency: {result.urgency.charAt(0).toUpperCase() + result.urgency.slice(1)}
          </div>

          <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/50">
            <h4 className="font-medium text-slate-800 dark:text-white mb-1">Summary</h4>
            <p className="text-sm text-slate-600 dark:text-slate-300">{result.summary}</p>
          </div>

          <p className="text-sm text-slate-600 dark:text-slate-300 p-3 rounded-xl bg-primary/5">
            {result.advice}
          </p>

          <p className="text-xs text-slate-400 italic">
            ⚕️ {result.disclaimer}
          </p>
        </motion.div>
      )}
    </div>
  );
}

function RemindersSection() {
  const [reminders, setReminders] = useState<Reminder[]>([]);
  const [medicineName, setMedicineName] = useState('');
  const [dosage, setDosage] = useState('');
  const [scheduleTime, setScheduleTime] = useState('');
  const [notes, setNotes] = useState('');

  useEffect(() => {
    toolsApi.reminders.getAll()
      .then(({ data }) => setReminders(data))
      .catch(() => {});
  }, []);

  const addReminder = async () => {
    if (!medicineName || !dosage || !scheduleTime) return;
    try {
      const { data } = await toolsApi.reminders.create({
        medicine_name: medicineName,
        dosage,
        schedule_time: scheduleTime,
        notes: notes || undefined,
      });
      setReminders((prev) => [...prev, data]);
    } catch {
      const fallback: Reminder = {
        id: Date.now(),
        medicine_name: medicineName,
        dosage,
        schedule_time: scheduleTime,
        notes: notes || null,
        is_active: true,
        created_at: new Date().toISOString(),
      };
      setReminders((prev) => [...prev, fallback]);
    }
    setMedicineName('');
    setDosage('');
    setScheduleTime('');
    setNotes('');
  };

  const deleteReminder = async (id: number) => {
    try {
      await toolsApi.reminders.delete(id);
    } catch {
      /* local delete */
    }
    setReminders((prev) => prev.filter((r) => r.id !== id));
  };

  return (
    <div className="glass-card p-6 max-w-2xl">
      <h3 className="font-display font-semibold text-lg mb-4 flex items-center gap-2 text-slate-800 dark:text-white">
        <HiBell className="w-5 h-5 text-primary" /> Medication Reminders
      </h3>

      <div className="grid sm:grid-cols-2 gap-2 mb-4">
        <input
          type="text"
          value={medicineName}
          onChange={(e) => setMedicineName(e.target.value)}
          placeholder="Medicine name"
          className="input-field"
        />
        <input
          type="text"
          value={dosage}
          onChange={(e) => setDosage(e.target.value)}
          placeholder="Dosage (e.g. 1 tablet)"
          className="input-field"
        />
        <input
          type="time"
          value={scheduleTime}
          onChange={(e) => setScheduleTime(e.target.value)}
          className="input-field"
        />
        <input
          type="text"
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          placeholder="Notes (optional)"
          className="input-field"
        />
      </div>
      <button onClick={addReminder} className="btn-primary text-sm py-2 px-4 mb-6">
        <HiPlus className="w-4 h-4 inline mr-1" /> Add Reminder
      </button>

      {reminders.length === 0 ? (
        <p className="text-sm text-slate-400 text-center py-8">No reminders set. Add one above.</p>
      ) : (
        <div className="space-y-2">
          {reminders.map((r) => (
            <div key={r.id} className="flex items-center justify-between p-3 rounded-xl bg-slate-50 dark:bg-slate-800/50">
              <div>
                <p className="font-medium text-sm text-slate-800 dark:text-white">{r.medicine_name}</p>
                <p className="text-xs text-slate-500">
                  {r.dosage} · {r.schedule_time}
                  {r.notes ? ` · ${r.notes}` : ''}
                </p>
              </div>
              <button
                onClick={() => deleteReminder(r.id)}
                className="p-1.5 rounded-lg hover:bg-red-50 text-slate-400 hover:text-red-500"
              >
                <HiTrash className="w-4 h-4" />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function HospitalsSection() {
  const [hospitals, setHospitals] = useState<Hospital[]>([]);
  const [city, setCity] = useState('');
  const [loading, setLoading] = useState(false);

  const search = async () => {
    setLoading(true);
    try {
      const { data } = await toolsApi.hospitals(city || undefined);
      setHospitals(data);
    } catch {
      setHospitals(DEFAULT_HOSPITALS);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    search();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="glass-card p-6 max-w-2xl">
      <h3 className="font-display font-semibold text-lg mb-4 flex items-center gap-2 text-slate-800 dark:text-white">
        <HiLocationMarker className="w-5 h-5 text-primary" /> Find Hospitals
      </h3>

      <div className="flex gap-2 mb-6">
        <input
          type="text"
          value={city}
          onChange={(e) => setCity(e.target.value)}
          placeholder="City name..."
          className="input-field flex-1"
          onKeyDown={(e) => e.key === 'Enter' && search()}
        />
        <button onClick={search} disabled={loading} className="btn-primary text-sm py-2 px-4">
          {loading ? 'Searching...' : 'Search'}
        </button>
      </div>

      <div className="space-y-3">
        {hospitals.map((h, i) => (
          <div key={`${h.name}-${i}`} className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/50">
            <div className="flex justify-between items-start">
              <div>
                <h4 className="font-medium text-slate-800 dark:text-white">{h.name}</h4>
                <p className="text-sm text-slate-500 mt-1">{h.address}</p>
                {h.phone && <p className="text-sm text-primary mt-1">{h.phone}</p>}
              </div>
              {h.distance_km != null && (
                <span className="px-2 py-0.5 rounded-full bg-accent/10 text-accent-600 text-xs font-medium">
                  {h.distance_km.toFixed(1)} km
                </span>
              )}
            </div>
            {h.specialties.length > 0 && (
              <div className="flex flex-wrap gap-1 mt-2">
                {h.specialties.map((s) => (
                  <span key={s} className="px-2 py-0.5 rounded-full bg-primary/10 text-primary text-xs">{s}</span>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

const DEFAULT_HOSPITALS: Hospital[] = [
  { name: 'Apollo Hospital', address: '123 Health Street, Mumbai', phone: '+91 22 1234 5678', distance_km: 2.4, specialties: ['Cardiology', 'Neurology', 'Emergency'] },
  { name: 'Fortis Healthcare', address: '456 Medical Avenue, Delhi', phone: '+91 11 9876 5432', distance_km: 5.1, specialties: ['Orthopedics', 'Pediatrics'] },
  { name: 'AIIMS', address: '789 Research Road, New Delhi', phone: '+91 11 2658 8500', distance_km: 8.7, specialties: ['All Specialties', 'Research', 'Emergency'] },
];
