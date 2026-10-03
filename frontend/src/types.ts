// Типы повторяют ответ бэкенда (StudyListSerializer, GET /api/studies/).
// Названия полей должны совпадать с бэкендом буква в букву.

export type StudyStatus = 'new' | 'ai_done' | 'in_review' | 'approved' | 'sent'

export type Modality = 'CHEST_XRAY' | 'FLG' | 'CHEST_CT' | 'BRAIN_CT' | 'MAMMO'

export interface StudyListItem {
  id: number
  patient: number
  patient_code: string | null // анонимный код, на бэке может быть пустым
  modality: Modality
  modality_display: string // готовая подпись, например «Маммограмма»
  study_date: string // 'YYYY-MM-DD'
  status: StudyStatus
  status_display: string // готовая подпись статуса
  recommendations_count: number
  created_at: string // ISO-дата со временем
}
