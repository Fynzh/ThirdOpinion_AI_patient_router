import { useNavigate } from 'react-router-dom';
import type { StudyListItem, StudyStatus } from '@/types/study';
import { formatDateTime, formatDate } from '@/utils/formatDateTime';
import { getPatientLabel } from '@/utils/patientLabel';
import s from './StudiesTable.module.css';

const STATUS_DOT: Record<StudyStatus, string> = {
  new: s.grey,
  ai_done: s.blue,
  in_review: s.yellow,
  approved: s.green,
  sent: s.green,
};

interface StudiesTableProps {
  studies: StudyListItem[];
  isEditing: boolean;
  selectedIds: number[];
  onToggleSelect: (id: number) => void;
}

export default function StudiesTable({ studies, isEditing, selectedIds, onToggleSelect }: StudiesTableProps) {
  const navigate = useNavigate();
    return (
    <div className={s.scroll}>
      <table className={s.table}>
        <thead>
          <tr>
            {isEditing && <th aria-label="Выбор" />}
            <th>Код пациента</th>
            <th>Тип исследования</th>
            <th>Дата исследования</th>
            <th>Статус</th>
            <th>Рекомендации</th>
            <th>Дата загрузки</th>
          </tr>
        </thead>
        <tbody>
          {studies.length === 0 && (
            <tr>
              <td colSpan={isEditing ? 7 : 6} className={s.empty}>Исследований пока нет</td>
            </tr>
          )}
          {studies.map((st) => {
            return (
              <tr key={st.id} onClick={() => navigate(`/patient/view?id=${st.id}`)}>
                {isEditing && (
                  <td>
                    <input
                      type="checkbox"
                      checked={selectedIds.includes(st.id)}
                      onChange={() => onToggleSelect(st.id)}
                    />
                  </td>
                )}
                <td>{getPatientLabel(st.patient, st.patient_code)}</td>
                <td>{st.modality_display}</td>
                <td>{formatDate(st.study_date)}</td>
                <td>
                  <span className={s.status}>
                    <span className={`${s.dot} ${STATUS_DOT[st.status]}`} aria-hidden="true" />
                    {st.status_display}
                  </span>
                </td>
                <td>{st.recommendations_count}</td>
                <td>{formatDateTime(st.created_at)}</td>
                </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}