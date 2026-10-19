# Training Tracker — Architecture

## 1. Architecture Overview

Training Tracker is a **modular monolith**: one Django application whose code is organised around business modules, backed by one relational database.

```text
                    Training Tracker
                           │
             ┌─────────────┴─────────────┐
             │                           │
        Frontend                    Backend API
             │                           │
   Web app (server-rendered,      Application Logic
   installable PWA)              (domain services)
                                         │
                                  ┌──────┴──────┐
                                  │             │
                              Database      Static storage
                               (MySQL)
```

The application does not use microservices.

---

# 2. Architecture Goals

1. Keep the application simple.
2. Clearly separate frontend and backend responsibilities.
3. Keep business rules inside the backend.
4. Preserve historical training data.
5. Allow the training plan to change without modifying old records.
6. Support multiple activities in a single day.
7. Allow new exercise/activity types to be added without redesigning the system.
8. Make future features possible without prematurely implementing them.
9. Keep V1 easy to develop, test, deploy, and maintain.

All nine goals are met by the current implementation (see §21 and §22).

---

# 3. High-Level Architecture

```text
┌────────────────────────────────────────────────────┐
│                    Frontend                        │
│  Django templates + vanilla JS, installable PWA    │
│                                                    │
│  Dashboard · Training Plan · Daily Session         │
│  History · Statistics · Dog profile                │
└────────────────────────┬───────────────────────────┘
                         │
          HTML forms (web)  /  HTTP + JSON (/api)
                         │
                         ▼
┌────────────────────────────────────────────────────┐
│                    Backend (Django)                │
│                                                    │
│  dog · exercise · training_plan ·                  │
│  training_session · statistics                     │
│  (models → services → serializers/api)             │
└────────────────────────┬───────────────────────────┘
                         │
                     Django ORM
                         │
                         ▼
┌────────────────────────────────────────────────────┐
│                  MySQL (database "plan")           │
│                                                    │
│  dogs · exercise_types · training_plans ·          │
│  training_plan_days · planned_activities ·         │
│  training_sessions                                 │
└────────────────────────────────────────────────────┘
```

The web pages and the REST API are two thin entry points over **the same domain services**, so business rules exist exactly once.

---

# 4. Architectural Style — Modular Monolith

All backend modules run as one application:

```text
plan_app
├── dog
├── exercise
├── training_plan
├── training_session
└── statistics
```

### Why not microservices?

The application does not require independent scaling, distributed processing, multiple teams, service-to-service communication, independently deployed services, or distributed messaging. Microservices would add complexity without solving a current problem.

---

# 5. Frontend

The frontend:

- Displays the training plan, today's training, history, and statistics.
- Collects user input and performs basic UI validation (e.g. disabling duration/distance for Rest or Skipped).
- Is responsive (phone, tablet, desktop) and installable as a **PWA** (manifest + service worker with an offline page).

The frontend does **not** own business rules. It never decides that "Wednesday = Swimming"; it renders what the backend services return:

```text
Frontend (dashboard or GET /api/training/today)
   │
   ▼
Backend: training_session.services.day_entries(dog, date)
   ├── Determine the date
   ├── Find the plan covering that date (training_plan.services.plan_for_date)
   ├── Find that day's planned activities (in sequence)
   └── Pair them with recorded sessions → status PLANNED / COMPLETED / …
```

---

# 6. Backend

The backend is the source of truth for:

- Managing dogs, exercise types, and training plans.
- Generating today's planned training.
- Recording training sessions and validating their status and metrics.
- Preserving historical (planned) values.
- Retrieving history and calculating statistics.

It exposes a REST API under `/api` (§14).

---

# 7. Backend Module Structure

Each module is a package inside the Django app `plan_app`:

```text
plan/                         Django project (settings, root URLs)
plan_app/
├── core/                     shared building blocks
│   ├── models.py             TimeStampedModel, metric fields, validation helpers
│   ├── api.py                exception handler, permissions, owner-scoped fields
│   └── renderers.py          camelCase JSON renderer/parser
├── dog/                      models · serializers · api
├── exercise/                 models · serializers · api
├── training_plan/            models · services · serializers · api
├── training_session/         models · services · serializers · api
├── statistics/               services · api
├── api_urls.py               REST routes (/api/…)
├── views.py · forms.py       web controllers and forms (call the services)
├── templates/ · static/      web UI and PWA assets
├── migrations/
└── tests/                    test_services · test_api · test_web
```

Mapping to the conceptual layers:

| Concept | Django implementation |
|---|---|
| controller | `api.py` (DRF viewsets) and `views.py` (web) |
| service | `services.py` — all business rules and transactions |
| repository | Django ORM managers/querysets (no extra layer needed) |
| entity/model | `models.py` (validation in `clean()` and field validators) |
| dto | DRF serializers |
| tests | `plan_app/tests/` |

---

# 8. Domain-Oriented Modules

## Dog Module

Creates, updates and retrieves dogs. Fields: `name`, `breed`, `date_of_birth`, `weight_kg`, `notes`. Each dog belongs to a user (owner).

## Exercise Module

Configurable activity types. Initial: Running, Walking, Swimming, Hill Climbing, Rest (plus Bike/Cycle). Each type has a `description` and a `tracks_metrics` flag (Rest = no duration/distance/repetitions). Adding an activity is a data change, not a code change.

## Training Plan Module

A dog has training plans, each covering a period (`start_date` → optional `end_date`). A plan has seven plan days; each day has an ordered list of planned activities with optional duration, distance, repetitions and notes. Exactly one plan per dog is active. "Start a new plan version" copies the active week into a new plan and ends the old one the day before.

## Training Session Module

Records what actually happened: status, actual metrics, notes, and a snapshot of the planned values at the time. Sessions can be linked to a planned activity or recorded as extra (unplanned) activities.

## Statistics Module

Descriptive summaries for this week, this month, or all time: training days, rest days, completed / partially completed / skipped, completion rate, streak, and per-activity session count, total and average minutes, and total distance — computed with SQL aggregation directly on `training_sessions`.

---

# 9. Domain Model

```text
User
 └── Dog
      ├───────────────┐
      ▼               ▼
 Training Plan    Training Sessions ──(optional link)──┐
      │                                                │
      ▼                                                │
 Plan Days (Mon–Sun)                                   │
      │                                                │
      ▼                                                │
 Planned Activities ◄──────────────────────────────────┘
      │
      ▼
 Exercise Type
```

---

# 10. Supporting Multiple Activities Per Day

Implemented in both the model and the UI:

```text
Training Plan
     └── Plan Day (Wednesday)
            ├── Activity 1  (sequence 0)
            ├── Activity 2  (sequence 1)
            └── Activity 3  (sequence 2)
```

The plan editor lets you add, reorder (by row order) and remove activities per day; the dashboard and record page handle each activity separately.

---

# 11. Database Architecture

Implemented tables (MySQL, database `plan`):

| Table | Key columns |
|---|---|
| `dogs` | id, owner_id, name, breed, date_of_birth, weight_kg, notes, created_at, updated_at |
| `exercise_types` | id, name (unique), description, tracks_metrics, created_at, updated_at |
| `training_plans` | id, dog_id, name, start_date, end_date, is_active, created_at, updated_at |
| `training_plan_days` | id, training_plan_id, day_of_week — unique (training_plan_id, day_of_week) |
| `planned_activities` | id, training_plan_day_id, exercise_type_id, sequence, planned_duration_minutes, planned_distance_km, planned_repetitions, notes |
| `training_sessions` | id, dog_id, planned_activity_id (nullable, SET NULL), exercise_type_id, date, planned_exercise_type_id, planned_duration_minutes, planned_distance_km, planned_repetitions, actual_duration_minutes, actual_distance_km, actual_repetitions, status, notes, created_at, updated_at — unique (planned_activity_id, date), index (dog_id, date) |

**Activity metric strategy:** every activity may carry duration (minutes), distance (km) and repetitions; all are optional, and types with `tracks_metrics = false` (Rest) reject all three.

**Integrity rules:** exercise types are `PROTECT`ed (cannot be deleted while referenced); deleting a planned activity sets `planned_activity_id` to NULL on sessions, keeping their snapshot.

---

# 12. Historical Data Preservation

When a session is recorded, the planned exercise type, duration, distance and repetitions are copied into the session row.

```text
September: Wednesday → Swimming → 20 min   (session recorded: planned 20, actual 20)
October:   Wednesday → Swimming → 30 min   (plan edited)

September session still shows: Planned 20 min · Actual 20 min
```

Plan edits update planned activities **in place** (by id), so existing sessions stay linked; removed activities only unlink sessions. Plan versions (start/end dates) let past dates resolve to the plan that applied at the time.

---

# 13. Training Session Lifecycle

```text
PLANNED (derived: planned activity without a session)
   │
   ├──────────────┬────────────────────┐
   ▼              ▼                    ▼
COMPLETED   PARTIALLY_COMPLETED     SKIPPED
   └──────────────┴────────────────────┘
                  ▼
                SAVED
```

`PLANNED` is computed, not stored. Stored statuses are validated by the backend: only `COMPLETED`, `PARTIALLY_COMPLETED` and `SKIPPED` are accepted; skipped sessions and Rest cannot have metrics; sessions cannot be in the future; a planned activity must belong to the same dog and weekday.

---

# 14. REST API

Base path `/api`. JSON keys are camelCase. Authentication: Django session (same-origin, CSRF-protected). All data is scoped to the signed-in user.

| Method & path | Purpose |
|---|---|
| `GET/POST /api/dogs`, `GET/PUT/PATCH /api/dogs/{id}` | Dogs |
| `GET /api/exercise-types` (write: staff only) | Activity types |
| `GET/POST /api/training-plans?dog=`, `GET/PUT/PATCH /api/training-plans/{id}` | Plans |
| `POST /api/training-plans/{id}/activate` | Make a plan active |
| `GET/PUT /api/training-plans/{id}/days` | Read / upsert the week's planned activities |
| `GET /api/training/today?dog=&date=` | Today's training (planned activities + status) |
| `GET/POST /api/training/sessions`, `GET/PUT/PATCH /api/training/sessions/{id}` | Record and edit sessions |
| `GET /api/training/history?dog=&status=&from=&to=` | Paginated history |
| `GET /api/statistics?dog=&period=week\|month\|all` | Summary statistics |

`?dog=` may be omitted when the user has exactly one dog.

## Example — Today's Training

```http
GET /api/training/today
```

```json
{
  "date": "2026-09-29",
  "dog": { "id": 1, "name": "Luna" },
  "activities": [
    {
      "plannedActivityId": 12,
      "sessionId": null,
      "exercise": "Swimming",
      "exerciseTypeId": 3,
      "plannedDurationMinutes": 20,
      "plannedDistanceKm": null,
      "plannedRepetitions": null,
      "notes": "10 min + 5 min rest + 10 min",
      "status": "PLANNED"
    }
  ]
}
```

## Example — Record Session

```http
POST /api/training/sessions
```

```json
{
  "plannedActivityId": 12,
  "actualDurationMinutes": 18,
  "status": "PARTIALLY_COMPLETED",
  "notes": "Good session"
}
```

The backend determines the dog, date (default today), plan, activity and planned snapshot. Posting again for the same planned activity and date updates that session.

**Conventions:** metric fields carry units in their names (`…Minutes`, `…Km`). Validation errors return `400` with field-keyed messages (`{"actualDurationMinutes": ["Leave empty for skipped sessions."]}`); `nonFieldErrors` holds cross-field errors. Lists are paginated (`count`, `next`, `previous`, `results`; 20 per page). Users are throttled at 1000 requests/hour.

---

# 15. Statistics Architecture

```text
Statistics API / dashboard
      │
      ▼
statistics.services.summarize(dog, period)
      │
      ▼
SQL aggregation on training_sessions: COUNT, SUM, AVG, GROUP BY exercise type
```

No separate analytics database.

---

# 16. Authentication and Users

Implemented: Django authentication with login required for all pages and API endpoints. Ownership chain:

```text
User → Dogs → Training Plans → Training Sessions
```

Every query is scoped to the signed-in user's dogs. Accounts are created by an administrator (`createsuperuser` or `/admin/`). Token authentication for a future native mobile app is deferred.

---

# 17. Project Structure

```text
Plan/                         repository root
├── README.md
├── docs/
│   ├── ARCHITECTURE.md
│   ├── PLAN.md
│   └── USER_GUIDE.md
└── plan/                     Django project (backend + server-rendered frontend)
    ├── manage.py
    ├── requirements.txt
    ├── .env.example
    ├── plan/                 settings, root URLs
    └── plan_app/             domain modules, web UI, API, tests
```

Docker is not used yet (§28).

---

# 18. Deployment Architecture

```text
Internet / Local Network
          │
          ▼
  Django (web pages + /api + PWA assets)
          │
          ▼
        MySQL
```

For production: run behind a WSGI server (e.g. gunicorn) and a reverse proxy with HTTPS, set `DJANGO_DEBUG=False`, a strong `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS`, and serve static files via `collectstatic`.

---

# 19. Technology Selection

| Concern | Choice | Status |
|---|---|---|
| Backend framework | Django 6 (Python 3.14) | Confirmed |
| API | Django REST Framework 3.18 | Confirmed |
| Frontend | Django templates + vanilla JS, PWA | Confirmed for V1 |
| Database | MySQL (`plan`) | Confirmed |
| ORM | Django ORM | Confirmed |
| Authentication | Django session auth | Confirmed |
| Configuration | Environment variables via `.env` (python-dotenv) | Confirmed |
| Mobile | PWA first; native app later if needed | Confirmed approach |

The original proposal (Angular + NestJS + TypeORM + PostgreSQL) was set aside in favour of the existing Django + MySQL stack, as permitted by "the technology should serve the domain". The domain model, module boundaries and API are technology-neutral, so an Angular or native client can be added on top of `/api` later.

---

# 20. V1 Architecture Boundaries

V1 contains:

```text
Web frontend (PWA)
    ↓
REST API + web controllers
    ↓
Modular backend (domain services)
    ↓
Relational database
```

V1 does not contain microservices, message queues, event streaming, a data warehouse, a separate analytics service, an AI service, a GPS pipeline, or a wearable ingestion pipeline.

---

# 21. Core Architectural Principles

1. **Backend is the source of truth** — rules live in model validation and `services.py`; both UI and API call them.
2. **Domain-oriented modules** — `dog`, `exercise`, `training_plan`, `training_session`, `statistics`.
3. **Preserve history** — planned values are snapshotted on every session.
4. **Activity-driven design** — exercises are data (`exercise_types`), not code.
5. **Multiple activities per day** — plan days hold ordered planned activities.
6. **Keep V1 simple** — no infrastructure beyond Django + MySQL.

---

# 22. Architecture Decision Log

| Decision | Status | Reason |
|---|---|---|
| Use a modular monolith for V1 | Confirmed | Simple and maintainable |
| Use a relational database (MySQL) | Confirmed | Clear relationships; existing database |
| Use Django + DRF instead of NestJS/Angular | Confirmed | Existing working stack; technology serves the domain |
| Backend owns business rules | Confirmed | Single source of truth for web and API |
| Separate planned and actual training | Confirmed | Accurate tracking |
| Snapshot planned values in sessions | Confirmed | History never changes |
| Edit planned activities in place (upsert by id) | Confirmed | Keeps sessions linked to their planned activity |
| Support multiple activities per day | Confirmed | Flexible domain |
| Treat exercises as activity types with a `tracks_metrics` flag | Confirmed | New activities without redesign |
| `PLANNED` is a derived status | Confirmed | No placeholder rows; only real results are stored |
| REST API with camelCase JSON and unit-suffixed metrics | Confirmed | Clean client contract, unambiguous units |
| Session authentication; token auth deferred | Confirmed | Same-origin web/PWA today; native app later |
| PWA before native mobile | Confirmed | Covers today's mobile needs without a second codebase |
| Avoid microservices and separate analytics in V1 | Confirmed | No current requirement |

---

# 23. Open Architecture Questions

- [x] Select frontend technology — Django templates + vanilla JS (PWA).
- [x] Select backend technology — Django 6 + DRF.
- [x] Select relational database — MySQL.
- [x] Decide ORM — Django ORM.
- [x] Finalize domain entities — §8, §9.
- [x] Finalize database relationships — §11.
- [x] Finalize activity metric strategy — optional duration/distance/repetitions; `tracks_metrics` flag.
- [x] Decide whether V1 supports multiple dogs — yes, per user.
- [x] Decide whether V1 requires authentication — yes.
- [x] Define API conventions — §14.
- [x] Define error-handling conventions — §14.
- [x] Define testing strategy — Django `TestCase` suites for services, API and web (`plan_app/tests`).
- [ ] Define deployment environment.

---

# 24. Architecture Status

**Project:** Training Tracker · **Version:** V1

**Architecture status:** Implemented — modular Django monolith, REST API, PWA, MySQL.

**Next step:** Choose the production deployment environment; evaluate whether a native mobile app is needed.

---

# 25. Client Applications — Web and Mobile

Web and mobile are clients of the **same backend and database**:

```text
Web (Django pages / PWA) ───┐
                            ├── same services ──→ Django ──→ MySQL
Future mobile / Angular ────┘   (REST /api)
```

- **Web** is best for plan configuration, history, statistics and administration.
- **Mobile (PWA)** is best for today's training, one-tap "Done", quick notes and recording outside.
- A session recorded on any client is immediately part of the same history.

A native app (Flutter or React Native) becomes worthwhile only for advanced GPS, background location, wearables, or richer offline recording.

---

# 26. Client Stack

| Client | Technology | Status |
|---|---|---|
| Web | Django templates + vanilla JS | Implemented |
| Mobile | Installable PWA | Implemented |
| Native mobile | Flutter or React Native | To be decided (later phase) |
| Backend | Django + DRF | Implemented |
| API | REST + JSON | Implemented |
| ORM | Django ORM | Implemented |
| Database | MySQL | Implemented |

---

# 27. System Architecture (current)

```text
              ┌──────────────────────────┐
              │  Web app / PWA (browser) │
              └────────────┬─────────────┘
                           │  HTML forms · REST/JSON
              ┌────────────▼─────────────┐
              │      Django backend      │
              │  dog · exercise ·        │
              │  training_plan ·         │
              │  training_session ·      │
              │  statistics              │
              └────────────┬─────────────┘
                           │  Django ORM
              ┌────────────▼─────────────┐
              │          MySQL           │
              └──────────────────────────┘
```

---

# 28. Remaining Architecture Questions

- [x] Decide whether mobile is part of V1 — yes, as a PWA.
- [ ] Decide between Flutter and React Native — only if a native app is needed.
- [x] Evaluate whether a PWA is sufficient for V1 — yes.
- [ ] Define offline recording requirements (currently: offline page only).
- [ ] Define future GPS and wearable requirements.
- [ ] Decide on Docker for local development and deployment.
