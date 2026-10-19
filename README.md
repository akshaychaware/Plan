# Training Tracker

A simple application for tracking a Greyhound's daily training routine.

**Plan training → Perform training → Record actual result → Review history**

## Features (V1)

- Dog profiles (name, breed, date of birth, weight, notes); multiple dogs per user
- Configurable training plans with start/end dates and versions
- Multiple activities per day, with optional duration, distance and repetitions
- Today's training with one-tap **Done** or a detailed entry form
- Completed / partially completed / skipped status, notes, extra activities
- Planned values snapshotted per session, so history never changes
- Weekly overview, training history and statistics (week / month / all time), streaks
- Responsive web UI with dark mode, installable as a PWA
- REST API (`/api/...`) sharing the same business logic as the web UI

## Tech stack

Django 6 · Django REST Framework · MySQL · Python 3.14 · vanilla JS/CSS (no CDN)

## Getting started

```bash
cd plan
pyenv activate workout                 # or your own virtualenv
pip install -r requirements.txt
cp .env.example .env                   # then fill in real values (never commit .env)
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open http://127.0.0.1:8000/ and log in.

### Configuration (`plan/.env`)

| Variable | Purpose |
|---|---|
| `DJANGO_SECRET_KEY` | Required. Long random secret |
| `DJANGO_DEBUG` | `True` for local development only |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated host names |
| `DJANGO_TIME_ZONE` | e.g. `Asia/Kolkata` (determines "today") |
| `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` | MySQL connection |

### Tests

```bash
cd plan
python manage.py test plan_app
```

The suite creates a temporary `test_<DB_NAME>` database, so the database user needs permission to create databases.

## Documentation

- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md): architecture, domain model, database and API
- [`docs/PLAN.md`](docs/PLAN.md): scope, roadmap, decisions and progress tracking
- [`docs/USER_GUIDE.md`](docs/USER_GUIDE.md): how to use the application

## Current status

**Version:** V1 · **Status:** feature-complete, tests passing, deployment pending.

## Project principles

1. Keep daily usage simple.
2. Record planned and actual training separately.
3. Preserve historical records.
4. Avoid unnecessary data collection.
5. Build the smallest useful version first.
6. Add complexity only when the real training workflow requires it.
