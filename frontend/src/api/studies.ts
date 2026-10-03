import type { StudyListItem } from '../types'

// true — читаем демо-данные из public/studies.json (бэкенд не нужен)
// false — ходим на настоящий бэкенд. Меняется в одном месте.
const USE_MOCK = true

export async function fetchStudies(): Promise<StudyListItem[]> {
  const url = USE_MOCK ? '/studies.json' : '/api/studies/' // у Django слэш в конце обязателен
  const response = await fetch(url)
  if (!response.ok) throw new Error('Не удалось загрузить список исследований')
  const data = await response.json()
  // Бэкенд может отдать массив или объект с пагинацией { results: [...] }
  return Array.isArray(data) ? data : data.results
}
