import type { StudyListItem } from '../types'
import { formatDate, formatDateTime } from '../utils/format'
import StatusDot from './StatusDot'

interface Props {
  studies: StudyListItem[]
  sortDesc: boolean // true — сначала новые
  onToggleSort: () => void
  onOpen: (id: number) => void
}

export default function StudiesTable({ studies, sortDesc, onToggleSort, onOpen }: Props) {
  return (
    <div className="table-wrap">
      <table className="table">
        <thead>
          <tr>
            <th>ID</th>
            <th>Код пациента</th>
            <th>Исследование</th>
            <th>Дата исследования</th>
            <th>Статус обработки</th>
            <th>Рекомендации</th>
            <th>
              <button type="button" className="table__sort" onClick={onToggleSort}>
                Дата загрузки {sortDesc ? '↓' : '↑'}
              </button>
            </th>
          </tr>
        </thead>
        <tbody>
          {studies.map((study) => (
            <tr
              key={study.id}
              tabIndex={0}
              onClick={() => onOpen(study.id)}
              onKeyDown={(e) => e.key === 'Enter' && onOpen(study.id)}
            >
              <td>{study.id}</td>
              <td>{study.patient_code ?? '—'}</td>
              <td>{study.modality_display}</td>
              <td>{formatDate(study.study_date)}</td>
              <td>
                <StatusDot status={study.status} label={study.status_display} />
              </td>
              <td>{study.recommendations_count}</td>
              <td>{formatDateTime(study.created_at)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
