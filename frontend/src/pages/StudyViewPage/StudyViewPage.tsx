import { useSearchParams } from 'react-router-dom';
import s from './StudyViewPage.module.css'

export default function StudyViewPage() {
    const [searchParams] = useSearchParams();
    const patientId = searchParams.get('id');
    return (
        <>
            <h1 className={s.title}>Просмотр исследования: {patientId}</h1>
        </>
    );
}