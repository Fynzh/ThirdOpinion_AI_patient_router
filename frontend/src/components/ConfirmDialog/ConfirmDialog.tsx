import { useEffect, useRef } from 'react';
import type { ReactNode } from 'react';
import s from './ConfirmDialog.module.css';

export type ConfirmVariant = 'danger' | 'warning' | 'info';

interface Props {
  open: boolean;
  title: string;
  message?: ReactNode;
  variant?: ConfirmVariant;
  confirmText?: string;
  cancelText?: string;
  isLoading?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}

const ICONS: Record<ConfirmVariant, string> = {
  danger: '!',
  warning: '!',
  info: 'i',
};

export default function ConfirmDialog({
  open,
  title,
  message,
  variant = 'info',
  confirmText = 'Подтвердить',
  cancelText = 'Отмена',
  isLoading = false,
  onConfirm,
  onCancel,
}: Props) {
  const ref = useRef<HTMLDialogElement>(null);

  useEffect(() => {
    const dialog = ref.current;
    if (!dialog) return;
    if (open && !dialog.open) dialog.showModal();
    if (!open && dialog.open) dialog.close();
  }, [open]);

  const cancel = () => {
    if (!isLoading) onCancel();
  };

  return (
    <dialog
      ref={ref}
      className={`${s.dialog} ${s[variant]}`}
      onCancel={(e) => {
        e.preventDefault();
        cancel();
      }}
      onClick={(e) => {
        if (e.target === e.currentTarget) cancel();
      }}
    >
      <div className={s.body}>
        <div className={s.head}>
          <span className={s.icon} aria-hidden="true">{ICONS[variant]}</span>
          <h2 className={s.title}>{title}</h2>
        </div>

        {message && <div className={s.message}>{message}</div>}

        <div className={s.actions}>
          <button type="button" className={`${s.btn} ${s.cancel}`} disabled={isLoading} onClick={cancel}>
            {cancelText}
          </button>
          <button type="button" className={`${s.btn} ${s.confirm}`} disabled={isLoading} onClick={onConfirm}>
            {isLoading ? 'Подождите…' : confirmText}
          </button>
        </div>
      </div>
    </dialog>
  );
}