import { NavLink } from 'react-router-dom';
import s from './StudiesToolbar.module.css';

export default function StudiesToolbar() {
  return (
    <div className={s.toolbar}>
      <NavLink to="/upload" className={s.upload}>Загрузить новый</NavLink>
    </div>
  );
}