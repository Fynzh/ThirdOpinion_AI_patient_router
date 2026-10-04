import { useEffect, useId, useRef, useState } from 'react';
import type { ReactNode } from 'react';
import s from './TextBox.module.css';

interface Props {
  title?: string;
  children: ReactNode;
  /** Высота (px) в свёрнутом состоянии */
  collapsedHeight?: number;
  defaultExpanded?: boolean;
}

export default function TextBox({
  title,
  children,
  collapsedHeight = 140,
  defaultExpanded = false,
}: Props) {
  const contentId = useId();
  const contentRef = useRef<HTMLDivElement>(null);
  const [fullHeight, setFullHeight] = useState(0);
  const [expanded, setExpanded] = useState(defaultExpanded);
  const [animate, setAnimate] = useState(false);

  useEffect(() => {
    const el = contentRef.current;
    if (!el) return;
    const observer = new ResizeObserver(() => setFullHeight(el.scrollHeight));
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  const collapsible = fullHeight > collapsedHeight + 8;
  const isCollapsed = collapsible && !expanded;
  const maxHeight = expanded ? fullHeight || undefined : collapsedHeight;

  const toggle = () => {
    setAnimate(true);
    setExpanded((v) => !v);
  };

  return (
    <div className={s.box}>
      {title && (
        <div className={s.header}>
          <h3 className={s.title}>{title}</h3>
        </div>
      )}

      <div
        className={`${s.viewport} ${animate ? s.animated : ''}`}
        style={{ maxHeight }}
      >
        <div id={contentId} ref={contentRef} className={s.content}>
          {children}
        </div>
        <div className={`${s.fade} ${isCollapsed ? s.fadeVisible : ''}`} />
      </div>

      {collapsible && (
        <button
          type="button"
          className={s.toggle}
          onClick={toggle}
          aria-expanded={expanded}
          aria-controls={contentId}
          aria-label={expanded ? 'Свернуть' : 'Показать полностью'}
        >
          <svg
            className={`${s.arrow} ${expanded ? s.arrowUp : ''}`}
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            aria-hidden="true"
          >
            <polyline points="6 9 12 15 18 9" />
          </svg>
        </button>
      )}
    </div>
  );
}