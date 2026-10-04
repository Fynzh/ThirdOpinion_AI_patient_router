import { createBrowserRouter, redirect } from 'react-router-dom';
import MainLayout from '@/layouts/MainLayout/MainLayout';
import StudiesPage from '@/pages/StudiesPage/StudiesPage';
import ProfilePage from '@/pages/ProfilePage/ProfilePage';
import StudyAddPage from '@/pages/StudyAddPage/StudyAddPage';
import StudyPage from '@/pages/StudyPage/StudyPage';

export const router = createBrowserRouter([
  {
    element: <MainLayout />,
    children: [
      { index: true, loader: () => redirect('/studies') },
      { path: 'studies', element: <StudiesPage />},
      { path: 'studies/view', element: <StudyPage />},
      {
        path: 'study',
        children: [
          {index: true, loader: () => redirect('/studies')},
          {path: 'add', element: <StudyAddPage />},
        ],
      },
      { path: 'profile', element: <ProfilePage /> },
      { path: '*', loader: () => redirect('/studies') },
    ],
  },
]);