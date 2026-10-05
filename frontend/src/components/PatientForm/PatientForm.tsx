import type { PatientFormValues, Sex } from '@/types/patient';
import { SEX_LABELS } from '@/types/patient';
import { TODAY, calcAge } from '@/utils/dates';
import { formatPhone, isPhoneComplete } from '@/utils/phone';
import s from './PatientForm.module.css';

interface Props {
  value: PatientFormValues;
  onChange: (next: PatientFormValues) => void;
}

export default function PatientForm({ value, onChange }: Props) {
  const set = <K extends keyof PatientFormValues>(key: K, v: PatientFormValues[K]) =>
    onChange({ ...value, [key]: v });

  const age = calcAge(value.birth_date);

  return (
    <div className={s.card}>
      <h2 className={s.title}>Данные нового пациента</h2>

      <div className={s.grid}>
        <label className={`${s.field} ${s.wide}`}>
          <span>ФИО</span>
          <input
            className={s.input}
            value={value.full_name}
            autoComplete="off"
            onChange={(e) => set('full_name', e.target.value)}
          />
        </label>

        <label className={s.field}>
          <span>Дата рождения</span>
          <input
            className={s.input}
            type="date"
            max={TODAY}
            value={value.birth_date}
            onChange={(e) => set('birth_date', e.target.value)}
          />
        </label>

        <div className={s.field}>
          <span>Пол</span>
          <div className={s.segmented}>
            {(Object.keys(SEX_LABELS) as Sex[]).map((key) => (
              <button
                key={key}
                type="button"
                aria-pressed={value.sex === key}
                className={`${s.seg} ${value.sex === key ? s.segActive : ''}`}
                onClick={() => set('sex', key)}
              >
                {SEX_LABELS[key]}
              </button>
            ))}
          </div>
        </div>

        <label className={s.field}>
            <span>Телефон</span>
            <input
                className={`${s.input} ${value.phone !== '' && !isPhoneComplete(value.phone) ? s.invalid : ''}`}
                type="tel"
                inputMode="tel"
                autoComplete="tel"
                maxLength={18}
                placeholder="+7 (___) ___-__-__"
                value={value.phone}
                onChange={(e) => set('phone', formatPhone(e.target.value))}
                onKeyDown={(e) => {
                // «+7 (» нельзя стереть по одному символу, поэтому Backspace очищает поле целиком
                if (e.key === 'Backspace' && value.phone === '+7 (') {
                    e.preventDefault();
                    set('phone', '');
                }
                }}
            />
            </label>

        <label className={s.field}>
          <span>Email</span>
          <input
            className={s.input}
            type="email"
            value={value.email}
            onChange={(e) => set('email', e.target.value)}
          />
        </label>
      </div>

      <p className={s.hint}>
        {age !== null ? `Возраст: ${age}. ` : ''}Email нужен, чтобы отправить пациенту план обращения.
      </p>
    </div>
  );
}