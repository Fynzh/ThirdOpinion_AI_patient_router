import { createBrowserRouter, redirect } from 'react-router-dom';
import MainLayout from '@/layouts/MainLayout/MainLayout';
import StudiesPage from '@/pages/StudiesPage/StudiesPage';
import ProfilePage from '@/pages/ProfilePage/ProfilePage';

export const router = createBrowserRouter([
  {
    element: <MainLayout />,
    children: [
      { index: true, loader: () => redirect('/studies') },
      { path: 'studies', element: <StudiesPage /> },
      { path: 'profile', element: <ProfilePage /> },
      { path: '*', loader: () => redirect('/studies') },
    ],
  },
]);