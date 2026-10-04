import type { Study } from '@/types/study'

export const mockStudies: Study[] = [
    {
        id: '1', patientId: 'Демо', sex: 'F', age: 42,
        title: 'Подозрительное образование', status: 'pathology_found',
        studyDate: '2022-09-27T14:06:00', uploadedAt: '2026-05-21T15:09:00', slicesCount: 16,
    },
    {
        id: '2', patientId: 'Демо', sex: 'F', age: 60,
        title: 'Доброкачественное образование', status: 'no_pathology',
        studyDate: '2014-02-17T07:50:00', uploadedAt: '2026-05-21T14:55:00', slicesCount: 16,
    },
    {
        id: '3', patientId: 'Демо', sex: 'F', age: 44,
        title: 'Кальцинаты подозрительные', status: 'pathology_found',
        studyDate: '2023-08-02T20:09:00', uploadedAt: '2026-05-21T14:40:00', slicesCount: 16,
    },
]