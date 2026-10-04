import { useState } from 'react';
import type { FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { login, register } from '@/api/auth';
import s from './LoginPage.module.css';

type Mode = 'login' | 'register';

export default function LoginPage() {
  const navigate = useNavigate();
  const [mode, setMode] = useState<Mode>('login');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [email, setEmail] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      if (mode === 'login') await login({ username, password });
      else await register({ username, password, email });
      navigate('/studies', { replace: true });
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const toggleMode = () => {
    setMode((m) => (m === 'login' ? 'register' : 'login'));
    setError(null);
  };

  return (
    <div className={s.wrapper}>
      <form className={s.card} onSubmit={submit}>
        <h1 className={s.title}>{mode === 'login' ? 'Вход' : 'Регистрация'}</h1>

        <input
          className={s.input}
          placeholder="Логин"
          autoComplete="username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
        />
        {mode === 'register' && (
          <input
            className={s.input}
            type="email"
            placeholder="Email (необязательно)"
            autoComplete="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        )}
        <input
          className={s.input}
          type="password"
          placeholder="Пароль"
          autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />

        {error && <p className={s.error} role="alert">{error}</p>}

        <button className={s.submit} type="submit" disabled={busy || !username || !password}>
          {mode === 'login' ? 'Войти' : 'Зарегистрироваться'}
        </button>

        <button className={s.link} type="button" onClick={toggleMode}>
          {mode === 'login' ? 'Нет аккаунта? Зарегистрироваться' : 'Уже есть аккаунт? Войти'}
        </button>
      </form>
    </div>
  );
}