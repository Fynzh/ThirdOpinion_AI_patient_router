import { useSearchParams } from 'react-router-dom';
import s from './PatientViewPage.module.css'

export default function PatientViewPage() {
    const [searchParams] = useSearchParams();
    const patientId = searchParams.get('id');
    return (
        <>
            <h1 className={s.title}>просмотр пациента с айди: {patientId}</h1>
        </>
    );
}