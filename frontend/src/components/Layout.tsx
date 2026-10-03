import { Link, Outlet } from 'react-router-dom'

// Общая рамка страниц: шапка + место для текущей страницы (Outlet)
export default function Layout() {
  return (
    <>
      <header className="layout__header">
        <Link to="/studies" className="layout__logo">
          Маршрутизация
        </Link>
      </header>
      <main className="layout__main">
        <Outlet />
      </main>
    </>
  )
}
