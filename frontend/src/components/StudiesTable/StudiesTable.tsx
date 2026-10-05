import { Fragment, useMemo, useState } from 'react';
import type { ReactNode } from 'react';
import { useNavigate } from 'react-router-dom';
import type { StudyListItem } from '@/types/study';
import { formatDateTime, formatDate } from '@/utils/formatDateTime';
import s from './StudiesTable.module.css';

interface StudiesTableProps {
  studies: StudyListItem[];
  isEditing: boolean;
  selectedIds: number[];
  onToggleSelect: (id: number) => void;
}

interface Group {
  patientId: number;
  studies: StudyListItem[]; // от новых к старым
}

const byNewest = (a: StudyListItem, b: StudyListItem) =>
  b.study_date.localeCompare(a.study_date) || b.created_at.localeCompare(a.created_at);

function groupByPatient(studies: StudyListItem[]): Group[] {
  const map = new Map<number, StudyListItem[]>();
  for (const st of studies) {
    const list = map.get(st.patient);
    if (list) list.push(st);
    else map.set(st.patient, [st]);
  }
  const groups = [...map.entries()].map(([patientId, list]) => ({
    patientId,
    studies: [...list].sort(byNewest),
  }));
  groups.sort((a, b) => byNewest(a.studies[0], b.studies[0]));
  return groups;
}

function pluralStudies(n: number) {
  const m10 = n % 10;
  const m100 = n % 100;
  if (m10 === 1 && m100 !== 11) return 'исследование';
  if (m10 >= 2 && m10 <= 4 && (m100 < 12 || m100 > 14)) return 'исследования';
  return 'исследований';
}

export default function StudiesTable({ studies, isEditing, selectedIds, onToggleSelect }: StudiesTableProps) {
  const navigate = useNavigate();
  const groups = useMemo(() => groupByPatient(studies), [studies]);
  const [expanded, setExpanded] = useState<Set<number>>(new Set());

  const toggleGroup = (patientId: number) =>
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(patientId)) next.delete(patientId);
      else next.add(patientId);
      return next;
    });

  const columns = 7 + (isEditing ? 1 : 0);

  const renderRow = (
    st: StudyListItem,
    toggleCell: ReactNode,
    patientCell: ReactNode,
    isChild = false,
  ) => (
    <tr
      key={st.id}
      className={`${isEditing ? '' : s.clickable} ${isChild ? s.child : ''}`}
      onClick={() => {
        if (isEditing) return;
        navigate(`/studies/view?id=${st.id}`);
      }}
    >
      <td className={s.toggleCell}>{toggleCell}</td>
      {isEditing && (
        <td>
          <input
            type="checkbox"
            className={s.checkbox}
            checked={selectedIds.includes(st.id)}
            onChange={() => onToggleSelect(st.id)}
          />
        </td>
      )}
      {patientCell}
      <td>
        {st.modality_display}
        {st.display_title && <div className={s.sub}>{st.display_title}</div>}
      </td>
      <td>{formatDate(st.study_date)}</td>
      <td>{st.status_display}</td>
      <td>{st.recommendations_count}</td>
      <td>{formatDateTime(st.created_at)}</td>
    </tr>
  );

  return (
    <div className={s.scroll}>
      <table className={s.table}>
        <thead>
          <tr>
            <th className={s.toggleCell} aria-label="Развернуть" />
            {isEditing && <th aria-label="Выбор" />}
            <th>Пациент</th>
            <th>Тип исследования</th>
            <th>Дата исследования</th>
            <th>Статус</th>
            <th>Рекомендации</th>
            <th>Дата загрузки</th>
          </tr>
        </thead>
        <tbody>
          {groups.length === 0 && (
            <tr>
              <td colSpan={columns} className={s.empty}>Исследований пока нет</td>
            </tr>
          )}

          {groups.map(({ patientId, studies: list }) => {
            const [latest, ...older] = list;
            const isOpen = expanded.has(patientId);

            const toggle =
              older.length > 0 ? (
                <button
                  type="button"
                  className={s.toggle}
                  aria-expanded={isOpen}
                  aria-label={isOpen ? 'Свернуть исследования пациента' : 'Показать другие исследования пациента'}
                  onClick={(e) => {
                    e.stopPropagation();
                    toggleGroup(patientId);
                  }}
                >
                  <svg
                    className={`${s.chevron} ${isOpen ? s.chevronOpen : ''}`}
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    aria-hidden="true"
                  >
                    <polyline points="9 6 15 12 9 18" />
                  </svg>
                </button>
              ) : null;

            const patientCell = (
              <td>
                <span>{latest.patient_full_name}</span>
                <div className={s.sub}>
                  {latest.patient_code}
                  {list.length > 1 && ` · ${list.length} ${pluralStudies(list.length)}`}
                </div>
              </td>
            );

            return (
              <Fragment key={patientId}>
                {renderRow(latest, toggle, patientCell)}
                {isOpen && older.map((st) => renderRow(st, null, <td />, true))}
              </Fragment>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}