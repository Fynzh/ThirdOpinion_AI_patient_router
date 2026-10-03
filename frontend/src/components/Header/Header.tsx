import { Link, NavLink } from 'react-router-dom';
import logo from '@/assets/logo.svg'
import s from './Header.module.css';

export default function Header() {
  return (
    <header className={s.header}>
      <Link to="/studies" className={s.logoLink} aria-label='На главную'>
        <img src={logo} alt="" className={s.logo} />
      </Link>

      <nav className={s.nav}>
        <NavLink
          to="/studies"
          className={({ isActive }) => `${s.link} ${isActive ? s.active : ''}`}
        >
          Маршрутизация
        </NavLink>
      </nav>

      <NavLink to="/profile" className={s.user} >
        ИФ
      </NavLink>
      
    </header>
  );
}