import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { fetchStudies } from '../api/studies'
import StudiesTable from '../components/StudiesTable'
import type { StudyListItem } from '../types'

export default function StudiesPage() {
  const navigate = useNavigate()
  const [studies, setStudies] = useState<StudyListItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [query, setQuery] = useState('') // поиск по коду пациента
  const [statusFilter, setStatusFilter] = useState('') // '' = все статусы
  const [sortDesc, setSortDesc] = useState(true) // сортировка по дате загрузки

  useEffect(() => {
    fetchStudies()
      .then(setStudies)
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  // Варианты фильтра берём из самих данных, чтобы не дублировать подписи бэкенда
  const statusOptions = useMemo(
    () => Array.from(new Map(studies.map((s) => [s.status, s.status_display]))),
    [studies],
  )

  const visible = useMemo(() => {
    const q = query.trim().toLowerCase()
    return studies
      .filter((s) => !statusFilter || s.status === statusFilter)
      .filter((s) => !q || (s.patient_code ?? '').toLowerCase().includes(q))
      .sort((a, b) => {
        const diff = new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
        return sortDesc ? -diff : diff
      })
  }, [studies, query, statusFilter, sortDesc])

  return (
    <>
      <nav className="breadcrumbs">Сервисы / Маршрутизация</nav>
      <div className="page-head">
        <h1 className="page-title">Маршрутизация</h1>
        {/* Эндпоинта создания пока нет, поэтому кнопка неактивна */}
        <button type="button" className="button" disabled title="Скоро">
          Создать маршрут
        </button>
      </div>

      <div className="toolbar">
        <input
          className="input"
          placeholder="Поиск по коду пациента"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <select
          className="input"
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
        >
          <option value="">Все статусы</option>
          {statusOptions.map(([value, label]) => (
            <option key={value} value={value}>
              {label}
            </option>
          ))}
        </select>
      </div>

      {loading && <div className="state">Загрузка…</div>}
      {error && <div className="state state--error">{error}</div>}
      {!loading && !error && visible.length === 0 && (
        <div className="state">Исследований не найдено</div>
      )}
      {!loading && !error && visible.length > 0 && (
        <StudiesTable
          studies={visible}
          sortDesc={sortDesc}
          onToggleSort={() => setSortDesc((d) => !d)}
          onOpen={(id) => navigate(`/studies/${id}`)}
        />
      )}
    </>
  )
}
