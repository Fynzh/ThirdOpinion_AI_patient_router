import { useNavigate } from 'react-router-dom';
import { fetchMe, logout } from '@/api/auth';
import { useFetch } from '@/hooks/useFetch';
import type { CurrentUser } from '@/types/auth';

export default function ProfilePage() {
  const navigate = useNavigate();
  const { data: user, isLoading, error } = useFetch<CurrentUser | null>(fetchMe, null);

  const handleLogout = async () => {
    await logout();
    navigate('/login', { replace: true });
  };

  if (isLoading) return <p>Загрузка…</p>;
  if (error) return <p role="alert">{error.message}</p>;

  return (
    <>
      <h1>Профиль</h1>
      {user && (
        <p>
          {user.username}
          {user.email && ` · ${user.email}`}
        </p>
      )}
      <button type="button" onClick={handleLogout}>Выйти</button>
    </>
  );
}