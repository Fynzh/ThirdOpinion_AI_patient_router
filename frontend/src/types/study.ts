export type StudyStatus = 'pathology_found' | 'no_pathology' | 'processing';

export interface Study {
    id: string;
    patientId: string;
    sex: "F" | "M";
    age: number;
    title: string;
    status: StudyStatus;
    studyDate: string;
    uploadedAt: string;
    slicesCount: number;
}