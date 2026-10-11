import { useState } from 'react';
import { motion } from 'framer-motion';
import { toolsApi } from '@/services/api';
import type { BMIResult } from '@/types';
import { HiScale } from 'react-icons/hi';

export default function BMIWidget() {
  const [weight, setWeight] = useState('');
  const [height, setHeight] = useState('');
  const [unit, setUnit] = useState<'metric' | 'imperial'>('metric');
  const [result, setResult] = useState<BMIResult | null>(null);
  const [loading, setLoading] = useState(false);

  const toMetric = () => {
    const w = parseFloat(weight);
    const h = parseFloat(height);
    if (unit === 'metric') {
      return { weight_kg: w, height_cm: h };
    }
    return {
      weight_kg: w * 0.453592,
      height_cm: h * 2.54,
    };
  };

  const calculate = async () => {
    if (!weight || !height) return;
    setLoading(true);
    const { weight_kg, height_cm } = toMetric();
    try {
      const { data } = await toolsApi.bmi({ weight_kg, height_cm });
      setResult(data);
    } catch {
      const h = height_cm / 100;
      const bmi = weight_kg / (h * h);
      let category = 'Normal weight';
      if (bmi < 18.5) category = 'Underweight';
      else if (bmi >= 25 && bmi < 30) category = 'Overweight';
      else if (bmi >= 30) category = 'Obese';
      setResult({
        bmi: Math.round(bmi * 10) / 10,
        category,
        advice: 'Maintain a balanced diet and regular exercise.',
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass-card p-6"
    >
      <div className="flex items-center gap-2 mb-4">
        <HiScale className="w-5 h-5 text-primary" />
        <h3 className="font-display font-semibold text-lg">BMI Calculator</h3>
      </div>

      <div className="flex gap-2 mb-4">
        {(['metric', 'imperial'] as const).map((u) => (
          <button
            key={u}
            onClick={() => setUnit(u)}
            className={`px-3 py-1 rounded-lg text-sm font-medium transition-colors ${
              unit === u ? 'bg-primary text-white' : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300'
            }`}
          >
            {u === 'metric' ? 'Metric' : 'Imperial'}
          </button>
        ))}
      </div>

      <div className="grid grid-cols-2 gap-3 mb-4">
        <input
          type="number"
          value={weight}
          onChange={(e) => setWeight(e.target.value)}
          placeholder={unit === 'metric' ? 'Weight (kg)' : 'Weight (lbs)'}
          className="input-field text-sm py-2"
        />
        <input
          type="number"
          value={height}
          onChange={(e) => setHeight(e.target.value)}
          placeholder={unit === 'metric' ? 'Height (cm)' : 'Height (in)'}
          className="input-field text-sm py-2"
        />
      </div>

      <button
        onClick={calculate}
        disabled={loading || !weight || !height}
        className="w-full btn-primary text-sm py-2 disabled:opacity-50"
      >
        {loading ? 'Calculating...' : 'Calculate BMI'}
      </button>

      {result && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="mt-4 p-4 rounded-xl bg-primary/5 border border-primary/20"
        >
          <p className="text-2xl font-display font-bold text-primary">{result.bmi}</p>
          <p className="text-sm font-medium text-slate-700 dark:text-slate-300">{result.category}</p>
          <p className="text-xs text-slate-500 mt-1">{result.advice}</p>
        </motion.div>
      )}
    </motion.div>
  );
}
