import { Outlet } from 'react-router-dom';
import Header from '@/components/Header/Header';
import s from './MainLayout.module.css';

export default function MainLayout() {
  return (
    <div className={s.page}>
      <Header />
      <main className={s.container}>
        <Outlet />
      </main>
    </div>
  );
}