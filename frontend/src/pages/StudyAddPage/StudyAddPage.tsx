import { useMemo, useState } from 'react';
import type { FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { createPatient } from '@/api/patients';
import { createStudy, fetchStudy } from '@/api/studies';
import AvailableStudies from '@/components/AvailableStudies/AvailableStudies';
import PatientForm from '@/components/PatientForm/PatientForm';
import PatientSelect from '@/components/PatientSelect/PatientSelect';
import SelectBox from '@/components/SelectBox/SelectBox';
import { useAvailableStudies } from '@/hooks/useAvailableStudies';
import { usePatients } from '@/hooks/usePatients';
import { EMPTY_PATIENT_FORM } from '@/types/patient';
import type { PatientFormValues, PatientSummary } from '@/types/patient';
import { MODALITY_LABELS } from '@/types/study';
import type { Modality, StudyListItem } from '@/types/study';
import { TODAY, calcAge } from '@/utils/dates';
import { isPhoneComplete } from '@/utils/phone';
import s from './StudyAddPage.module.css';

const MODALITY_ITEMS = (Object.entries(MODALITY_LABELS) as [Modality, string][]).map(
  ([key, label], i) => ({ id: i + 1, key, label }),
);

export default function StudyAddPage() {
  const navigate = useNavigate();
  const { patients, isLoading, error } = usePatients();
  const [extraPatients, setExtraPatients] = useState<PatientSummary[]>([]);

  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [isCreatingNew, setIsCreatingNew] = useState(false);
  const [newPatient, setNewPatient] = useState<PatientFormValues>(EMPTY_PATIENT_FORM);

  const [modalityId, setModalityId] = useState<number | null>(null);
  const [showTypeHint, setShowTypeHint] = useState(false);
  const [studyDate, setStudyDate] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [conclusion, setConclusion] = useState('');

  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const allPatients = useMemo(
    () => [...patients, ...extraPatients.filter((e) => !patients.some((p) => p.id === e.id))],
    [patients, extraPatients],
  );
  const { items: availableStudies, isLoading: availableLoading } = useAvailableStudies(selectedId);

  const modality = MODALITY_ITEMS.find((m) => m.id === modalityId)?.key ?? null;

  const newPatientValid =
    newPatient.full_name.trim() !== '' &&
    newPatient.sex !== '' &&
    calcAge(newPatient.birth_date) !== null &&
    (newPatient.phone === '' || isPhoneComplete(newPatient.phone));
  const hasPatient = isCreatingNew ? newPatientValid : selectedId !== null;
  const canSubmit =
    hasPatient && modality !== null && studyDate !== '' && conclusion.trim() !== '' && !submitting;

  const handleSelect = (id: number) => {
    setSelectedId(id);
    setIsCreatingNew(false);
  };
  const handleCreateNew = () => {
    setSelectedId(null);
    setIsCreatingNew(true);
  };

  const pickAvailable = async (st: StudyListItem) => {
    try {
      const full = await fetchStudy(st.id);
      setConclusion(full.radiologist_conclusion);
      setStudyDate(full.study_date.slice(0, 10));
      const item = MODALITY_ITEMS.find((m) => m.key === full.modality);
      if (item) {
        setModalityId(item.id);
        setShowTypeHint(false);
      }
    } catch (err) {
      setSubmitError((err as Error).message);
    }
  };

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    if (!canSubmit || modality === null) return;

    setSubmitting(true);
    setSubmitError(null);

    try {
      let patientId = selectedId;

      if (isCreatingNew) {
        const created = await createPatient({
          full_name: newPatient.full_name.trim(),
          birth_date: newPatient.birth_date as string,
          sex: newPatient.sex as 'M' | 'F',
          age: calcAge(newPatient.birth_date) as number,
          phone: newPatient.phone.trim(),
          email: newPatient.email.trim(),
        });
        patientId = created.id;
        setExtraPatients((prev) => [...prev, created]);
        setSelectedId(created.id);
        setIsCreatingNew(false);
        setNewPatient(EMPTY_PATIENT_FORM);
      }

      if (patientId === null) return;

      const study = await createStudy({
        patient: patientId,
        modality,
        study_date: studyDate,
        radiologist_conclusion: conclusion.trim(),
        file,
      });
      navigate(`/studies/view?id=${study.id}`);
    } catch (err) {
      setSubmitError((err as Error).message);
      setSubmitting(false);
    }
  };

  return (
    <form className={s.form} onSubmit={submit}>
      <h1 className={s.title}>Новое исследование</h1>

      {error && <p className={s.error} role="alert">{error.message}</p>}

      <section className={s.section}>
        <h2 className={s.sectionTitle}>Пациент</h2>
        <PatientSelect
          patients={allPatients}
          selectedId={selectedId}
          isCreatingNew={isCreatingNew}
          isLoading={isLoading}
          onSelect={handleSelect}
          onCreateNew={handleCreateNew}
        />
        {isCreatingNew && <PatientForm value={newPatient} onChange={setNewPatient} />}
      </section>

      <section className={s.section}>
        <h2 className={s.sectionTitle}>Исследование</h2>
        <div className={s.row}>
          <div className={s.field}>
            <span>Тип исследования</span>
            <SelectBox
              items={MODALITY_ITEMS}
              selectedId={modalityId}
              placeholder="Выберите тип"
              getLabel={(m) => m.label}
              onSelect={(id) => {
                setModalityId(id);
                setShowTypeHint(false);
              }}
              actionButton={{
                label: 'Другой тип',
                icon: '+',
                onClick: () => setShowTypeHint(true),
              }}
            />
          </div>

          <label className={s.field}>
            <span>Дата исследования</span>
            <input
              className={s.input}
              type="date"
              max={TODAY}
              value={studyDate}
              onChange={(e) => setStudyDate(e.target.value)}
            />
          </label>

          <label className={s.field}>
            <span>Файл (необязательно)</span>
            <input
              className={`${s.input} ${s.file}`}
              type="file"
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            />
          </label>
        </div>
        {showTypeHint && (
          <p className={s.hint}>
            Добавление новых типов исследований пока недоступно.
          </p>
        )}
      </section>

      <section className={s.section}>
        <h2 className={s.sectionTitle}>Заключение</h2>
        {selectedId !== null && (
          <AvailableStudies
            key={selectedId}
            items={availableStudies}
            isLoading={availableLoading}
            onPick={pickAvailable}
          />
        )}
        <textarea
          className={s.textarea}
          placeholder="Заключение платформы «Третье Мнение»"
          value={conclusion}
          onChange={(e) => setConclusion(e.target.value)}
        />
      </section>

      {submitError && <p className={s.error} role="alert">{submitError}</p>}

      <button type="submit" className={s.submit} disabled={!canSubmit}>
        {submitting ? 'Создаём…' : 'Создать исследование'}
      </button>
    </form>
  );
}