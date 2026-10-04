import StudiesToolbar from "@/components/StudiesToolbar/StudiesToolbar";
import s from "./StudiesPage.module.css";
import { useState } from "react";
import StudiesTable from "@/components/StudiesTable/StudiesTable";
import { mockStudies } from "@/api/studies";

export default function StudiesPage() {
  const [isEditing, setIsEditing] = useState(false)
    return (
    <>
        <h2 className={s.title}>Маршрутизация пациентов</h2>
        <StudiesToolbar isEditing={isEditing} onToggleEditing={() => setIsEditing((p) => !p)}/>
        <StudiesTable studies={mockStudies}/>
    </>
  );
}
