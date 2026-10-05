import { Link, NavLink } from "react-router-dom";
import logo from "@/assets/logo.svg";
import logoSmall from "@/assets/logo_small.svg";
import { useCurrentUser } from "@/hooks/useCurrentUser";
import { getInitials } from "@/utils/initials";
import s from "./Header.module.css";

export default function Header() {
  const { user } = useCurrentUser();  
  return (
    <header className={s.header}>
      <Link to="/studies" className={s.logoLink} aria-label="На главную">
        <picture>
          <source media="(max-width: 600px)" srcSet={logoSmall} />
          <img src={logo} alt="" className={s.logo} />
        </picture>
      </Link>

      <nav className={s.nav}>
        <NavLink
          to="/studies"
          className={({ isActive }) => `${s.link} ${isActive ? s.active : ""}`}
        >
          Маршрутизация
        </NavLink>
      </nav>
      <NavLink
        to="/profile"
        title={user?.username}
        className={({ isActive }) => `${s.user} ${isActive ? s.profileActive : ''}`}
      >
        {user ? getInitials(user.username) : '··'}
      </NavLink>
    </header>
  );
}
