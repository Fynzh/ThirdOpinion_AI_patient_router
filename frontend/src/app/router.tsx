import { createBrowserRouter, redirect } from 'react-router-dom';
import MainLayout from '@/layouts/MainLayout/MainLayout';
import StudiesPage from '@/pages/StudiesPage/StudiesPage';
import ProfilePage from '@/pages/ProfilePage/ProfilePage';
import PatientAddPage from '@/pages/PatientAddPage/PatientAddPage';
import PatientViewPage from '@/pages/PatientViewPage/PatientViewPage';

export const router = createBrowserRouter([
  {
    element: <MainLayout />,
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