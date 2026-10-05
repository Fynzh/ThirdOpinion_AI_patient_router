import { useState } from 'react';
import StudiesToolbar from '@/components/StudiesToolbar/StudiesToolbar';
import StudiesTable from '@/components/StudiesTable/StudiesTable';
import { useStudies } from '@/hooks/useStudies';
import s from './StudiesPage.module.css';

export default function StudiesPage() {
  const { studies, isLoading, error } = useStudies();
  const [isEditing, setIsEditing] = useState(false);
  const [selectedIds, setSelectedIds] = useState<number[]>([]);
  
  const toggleSelected = (id: number) =>
    setSelectedIds((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]));

  const handleToggleEditing = () => {
    if (isEditing) setSelectedIds([]);
    setIsEditing((prev) => !prev);
  };
    return (
    <>
        <h2 className={s.title}>Маршрутизация пациентов</h2>
        <StudiesToolbar isEditing={isEditing} onToggleEditing={handleToggleEditing}/>
        {error && <p role="alert">{error.message}</p>}
        {isLoading ? (
          <p>Загрузка…</p>
        ) : (
          <StudiesTable
            studies={studies}
            isEditing={isEditing}
            selectedIds={selectedIds}
            onToggleSelect={toggleSelected}
          />
        )}
    </>
  );
}
