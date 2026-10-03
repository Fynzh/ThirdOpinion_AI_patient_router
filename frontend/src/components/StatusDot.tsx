import type { StudyStatus } from '../types'

// Цвет точки зависит от статуса исследования
const DOT_COLOR: Record<StudyStatus, string> = {
  new: 'gray', // ждёт обработки ИИ
  ai_done: 'pink', // ИИ закончил, ждёт врача — требует внимания
  in_review: 'amber', // врач проверяет
  approved: 'green', // план утверждён
  sent: 'teal', // отправлено пациенту
}

interface Props {
  status: StudyStatus
  label: string // подпись приходит с бэкенда (status_display)
}

export default function StatusDot({ status, label }: Props) {
  return (
    <span className="status">
      <span className={`status__dot status__dot--${DOT_COLOR[status]}`} aria-hidden="true" />
      {label}
    </span>
  )
}
