import type { PatientSummary } from "@/types/patient";
import { getPatientLabel } from "@/utils/patientLabel";
import SelectBox from "@/components/SelectBox/SelectBox"; // Импортируем наш универсальный селект

interface PatientSelectProps {
  patients: PatientSummary[];
  selectedId: number | null;
  isCreatingNew: boolean;
  isLoading?: boolean;
  onSelect: (id: number) => void;
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
    <SelectBox
      items={patients}
      selectedId={selectedId}
      isLoading={isLoading}
      placeholder={isCreatingNew ? "Новый пациент" : "Выберите пациента"}
      getLabel={getPatientLabel} // Указываем, как читать имя
      onSelect={onSelect}
      actionButton={{
        label: "Новый пациент",
        icon: "+",
        onClick: onCreateNew,
      }}
    />
  );
}
