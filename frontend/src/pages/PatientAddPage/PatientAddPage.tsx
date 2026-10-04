import { useState } from "react";
import PatientSelect from "@/components/PatientSelect/PatientSelect";
import { usePatients } from "@/hooks/usePatients";
import s from "./PatientAddPage.module.css";

export default function PatientAddPage() {
  const { patients, isLoading, error } = usePatients();
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [isCreatingNew, setIsCreatingNew] = useState(false);
  const selectedPatient = patients?.find((p) => p.id === selectedId);

  const handleSelect = (id: string) => {
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
      {selectedId && <p>{selectedPatient?.fullName}</p>}
    </>
  );
}
