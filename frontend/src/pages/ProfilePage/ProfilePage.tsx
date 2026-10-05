import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { logout } from '@/api/auth';
import ConfirmDialog from '@/components/ConfirmDialog/ConfirmDialog';
import { useCurrentUser } from '@/hooks/useCurrentUser';
import { getInitials } from '@/utils/initials';
import s from './ProfilePage.module.css';

export default function ProfilePage() {
  const navigate = useNavigate();
  const { user, isLoading, error } = useCurrentUser();
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [isLoggingOut, setIsLoggingOut] = useState(false);

  const handleLogout = async () => {
    setIsLoggingOut(true);
    await logout();
    navigate('/login', { replace: true });
  };

  if (isLoading) return <p className={s.state}>Загрузка…</p>;
  if (error) return <p className={s.error} role="alert">{error.message}</p>;
  if (!user) return null;

  const role = user.is_superuser ? 'Администратор' : user.is_staff ? 'Персонал' : 'Доктор';

  return (
    <div className={s.wrapper}>
      <section className={s.card}>
        <div className={s.top}>
          <div className={s.avatar}>{getInitials(user.username)}</div>
          <h1 className={s.name}>{user.username}</h1>
          <span className={s.badge}>{role}</span>
        </div>

        <dl className={s.list}>
          <div className={s.row}>
            <dt>Логин</dt>
            <dd>{user.username}</dd>
          </div>
          <div className={s.row}>
            <dt>Email</dt>
            <dd>{user.email || '—'}</dd>
          </div>
        </dl>

        <button type="button" className={s.logout} onClick={() => setConfirmOpen(true)}>
          <svg
            className={s.icon}
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            aria-hidden="true"
          >
            <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
            <polyline points="16 17 21 12 16 7" />
            <line x1="21" y1="12" x2="9" y2="12" />
          </svg>
          Выйти
        </button>
      </section>

      <ConfirmDialog
        open={confirmOpen}
        variant="danger"
        title="Выйти из аккаунта?"
        message="Чтобы продолжить работу, потребуется снова войти."
        confirmText="Выйти"
        isLoading={isLoggingOut}
        onConfirm={handleLogout}
        onCancel={() => setConfirmOpen(false)}
      />
    </div>
  );
}