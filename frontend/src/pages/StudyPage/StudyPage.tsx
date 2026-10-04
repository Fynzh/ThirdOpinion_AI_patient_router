import { useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import AddRecommendationForm from '@/components/AddRecommendationForm/AddRecommendationForm';
import RecommendationCard from '@/components/RecommendationCard/RecommendationCard';
import { addDoctorRecommendation, generateRecommendations } from '@/api/studies';
import { approveRecommendation, editRecommendation, rejectRecommendation } from '@/api/recommendation';
import { useStudy } from '@/hooks/useStudy';
import { SEX_LABELS } from '@/types/patient';
import { formatDate } from '@/utils/formatDateTime';
import s from './StudyPage.module.css';

export default function StudyPage() {
  const [searchParams] = useSearchParams();
  const id = searchParams.get('id');
  const { study, isLoading, error, reload } = useStudy(Number(id));
  const [busy, setBusy] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  const run = async (action: () => Promise<unknown>) => {
    setBusy(true);
    setActionError(null);
    try {
      await action();
      reload();
    } catch (e) {
      setActionError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  if (isLoading) return <p>Загрузка…</p>;
  if (error) return <p role="alert">{error.message}</p>;
  if (!study) return null;

  const p = study.patient;
  const allChecked = study.recommendations.length > 0
    && study.recommendations.every((r) => r.status !== 'pending');

  const regenerate = () => {
    if (!window.confirm('ИИ-рекомендации будут удалены и созданы заново, включая уже одобренные. Продолжить?')) return;
    run(() => generateRecommendations(study.id));
  };

  return (
    <>
      <Link to="/studies" className={s.back}>← К списку</Link>
      <h2 className={s.title}>{p.full_name || p.patient_code}</h2>
      <p className={s.sub}>
        {p.patient_code} · {SEX_LABELS[p.sex]}, {p.age} лет · {study.modality_display} от {formatDate(study.study_date)}
      </p>
      <p className={s.status}>{study.status_display}</p>

      <section className={s.block}>
        <h3>Заключение рентгенолога</h3>
        <p className={s.conclusion}>{study.radiologist_conclusion}</p>
        {study.file && <a href={study.file} target="_blank" rel="noreferrer">Открыть файл исследования</a>}
      </section>

      <section className={s.block}>
        <div className={s.row}>
          <h3>Рекомендации</h3>
          <button type="button" className={s.btn} disabled={busy} onClick={regenerate}>
            Перегенерировать ИИ
          </button>
        </div>

        {actionError && <p role="alert">{actionError}</p>}
        {allChecked && <p className={s.ok}>Все рекомендации проверены, план обращения сформирован.</p>}
        {study.recommendations.length === 0 && <p className={s.sub}>Рекомендаций пока нет</p>}

        {study.recommendations.map((rec) => (
          <RecommendationCard
            key={rec.id}
            rec={rec}
            busy={busy}
            onApprove={() => run(() => approveRecommendation(rec.id))}
            onReject={() => run(() => rejectRecommendation(rec.id))}
            onEdit={(payload) => run(() => editRecommendation(rec.id, payload))}
          />
        ))}

        <AddRecommendationForm
          busy={busy}
          onSubmit={(payload) => run(() => addDoctorRecommendation(study.id, payload))}
        />
      </section>
    </>
  );
}