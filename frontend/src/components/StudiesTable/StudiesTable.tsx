import { useNavigate } from 'react-router-dom';
import type { Study, StudyStatus } from '@/types/study';
import { formatDateTime } from '@/utils/formatDateTime';
import s from './StudiesTable.module.css';

const STATUS: Record<StudyStatus, { label: string; dotClass: string }> = {
  pathology_found: { label: 'Найдены патологии', dotClass: s.pink },
  no_pathology: { label: 'Патологии не найдены', dotClass: s.green },
  processing: { label: 'Обрабатывается', dotClass: s.grey },
};

interface StudiesTableProps {
  studies: Study[];
}

export default function StudiesTable({ studies }: StudiesTableProps) {
  const navigate = useNavigate();
    return (
    <div className={s.scroll}>
      <table className={s.table}>
        <thead>
          <tr>
            <th>ID пациента</th>
            <th>Пол, возраст</th>
            <th>Название</th>
            <th>Статус обработки</th>
            <th>Дата исследования</th>
            <th>Дата загрузки</th>
            <th>Срезы</th>
          </tr>
        </thead>
        <tbody>
          {studies.length === 0 && (
            <tr>
              <td colSpan={7} className={s.empty}>Исследований пока нет</td>
            </tr>
          )}
          {studies.map((st) => {
            const status = STATUS[st.status];
            return (
              <tr key={st.id} onClick={() => navigate(`/patient/view?id=${st.id}`)}>
                <td>{st.patientId}</td>
                <td>{st.sex === 'F' ? 'Ж' : 'М'}, {st.age}</td>
                <td>{st.title}</td>
                <td>
                  <span className={s.status}>
                    <span className={`${s.dot} ${status.dotClass}`} aria-hidden="true" />
                    {status.label}
                  </span>
                </td>
                <td>{formatDateTime(st.studyDate)}</td>
                <td>{formatDateTime(st.uploadedAt)}</td>
                <td>{st.slicesCount}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}