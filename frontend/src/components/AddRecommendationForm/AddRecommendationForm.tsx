import { useState } from 'react';
import type { AddDoctorRecommendationPayload, Priority } from '@/types/recommendation';
import { PRIORITY_LABELS } from '@/types/recommendation';
import s from './AddRecommendationForm.module.css';

interface Props {
  busy: boolean;
  onSubmit: (payload: AddDoctorRecommendationPayload) => Promise<void>;
}

export default function AddRecommendationForm({ busy, onSubmit }: Props) {
  const [specialist, setSpecialist] = useState('');
  const [reasoning, setReasoning] = useState('');
  const [priority, setPriority] = useState<Priority>('medium');

  const submit = async () => {
    if (!specialist.trim() || !reasoning.trim()) return;
    await onSubmit({ specialist, reasoning, priority });
    setSpecialist('');
    setReasoning('');
    setPriority('medium');
  };

  return (
    <div className={s.card}>
      <h3 className={s.title}>Своя рекомендация</h3>
      <div className={s.form}>
        <input placeholder="Специалист" value={specialist} onChange={(e) => setSpecialist(e.target.value)} />
        <textarea rows={3} placeholder="Обоснование" value={reasoning} onChange={(e) => setReasoning(e.target.value)} />
        <select value={priority} onChange={(e) => setPriority(e.target.value as Priority)}>
          {Object.entries(PRIORITY_LABELS).map(([k, v]) => (
            <option key={k} value={k}>{v}</option>
          ))}
        </select>
        <div className={s.actions}>
          <button type="button" disabled={busy || !specialist.trim() || !reasoning.trim()} onClick={submit}>
            Добавить
          </button>
        </div>
      </div>
    </div>
  );
}