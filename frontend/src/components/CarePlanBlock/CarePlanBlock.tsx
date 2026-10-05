import { useState } from 'react';
import ConfirmDialog from '@/components/ConfirmDialog/ConfirmDialog';
import type { CarePlan } from '@/types/care-plan';
import { PRIORITY_LABELS } from '@/types/recommendation';
import { formatDateTime } from '@/utils/formatDateTime';
import s from './CarePlanBlock.module.css';

interface Props {
  plan: CarePlan | null;
  hasPending: boolean;
  patientEmail: string;
  busy: boolean;
  onSaveComment: (comment: string) => void;
  onSend: () => void;
}

type ViewProps = Omit<Props, 'plan' | 'hasPending'> & { plan: CarePlan };

function PlanView({ plan, patientEmail, busy, onSaveComment, onSend }: ViewProps) {
  const [comment, setComment] = useState(plan.doctor_comment);
  const [confirmOpen, setConfirmOpen] = useState(false);

  const isSent = plan.status === 'sent';
  const items = plan.recommendations_snapshot;
  const dirty = comment !== plan.doctor_comment;
  const canSend = !isSent && !dirty && Boolean(patientEmail) && items.length > 0;

  let hint: string | null = null;
  if (!isSent) {
    if (items.length === 0) hint = 'В плане нет одобренных рекомендаций.';
    else if (!patientEmail) hint = 'У пациента не указан email, отправка невозможна.';
    else if (dirty) hint = 'Сохраните комментарий перед отправкой.';
  }

  return (
    <div className={`${s.card} ${isSent ? s.sent : ''}`}>
      <div className={s.head}>
        <span className={s.badge}>{plan.status_display}</span>
        {isSent && plan.sent_at && (
          <span className={s.muted}>{formatDateTime(plan.sent_at)}</span>
        )}
      </div>

      <ol className={s.list}>
        {items.map((item, i) => (
          <li key={i} className={s.item}>
            <div className={s.itemHead}>
              <strong>{item.specialist}</strong>
              <span className={`${s.prio} ${s[item.priority]}`}>{PRIORITY_LABELS[item.priority]}</span>
            </div>
            <p className={s.text}>{item.reasoning}</p>
          </li>
        ))}
      </ol>

      <label className={s.field}>
        <span>Комментарий врача</span>
        <textarea
          className={s.textarea}
          rows={3}
          value={comment}
          disabled={isSent || busy}
          placeholder="Необязательно. Попадёт в письмо пациенту"
          onChange={(e) => setComment(e.target.value)}
        />
      </label>

      {!isSent && (
        <div className={s.actions}>
          {dirty && (
            <button type="button" className={s.secondary} disabled={busy} onClick={() => onSaveComment(comment)}>
              Сохранить комментарий
            </button>
          )}
          <button type="button" className={s.primary} disabled={busy || !canSend} onClick={() => setConfirmOpen(true)}>
            {busy ? 'Подождите…' : 'Отправить пациенту'}
          </button>
        </div>
      )}
      {hint && <p className={s.hint}>{hint}</p>}

      <ConfirmDialog
        open={confirmOpen}
        variant="info"
        title="Отправить план пациенту?"
        message={`План будет отправлен на ${patientEmail}. После отправки изменить его будет нельзя.`}
        confirmText="Отправить"
        onConfirm={() => {
          setConfirmOpen(false);
          onSend();
        }}
        onCancel={() => setConfirmOpen(false)}
      />
    </div>
  );
}

export default function CarePlanBlock({ plan, hasPending, ...rest }: Props) {
  if (!plan) {
    return (
      <p className={s.hint}>
        {hasPending
          ? 'План обращения появится, когда все рекомендации будут одобрены или отклонены.'
          : 'Одобрите хотя бы одну рекомендацию, чтобы сформировать план.'}
      </p>
    );
  }
  return <PlanView key={plan.id} plan={plan} {...rest} />;
}