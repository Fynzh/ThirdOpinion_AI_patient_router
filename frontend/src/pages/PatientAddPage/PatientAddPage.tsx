import { useState } from "react";
import PatientSelect from "@/components/PatientSelect/PatientSelect";
import { usePatients } from "@/hooks/usePatients";
import { getPatientLabel } from "@/utils/patientLabel";
import s from "./PatientAddPage.module.css";

export default function PatientAddPage() {
  const { patients, isLoading, error } = usePatients();
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [isCreatingNew, setIsCreatingNew] = useState(false);
  const selectedPatient = patients?.find((p) => p.id === selectedId);

  const handleSelect = (id: number) => {
    setSelectedId(id);
    setIsCreatingNew(false);
  };
  const handleCreateNew = () => {
    setSelectedId(null);
    setIsCreatingNew(true);
  };

  return (
    <>
      <h1 className={s.title}>Добавление пациентов</h1>

      {error && <p role="alert">{error.message}</p>}

      <PatientSelect
        patients={patients}
        selectedId={selectedId}
        isCreatingNew={isCreatingNew}
        isLoading={isLoading}
        onSelect={handleSelect}
        onCreateNew={handleCreateNew}
      />

      {isCreatingNew && <div>Здесь будет модуль добавления пациента</div>}
      {selectedPatient && (
        <p>{getPatientLabel(selectedPatient.id, selectedPatient.patient_code)}</p>
      )}
    </>
  );
}
