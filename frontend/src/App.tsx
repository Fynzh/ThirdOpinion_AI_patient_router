import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import Layout from './components/Layout'
import StudiesPage from './pages/StudiesPage'
import StudyDetailPage from './pages/StudyDetailPage'
import './styles/components.css'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<Navigate to="/studies" replace />} />
          <Route path="/studies" element={<StudiesPage />} />
          <Route path="/studies/:id" element={<StudyDetailPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
