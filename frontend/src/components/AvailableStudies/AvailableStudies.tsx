import { useState } from 'react';
import SelectBox from '@/components/SelectBox/SelectBox';
import type { AvailableStudy } from '@/types/study';
import s from './AvailableStudies.module.css';

interface Props {
  items: AvailableStudy[];
  isLoading?: boolean;
  onPick: (study: AvailableStudy) => void;
}

export default function AvailableStudies({ items, isLoading = false, onPick }: Props) {
  const [pickedId, setPickedId] = useState<number | null>(null);

  const handleSelect = (id: number) => {
    const study = items.find((i) => i.id === id);
    if (!study) return;
    setPickedId(id);
    onPick(study);
  };

  return (
    <div className={s.wrap}>
      <span className={s.label}>Доступные исследования пациента</span>
      <SelectBox
        items={items}
        selectedId={pickedId}
        isLoading={isLoading}
        placeholder="Подставить заключение из исследования"
        getLabel={(i) => i.title}
        onSelect={handleSelect}
      />
    </div>
  );
}