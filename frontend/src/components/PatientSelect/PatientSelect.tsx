import type { Patient } from '@/types/patient';
import SelectBox from '@/components/SelectBox/SelectBox'; // Импортируем наш универсальный селект

interface PatientSelectProps {
  patients: Patient[];
  selectedId: string | null;
  isCreatingNew: boolean;
  isLoading?: boolean;
  onSelect: (id: string) => void;
  onCreateNew: () => void;
}

export default function PatientSelect({
  patients,
  selectedId,
  isCreatingNew,
  isLoading = false,
  onSelect,
  onCreateNew,
}: PatientSelectProps) {
  
  return (
    <SelectBox<Patient> // Явно указываем тип данных
      items={patients}
      selectedId={selectedId}
      isLoading={isLoading}
      placeholder={isCreatingNew ? 'Новый пациент' : 'Выберите пациента'}
      getLabel={(patient) => patient.fullName} // Указываем, как читать имя
      onSelect={onSelect}
      actionButton={{
        label: 'Новый пациент',
        icon: '+',
        onClick: onCreateNew,
      }}
    />
  );
}
