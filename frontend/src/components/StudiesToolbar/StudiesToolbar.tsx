import { useNavigate } from 'react-router-dom';
import s from './StudiesToolbar.module.css';

interface StudiesToolbarProps {
    isEditing: boolean;
    onToggleEditing: () => void;
}

export default function StudiesToolbar({ isEditing, onToggleEditing }: StudiesToolbarProps) {
    const navigate = useNavigate();
    
    return (
    <div className={s.toolbar}>
        {!isEditing && <button type='button'
            className={`${s.button} ${s.modif}`}
            onClick={onToggleEditing}
            >
            Управление
            </button>}
        <span className={s.modif_menu}>
        {isEditing && <button type='button'
            className={`${s.button} ${s.save}`}
            onClick={onToggleEditing}
            >
            Сохранить
            </button>}
        {isEditing && <button type='button'
            className={`${s.button} ${s.undo}`}
            onClick={onToggleEditing}
            >
            Отменить изменения
            </button>}
        </span>
        <button type='button' className={`${s.button} ${s.upload}`} onClick={() => navigate('/study/add')}>Новый пациент</button>
    </div>
  );
}