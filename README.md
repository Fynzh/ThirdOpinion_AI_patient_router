**Акведук - ML-сервис маршрутизации пациента после ИИ-анализа КТ, рентгена и маммографии:**
по заключению ИИ определяет следующий шаг (повторный приём, консультация специалиста,
дообследование) и помогает записаться.

> Проект создан командой **«cord доступа»** в рамках хакатона **MedITron 2026**
> по кейсу компании **«Третье Мнение»**.
> **Статус:** в разработке.

---

## 📋 О проекте

Платформа «Третье Мнение» с помощью собственной нейросети анализирует рентген-изображения
и формирует заключение. **Наш сервис** берёт это заключение и **превращает его
в конкретное действие** — маршрут пациента: к каким специалистам обратиться.

**Ключевая особенность** — принцип **human-in-the-loop**: врач **обязательно проверяет**
рекомендации ИИ, может их изменить, одобрить или отклонить. Только после проверки план
автоматически отправляется пациенту на email с кнопкой записи.

### Решаемая проблема

Пациент проходит исследование, получает заключение — и **не записывается** к врачу.
Клиника теряет пациента. Наш сервис **закрывает этот разрыв**: превращает
заключение в конкретный следующий шаг.

### Бизнес-ценность

- **Ускорение работы врача** — 30 секунд вместо 5 минут на пациента.
- **Снижение риска медицинской ошибки** — ИИ + обязательная проверка врачом.
- **Повышение конверсии** в повторный приём — пациент получает понятный маршрут
  с кнопкой записи в один клик.

---

## 🎯 Цели и задачи

- Превратить заключение ИИ в конкретное действие для пациента и сотрудника клиники.
- Снизить долю пациентов, которые прерывают лечение или не возвращаются на приём.
- Показать схему интеграции сервиса в контур клиники (МИС/РИС, сайт, приложение).

---

## 🏗️ Архитектура
┌─────────────────────────────────────────────────────────────┐
│ Платформа «Третье Мнение» │
│ (формирует заключение по КТ/рентгену/маммографии) │
└────────────────────────┬────────────────────────────────────┘
│
▼
┌─────────────────────────────────────────────────────────────┐
│ ThirdOpinion AI Patient Router (Django + DRF) │
│ │
│ • Study — исследование с заключением │
│ • GigaChat — NLP-анализ заключения │
│ • Recommendation — рекомендации от ИИ │
│ • CarePlan — итоговый план, отправляется пациенту │
│ │
│ Human-in-the-loop: врач одобряет / меняет / отклоняет │
└────────────────────────┬────────────────────────────────────┘
│
▼
┌─────────────────────────────────────────────────────────────┐
│ Email пациенту: план + заключение + файл + кнопка записи │
└─────────────────────────────────────────────────────────────┘

text

---

## ✅ Что реализовано

### Backend

- **REST API** на Django + Django REST Framework.
- **Аутентификация** по токенам (`/api/auth/register/`, `/api/auth/login/`, `/api/auth/logout/`).
- **Интеграция с GigaChat-3-Lightning** для анализа заключений.
- **Автоматический запуск ИИ-анализа** при создании исследования (Django signals).
- **Автосоздание плана обращения** при проверке всех рекомендаций врачом.
- **Кастомизированная админка** для врача (кнопки «Одобрить» / «Отклонить», вложенные таблицы).
- **Отправка email** через Gmail SMTP с вложением файла исследования.
- **Swagger-документация** API (`/api/docs/`).
- **Анонимизация персональных данных** — ФИО хранятся в отдельном JSON-реестре,
  в GigaChat уходят только возраст и пол.

### ML / NLP

- **Отдельный модуль `nlp_module/`**, не привязанный к Django.
- **Защита от prompt-инъекций** — заключение обёрнуто в маркеры.
- **Валидация ответа модели** по белым спискам специальностей.
- **Починка битого JSON** — повторный запрос к LLM при ошибке парсинга.
- **Нормализация полей** — `confidence` обрезается до [0.0, 1.0].

### Frontend

- _В разработке. См. каталог `frontend/`._

---

## 🛠️ Технологический стек

| Компонент | Технология |
|-----------|-----------|
| **Backend** | Python 3.14, Django 6.1, Django REST Framework 3.18 |
| **NLP** | GigaChat-3-Lightning (Sber) |
| **Аутентификация** | DRF Token Authentication |
| **Документация API** | drf-spectacular (OpenAPI 3.0 / Swagger) |
| **База данных** | SQLite (dev) / PostgreSQL (prod) |
| **Email** | SMTP (Gmail) |
| **Frontend** | React (в разработке) |
| **Инфраструктура** | Docker, Docker Compose |

---

## 🚀 Быстрый старт

Требования: **Docker** и **Docker Compose**.

```bash
git clone git@github.com:Fynzh/ThirdOpinion_AI_patient_router.git
cd ThirdOpinion_AI_patient_router
cp .env.example .env
docker compose up --build
После запуска:

Интерфейс: http://localhost:3000

API и документация: http://localhost:8000/docs

Запуск без Docker (для backend-разработки)
bash
cd backend/app

# 1. Создать и активировать venv
python3 -m venv venv
source venv/bin/activate          # Linux/macOS
# venv\Scripts\activate           # Windows

# 2. Установить зависимости
pip install -r requirements.txt

# 3. Создать файл .env (см. раздел «Переменные окружения»)
cp .env.example .env
# отредактировать .env — вписать свои ключи

# 4. Применить миграции
python manage.py migrate

# 5. Создать администратора
python manage.py createsuperuser

# 6. Запустить сервер
python manage.py runserver
🔐 Переменные окружения (.env)
Файл .env создаётся в backend/app/ (там, где manage.py).
Не коммитится в Git — добавлен в .gitignore.

dotenv
# ============================================
# GigaChat (Sber)
# ============================================
GIGACHAT_KEY=ваш_ключ_от_GigaChat

# ============================================
# Email (Gmail SMTP)
# ============================================
# Для отправки через Gmail нужен «пароль приложения»
# https://myaccount.google.com/apppasswords
EMAIL_HOST_USER=ваш_email@gmail.com
EMAIL_HOST_PASSWORD=16_символьный_пароль_приложения
Как получить ключи
GigaChat:

Зарегистрироваться на https://developers.sber.ru/

Получить ключ с scope GIGACHAT_API_PERS.

Gmail:

Включить двухфакторную аутентификацию в аккаунте Google.

Создать «пароль приложения» на https://myaccount.google.com/apppasswords.

Использовать 16-символьный пароль (без пробелов) в .env.

📡 API Endpoints
Все эндпоинты защищены токен-авторизацией. Требуют заголовок:

text
Authorization: Token <ваш_токен>
Авторизация
Метод	Endpoint	Описание
POST	/api/auth/register/	Регистрация нового пользователя
POST	/api/auth/login/	Получить токен
POST	/api/auth/logout/	Удалить токен
GET	/api/auth/me/	Данные текущего пользователя
Исследования
Метод	Endpoint	Описание
GET	/api/studies/	Список исследований
GET	/api/studies/{id}/	Детали исследования + рекомендации + план
POST	/api/studies/{id}/generate/	Запустить ИИ-анализ (перегенерация)
POST	/api/studies/{id}/add-recommendation/	Врач добавляет свою рекомендацию
PATCH	/api/studies/{id}/care-plan/	Обновить комментарий врача к плану
POST	/api/studies/{id}/send/	Отправить план пациенту на email
Рекомендации
Метод	Endpoint	Описание
PATCH	/api/recommendations/{id}/edit/	Изменить рекомендацию
POST	/api/recommendations/{id}/approve/	Одобрить
POST	/api/recommendations/{id}/reject/	Отклонить
Пример: получение токена
bash
curl -X POST http://127.0.0.1:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "doctor1", "password": "secret123"}'
Ответ:

json
{
    "token": "e24357e6316a1e7842dceaaf36d1d13efb07006b",
    "user": {"id": 2, "username": "doctor1", "email": "doctor@test.com"}
}
Пример: список исследований
bash
curl http://127.0.0.1:8000/api/studies/ \
  -H "Authorization: Token e24357e6316a1e7842dceaaf36d1d13efb07006b"
📥 Входные и выходные данные
Входные данные — объект Study
Создаётся через админку или API. Соответствует структуре исследования
платформы «Третье Мнение»:

Поле	Тип	Описание
patient	FK → Patient	Пациент (анонимный)
modality	choices	Тип исследования (КТ ОГК, маммография, ФЛГ, ...)
title	str	Краткое название («Очаг в легком», «Коронарный кальциноз»)
study_date	date	Дата исследования
slices_count	int	Количество срезов (для КТ/МРТ)
radiologist_conclusion	text	Заключение платформы «Третье Мнение»
file	file	Файл серии (DICOM/PDF)
Выходные данные — Recommendation и CarePlan
Recommendation — рекомендация от ИИ или врача:

Поле	Тип	Описание
specialist	str	Название специальности («онколог»)
specialty_code	str	Код (ONCO)
reasoning	text	Обоснование (со ссылкой на заключение)
priority	choices	high / medium / low
confidence	float	Уверенность ИИ (0.0–1.0)
source	choices	ai / doctor
status	choices	pending / approved / rejected
CarePlan — итоговый план обращения, отправляется пациенту:

Поле	Тип	Описание
study	FK → Study	Связанное исследование
recommendations_snapshot	JSON	Снимок одобренных рекомендаций
doctor_comment	text	Комментарий врача к плану
status	choices	draft / sent
sent_at	datetime	Дата отправки пациенту
Пример JSON от GigaChat
json
{
    "status": "findings",
    "recommendations": [
        {
            "specialist": "онколог",
            "specialty_code": "ONCO",
            "reasoning": "Образование в малом тазу 3.2 см с нечёткими контурами...",
            "priority": "high",
            "confidence": 0.95
        }
    ],
    "summary": "Рекомендуется срочная консультация онколога."
}
🧠 Как работает ИИ-анализ
Что уходит в GigaChat
Только обезличенные данные:

Текст заключения платформы «Третье Мнение».

Возраст пациента.

Пол пациента.

НИКОГДА не уходят: ФИО, дата рождения, телефон, email.

Защита от ошибок модели
Модуль nlp_module/analyzer.py содержит:

Защиту от prompt-инъекций — заключение обёрнуто в маркеры <<<ЗАКЛЮЧЕНИЕ>>>.

Валидацию по белым спискам — принимаются только разрешённые специальности.

Починку битого JSON — повторный запрос при ошибке парсинга.

Нормализацию полей — confidence обрезается до [0.0, 1.0], priority — только из списка.

Сортировку результатов — сначала high, потом medium, потом low.

🔒 Безопасность и защита персональных данных
Проект следует требованиям 152-ФЗ «О персональных данных».

Анонимизация
Персональные данные (ФИО, дата рождения, телефон, email) хранятся ОТДЕЛЬНО
от основной БД — в JSON-реестре patient_registry.json.

Где	Что хранится
Основная БД	patient_code (анонимный), возраст, пол
JSON-реестр	ФИО, дата рождения, телефон, email
API для внешних систем	Только patient_code
GigaChat	Только возраст и пол
Плюс такой архитектуры: если утечёт БД — ФИО там нет. Если утечёт JSON —
там нет медицинских данных. Чтобы связать — нужны обе системы.

Авторизация
Token Authentication — для API.

Session cookies — для админки Django.

Все API-эндпоинты требуют токен (кроме регистрации и логина).

📁 Структура репозитория
text
ThirdOpinion_AI_patient_router/
├── backend/                          # Серверная часть и ML-модуль
│   └── app/
│       ├── manage.py
│       ├── requirements.txt
│       ├── .env                      # ← в .gitignore
│       ├── patient_registry.json     # ← в .gitignore
│       ├── db.sqlite3                # ← в .gitignore
│       │
│       ├── medroute/                 # настройки Django-проекта
│       │   ├── settings.py
│       │   ├── urls.py
│       │   └── wsgi.py
│       │
│       ├── core/                     # основное приложение
│       │   ├── models.py             # Patient, Study, Recommendation, CarePlan
│       │   ├── views.py              # REST API views
│       │   ├── serializers.py
│       │   ├── urls.py
│       │   ├── auth_views.py         # регистрация, логин, логаут
│       │   ├── admin.py
│       │   ├── signals.py            # автозапуск ИИ, автосоздание плана
│       │   ├── patient_registry.py   # работа с JSON-реестром
│       │   ├── email_service.py      # отправка писем
│       │   ├── migrations/
│       │   └── templates/
│       │
│       └── nlp_module/               # NLP-модуль (независим от Django)
│           ├── analyzer.py           # логика анализа и валидации
│           └── llm.py                # обёртка над GigaChat
│
├── frontend/                         # Веб-интерфейс (React)
│
├── config/                           # Конфигурационные файлы
│
├── data/demo/                        # Синтетические демо-данные
│
├── tests/                            # Тесты
│
├── docs/                             # Архитектура и презентация
│
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md
🔄 Жизненный цикл исследования
text
1. Врач создаёт исследование с заключением
   └─→ сигнал автоматически запускает ИИ-анализ
       └─→ GigaChat возвращает 2-3 рекомендации (status=pending)

2. Врач проверяет каждую рекомендацию:
   ├─ Одобрил (approved)   → попадает в план
   ├─ Изменил (edited)     → source='doctor', попадает в план
   └─ Отклонил (rejected)  → не попадает

3. Как только ВСЕ рекомендации проверены:
   └─→ автоматически создаётся CarePlan (status='draft')

4. Врач может добавить комментарий к плану и нажать «Отправить»

5. Пациенту уходит email:
   • Данные пациента
   • Заключение
   • Рекомендованный маршрут
   • Файл исследования (вложение)
   • Кнопка «Записаться на приём»
Важная логика
Любая правка рекомендации → source='doctor', status='pending'.
Рекомендация откатывается в «ждёт проверки» и требует повторного одобрения.

Отправленный план — неизменяем. Если врач хочет что-то поправить,
создаётся новый план, старый остаётся как исторический артефакт.

🧪 Тестирование
Проверка авторизации
bash
# 1. Регистрация
curl -X POST http://127.0.0.1:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"username": "test", "password": "secret123", "email": "test@test.com"}'

# 2. Логин
curl -X POST http://127.0.0.1:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "test", "password": "secret123"}'

# 3. Запрос с токеном
curl http://127.0.0.1:8000/api/studies/ \
  -H "Authorization: Token <ТОКЕН>"

# 4. Запрос без токена — ожидаем 401
curl http://127.0.0.1:8000/api/studies/
Проверка ИИ-анализа
bash
python manage.py shell
python
from nlp_module.analyzer import generate_recommendations
from nlp_module.llm import call_llm

result = generate_recommendations(
    "В области малого таза определяется образование 3.2 см с нечёткими контурами.",
    call_llm,
    patient_age=67,
    patient_sex="M",
)
print(result)
Проверка отправки email
bash
python manage.py shell
python
from django.core.mail import send_mail

send_mail(
    "Тест",
    "Проверка SMTP",
    "noreply@thirdopinion.demo",
    ["your-email@gmail.com"],
    fail_silently=False,
)
⚠️ Ограничения и особенности
Это прототип для хакатона. Некоторые вещи упрощены осознанно:

Ограничение	Решение в продакшене
Синхронный вызов GigaChat	Celery + Redis (фоновые задачи)
JSON-реестр для персональных данных	Отдельный микросервис с транзакциями
Нет пагинации API	DRF Pagination (20 записей/страница)
Открытый /media/	Эндпоинт выдачи файлов с проверкой прав
Нет rate limiting	django-ratelimit
Один врач видит всё	Модель Clinic, User.clinic, фильтрация
Бессрочные токены	JWT с exp
SQLite	PostgreSQL
Имитация интеграции с МИС/РИС	Реальный коннектор к платформе «Третье Мнение»
Эти ограничения не влияют на демонстрацию ключевой ценности сервиса.

👥 Команда
«cord доступа»

Васильев Михаил Вячеславович

Фетисова Софья Олеговна

Иванов Денис Владимирович

Крылов Антон Вячеславович

Илющенко Оксана Романовна

Роли
Backend-разработчик — Django, REST API, интеграция с GigaChat.

NLP-разработчик — модуль анализа, промпт-инжиниринг, валидация.

Frontend-разработчик — React-интерфейс для врача.

Дизайнер — UX/UI.

📄 Лицензия
MIT

Прототип создан в рамках хакатона MedITron 2026 для компании «Третье Мнение».
Не предназначен для использования в медицинской практике без дополнительной
сертификации.

📞 Ссылки
Платформа «Третье Мнение» — https://platform.thirdopinion.ai/

Документация API (локально) — http://127.0.0.1:8000/api/docs/

Swagger (Docker) — http://localhost:8000/docs

text

---

## 📋 Что важно перед пушем в GitHub

**Проверь `.gitignore` в корне репозитория:**
.env
venv/
.venv/
pycache/
*.pyc
db.sqlite3
*.sqlite3
media/
patient_registry.json
sent_emails/
.DS_Store
node_modules/

text

**Проверь `git status` — в нём НЕ должно быть:**

- `.env` — там ключи GigaChat и Gmail.
- `patient_registry.json` — там ФИО и телефоны пациентов.
- `db.sqlite3` — там данные.
- `venv/` — там библиотеки.

**Если что-то в списке — удали из индекса:**

```bash
git rm --cached .env patient_registry.json db.sqlite3
И добавь в .gitignore.