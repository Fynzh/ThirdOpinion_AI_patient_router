import { Link, useParams } from 'react-router-dom'

// Заглушка: сюда придёт экран деталей (заключение + рекомендации)
export default function StudyDetailPage() {
  const { id } = useParams()
  return (
    <>
      <Link to="/studies">← К списку</Link>
      <h1 className="page-title">Исследование № {id}</h1>
    </>
  )
}
