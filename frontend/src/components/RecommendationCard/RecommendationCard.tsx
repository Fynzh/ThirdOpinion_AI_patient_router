import { useState } from 'react';
import type { EditRecommendationPayload, Priority, Recommendation } from '@/types/recommendation';
import { PRIORITY_LABELS } from '@/types/recommendation';
import s from './RecommendationCard.module.css';

interface Props {
  rec: Recommendation;
  busy: boolean;
  onApprove: () => void;
  onReject: () => void;
  onEdit: (payload: EditRecommendationPayload) => void;
}

export default function RecommendationCard({ rec, busy, onApprove, onReject, onEdit }: Props) {
  const [isEditing, setIsEditing] = useState(false);
  const [specialist, setSpecialist] = useState(rec.specialist);
  const [reasoning, setReasoning] = useState(rec.reasoning);
  const [priority, setPriority] = useState<Priority>(rec.priority);

  const save = () => {
    onEdit({ specialist, reasoning, priority });
    setIsEditing(false);
  };

  return (
    <div className={`${s.card} ${s[rec.status]}`}>
      <div className={s.head}>
        <span className={s.badge}>{rec.source_display}</span>
        <span className={`${s.badge} ${s[rec.priority]}`}>{rec.priority_display}</span>
        <span className={s.status}>{rec.status_display}</span>
        {rec.confidence !== null && (
          <span className={s.muted}>уверенность {Math.round(rec.confidence * 100)}%</span>
        )}
      </div>

      {isEditing ? (
        <div className={s.form}>
          <input value={specialist} onChange={(e) => setSpecialist(e.target.value)} />
          <textarea rows={4} value={reasoning} onChange={(e) => setReasoning(e.target.value)} />
          <select value={priority} onChange={(e) => setPriority(e.target.value as Priority)}>
            {Object.entries(PRIORITY_LABELS).map(([k, v]) => (
              <option key={k} value={k}>{v}</option>
            ))}
          </select>
          <div className={s.actions}>
            <button type="button" disabled={busy} onClick={save}>Сохранить</button>
            <button type="button" onClick={() => setIsEditing(false)}>Отмена</button>
          </div>
        </div>
      ) : (
        <>
          <h3 className={s.title}>{rec.specialist}</h3>
          <p className={s.text}>{rec.reasoning}</p>
          <div className={s.actions}>
            <button type="button" disabled={busy || rec.status === 'approved'} onClick={onApprove}>Одобрить</button>
            <button type="button" disabled={busy || rec.status === 'rejected'} onClick={onReject}>Отклонить</button>
            <button type="button" disabled={busy} onClick={() => setIsEditing(true)}>Править</button>
          </div>
        </>
      )}
    </div>
  );
}