import { createBrowserRouter, redirect } from 'react-router-dom';
import MainLayout from '@/layouts/MainLayout/MainLayout';
import StudiesPage from '@/pages/StudiesPage/StudiesPage';
import ProfilePage from '@/pages/ProfilePage/ProfilePage';
import PatientAddPage from '@/pages/PatientAddPage/PatientAddPage';
import PatientViewPage from '@/pages/PatientViewPage/PatientViewPage';
import LoginPage from '@/pages/LoginPage/LoginPage';
import { getToken } from '@/api/token';

const requireAuth = () => (getToken() ? null : redirect('/login'));
const redirectIfAuth = () => (getToken() ? redirect('/studies') : null);

export const router = createBrowserRouter([
  { path: 'login', element: <LoginPage />, loader: redirectIfAuth },
  {
    element: <MainLayout />,
    loader: requireAuth,
    children: [
      { index: true, loader: () => redirect('/studies') },
      { path: 'studies', element: <StudiesPage /> },
      {
        path: 'patient',
        children: [
          {index: true, loader: () => redirect('/studies')},
          {path: 'add', element: <PatientAddPage />},
          {path: 'view', element: <PatientViewPage />},
        ],
      },
      { path: 'profile', element: <ProfilePage /> },
      { path: '*', loader: () => redirect('/studies') },
    ],
  },
]);