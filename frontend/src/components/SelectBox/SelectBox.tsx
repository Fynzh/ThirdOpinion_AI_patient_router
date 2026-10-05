import { useState, useRef, useEffect, type ReactNode } from 'react';
import s from './SelectBox.module.css'; // Общие стили для всех селектов

// Описываем требования к структуре данных: у каждого элемента должен быть как минимум id
interface BaseItem {
  id: number;
}

interface SelectProps<T extends BaseItem> {
  items: T[];
  selectedId: number | null;
  placeholder?: string;
  isLoading?: boolean;
  // Функция, которая скажет селекту, какое поле объекта выводить как текст
  getLabel: (item: T) => string; 
  onSelect: (id: number) => void;
  // Дополнительная кнопка действия внизу (опционально)
  actionButton?: {
    label: string;
    onClick: () => void;
    icon?: ReactNode;
  };
}

export default function SelectBox<T extends BaseItem>({
  items,
  selectedId,
  placeholder = 'Выберите значение',
  isLoading = false,
  getLabel,
  onSelect,
  actionButton,
}: SelectProps<T>) {
  const [isOpen, setIsOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!isOpen) return;
    const handleMouseDown = (e: MouseEvent) => {
      if (!rootRef.current?.contains(e.target as Node)) setIsOpen(false);
    };
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setIsOpen(false);
    };
    document.addEventListener('mousedown', handleMouseDown);
    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('mousedown', handleMouseDown);
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [isOpen]);

  const selectedItem = items.find((item) => item.id === selectedId);
  const currentLabel = selectedItem ? getLabel(selectedItem) : placeholder;

  const handleItemClick = (id: number) => {
    onSelect(id);
    setIsOpen(false);
  };

  const handleActionClick = () => {
    if (actionButton) {
      actionButton.onClick();
      setIsOpen(false);
    }
  };

  return (
    <div className={s.root} ref={rootRef}>
      <button
        type="button"
        className={s.trigger}
        aria-haspopup="true"
        aria-expanded={isOpen}
        disabled={isLoading}
        onClick={() => setIsOpen((prev) => !prev)}
      >
        <span>{isLoading ? 'Загрузка…' : currentLabel}</span>
        <span className={`${s.arrow} ${isOpen ? s.arrowOpen : ''}`} aria-hidden="true">▾</span>
      </button>

      {isOpen && (
        <div className={s.dropdown}>
          <ul className={s.list}>
            {items.length === 0 && <li className={s.empty}>Список пуст</li>}
            {items.map((item) => (
              <li key={item.id}>
                <button
                  type="button"
                  className={`${s.option} ${item.id === selectedId ? s.optionActive : ''}`}
                  onClick={() => handleItemClick(item.id)}
                >
                  {getLabel(item)}
                </button>
              </li>
            ))}
          </ul>

          {actionButton && (
            <button type="button" className={s.actionButton} onClick={handleActionClick}>
              {actionButton.icon && <span className={s.aBicon} aria-hidden="true">{actionButton.icon}</span>}
              {actionButton.label}
            </button>
          )}
        </div>
      )}
    </div>
  );
}
