import { useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import AddRecommendationForm from '@/components/AddRecommendationForm/AddRecommendationForm';
import CarePlanBlock from '@/components/CarePlanBlock/CarePlanBlock';
import ConfirmDialog from '@/components/ConfirmDialog/ConfirmDialog';
import RecommendationCard from '@/components/RecommendationCard/RecommendationCard';
import TextBox from '@/components/TextBox/TextBox';
import {
  addDoctorRecommendation,
  downloadStudyFile,
  generateRecommendations,
  sendCarePlan,
  updateCarePlanComment,
} from '@/api/studies';
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
  const [regenOpen, setRegenOpen] = useState(false);

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
  const locked = study.care_plan?.status === 'sent';
  const hasPending = study.recommendations.some((r) => r.status === 'pending');
  const fileName = study.file
    ? decodeURIComponent(study.file.split('/').pop() ?? 'study')
    : '';

  return (
    <>
      <Link to="/studies" className={s.back}>← К списку</Link>
      <h2 className={s.title}>{p.full_name || p.patient_code}</h2>
      <p className={s.sub}>
        {p.patient_code} · {SEX_LABELS[p.sex]}, {p.age} лет · {study.modality_display} от {formatDate(study.study_date)}
      </p>
      <p className={s.status}></p>
      {actionError && <p className={s.error} role="alert">{actionError}</p>}

      <section className={s.block}>
        <TextBox title="Заключение платформы «Третье Мнение»">
          {study.radiologist_conclusion || 'Заключение не заполнено'}
        </TextBox>
        {study.file && (
          <button
            type="button"
            className={s.fileBtn}
            disabled={busy}
            onClick={() => run(() => downloadStudyFile(study.id, fileName))}
          >
            Скачать файл исследования
          </button>
        )}
      </section>

      <section className={s.block}>
        <div className={s.row}>
          <h3>Рекомендации</h3>
          <button
            type="button"
            className={s.btn}
            disabled={busy || locked}
            onClick={() => setRegenOpen(true)}
          >
            Перегенерировать ИИ
          </button>
        </div>

        {locked && (
          <p className={s.note}>План уже отправлен пациенту, рекомендации больше нельзя менять.</p>
        )}
        {study.recommendations.length === 0 && <p className={s.nocards}>Отклюнений не выявлено</p>}

        {study.recommendations.map((rec) => (
          <RecommendationCard
            key={rec.id}
            rec={rec}
            busy={busy || locked}
            onApprove={() => run(() => approveRecommendation(rec.id))}
            onReject={() => run(() => rejectRecommendation(rec.id))}
            onEdit={(payload) => run(() => editRecommendation(rec.id, payload))}
          />
        ))}

        <AddRecommendationForm
          busy={busy || locked}
          onSubmit={(payload) => run(() => addDoctorRecommendation(study.id, payload))}
        />
      </section>

      <section className={s.block}>
        <h3>План обращения</h3>
        <CarePlanBlock
          plan={study.care_plan}
          hasPending={hasPending}
          patientEmail={p.email}
          busy={busy}
          onSaveComment={(comment) => run(() => updateCarePlanComment(study.id, comment))}
          onSend={() => run(() => sendCarePlan(study.id))}
        />
      </section>

      <ConfirmDialog
        open={regenOpen}
        variant="warning"
        title="Перегенерировать рекомендации?"
        message="ИИ-рекомендации будут удалены и созданы заново, включая уже одобренные."
        confirmText="Перегенерировать"
        onConfirm={() => {
          setRegenOpen(false);
          run(() => generateRecommendations(study.id));
        }}
        onCancel={() => setRegenOpen(false)}
      />
    </>
  );
}