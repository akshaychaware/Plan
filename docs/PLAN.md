# Training Tracker — Project Plan

## 1. Project Overview

### Project Name

**Training Tracker**

### Purpose

Build a simple application to track the daily training and exercise routine of a Greyhound being prepared for racing.

The application makes it easy to:

- Define the dog's weekly training routine.
- See what training is planned for today.
- Record what actually happened.
- Mark training as completed, skipped, or partially completed.
- Record simple observations or notes.
- Review the dog's training history.
- Track consistency over time.

The first version remains intentionally simple: a reliable daily training record, not a veterinary, fitness, or race-performance platform.

---

# 2. Core Problem

The training follows a routine such as:

- Monday → Running
- Tuesday → Walking
- Wednesday → Swimming for 20 minutes
- Thursday → Rest
- Friday → Running
- Saturday → Walking
- Sunday → Rest

The application answers:

1. What was planned?
2. What was actually done?
3. Was the session completed?
4. If it was not completed, why?
5. What observations were made?

---

# 3. Product Vision

A lightweight training journal that can answer:

- What was today's training?
- What training is planned this week?
- How consistently has the dog been trained?
- How many running / swimming sessions were completed?
- How long were the swimming sessions?
- Which training sessions were skipped?
- What notes were recorded on a particular day?
- How has the training routine changed over time?

Race preparation, performance metrics, training load, charts and reminders remain outside V1 unless they become necessary.

---

# 4. Initial Scope — V1

## 4.1 Dog

Name, breed, date of birth, optional weight, optional notes. Multiple dogs per user are supported.

## 4.2 Exercise Types

Running, Walking, Swimming, Hill Climbing, Rest (plus Bike/Cycle). More can be added by an administrator without code changes.

Measurements available for every activity type (all optional): duration (minutes), distance (km), repetitions. Rest records no measurements — recovery is still part of the plan.

---

# 5. Weekly Training Plan

The weekly routine is configurable in the app (no code changes), supports **several activities per day**, and can be versioned with start/end dates ("start a new plan version").

---

# 6. Planned vs Actual Training

Each session stores both what was planned (copied from the plan at the time) and what actually happened.

```text
Wednesday — Swimming
Planned: 20 minutes
Actual: 18 minutes
Status: Partially Completed
```

---

# 7. Daily Training Record

A record contains: date, dog, exercise, planned values, actual values, status, notes.

Statuses: **Planned** (derived — not yet recorded), **Completed**, **Partially Completed**, **Skipped**.

Rest days are recorded as a completed planned Rest activity.

---

# 8. Daily User Workflow

1. Open the application → see today's training.
2. Perform the training.
3. Record the result (or tap **Done** if it went exactly as planned).
4. Add optional notes.
5. Save → the session becomes part of the permanent history.

---

# 9. Main Application Screens — V1

| Screen | Status |
|---|---|
| Dashboard — today's activities, one-tap Done, this week, progress, statistics | Built |
| Training Plan — per-day activities, plan dates, new plan version | Built |
| Daily Training Entry — per activity, extra activities, any past date | Built |
| History — planned vs actual, status filter, pagination | Built |
| Dog profile — create and edit | Built |

---

# 10. Training History

Historical records are never rewritten when the plan changes. A September session planned at 20 minutes still shows "Planned: 20 minutes" after the plan becomes 30 minutes.

---

# 11. Basic Statistics — V1

For this week, this month, or all time:

- Training days, rest days
- Completed, partially completed, skipped, completion rate
- Current streak
- Per activity: sessions, total minutes, average minutes, total distance

Statistics are descriptive, not assessments of fitness or health.

---

# 12. What V1 Will NOT Do

Medical diagnosis, veterinary recommendations, automatic health assessment, automatic training prescriptions, AI-generated plans, GPS tracking, live heart-rate monitoring, wearable integration, complex performance analytics, race prediction, automatic injury detection, advanced nutrition management, multi-user permissions, social features.

---

# 13. Future Scope

- **V2 — Better training metrics:** speed, pace, track/surface, intensity. (Distance and repetitions are already available.)
- **V3 — Training analytics:** weekly/monthly volume, distribution, trends, personal records, charts.
- **V4 — Race preparation:** race, distance, target date, programme, phases (conditioning, strength, speed, race preparation, taper, recovery).
- **V5 — Advanced tracking:** GPS, wearables, heart rate, recovery, training load, notifications, calendar integration, offline recording, native mobile app.

---

# 14. Product Principles

1. **Keep it simple** — record a session in seconds.
2. **Record reality** — planned vs actual.
3. **Preserve history** — past records stay accurate.
4. **Start small** — no future features before the core workflow works.
5. **Make the data useful** — every field has a reason to exist.

---

# 15. Core Use Cases

| ID | Use case | Status |
|---|---|---|
| UC-01 | Create Dog | Done |
| UC-02 | Configure Weekly Training Plan | Done (multiple activities/day, plan versions) |
| UC-03 | View Today's Training | Done (web + `GET /api/training/today`) |
| UC-04 | Record Training | Done (web + `POST /api/training/sessions`) |
| UC-05 | Mark Training Status | Done (Completed / Partially Completed / Skipped) |
| UC-06 | Add Training Notes | Done |
| UC-07 | View Training History | Done (web + `GET /api/training/history`) |
| UC-08 | View Basic Statistics | Done (week / month / all; web + `GET /api/statistics`) |

---

# 16. Domain Model

```text
Dog
  ├── Training Plan (start/end dates, active flag)
  │       └── Plan Day (Mon–Sun)
  │               └── Planned Activity (exercise type, sequence, planned metrics, notes)
  └── Training Sessions (planned snapshot + actual values + status + notes)
```

Entities: `Dog`, `ExerciseType`, `TrainingPlan`, `TrainingPlanDay`, `PlannedActivity`, `TrainingSession`. See `ARCHITECTURE.md` §9–§11.

---

# 17. Development Approach

```text
1. Define requirements          ✓
2. Define use cases             ✓
3. Define domain model          ✓
4. Define database model        ✓
5. Build backend foundation     ✓
6. Build training plan          ✓
7. Build daily training records ✓
8. Build dashboard              ✓
9. Build history                ✓
10. Add basic statistics        ✓
11. Test complete workflow      ✓ (automated)
12. Release V1                  ◻ deployment pending
```

---

# 18. Definition of Done — V1

- [x] Create a dog.
- [x] Define a weekly training schedule.
- [x] View today's planned training.
- [x] Record a completed training session.
- [x] Record a partially completed session.
- [x] Record a skipped session.
- [x] Record actual duration where applicable.
- [x] Add notes.
- [x] View previous training records.
- [x] View the current week's training status.
- [x] View basic training statistics.
- [x] Change the future weekly schedule without corrupting historical records.
- [x] The complete workflow works end to end without manual database changes.

---

# 19. Development Tracking

## Phase 1 — Requirements

- [x] Define actual real-world training workflow
- [x] Confirm initial exercise types
- [x] Confirm weekly schedule behavior
- [x] Define training session statuses
- [x] Define minimum information required for each activity
- [x] Confirm V1 scope

## Phase 2 — Domain Design

- [x] Define entities
- [x] Define relationships
- [x] Define domain rules
- [x] Define historical data behavior
- [x] Review domain model

## Phase 3 — Database Design

- [x] Design tables
- [x] Define primary keys
- [x] Define foreign keys
- [x] Define indexes
- [x] Define constraints
- [x] Create initial migration (including data migration of the existing plan)

## Phase 4 — Backend

- [x] Project setup
- [x] Dog APIs
- [x] Exercise type APIs
- [x] Training plan APIs
- [x] Training session APIs
- [x] History APIs
- [x] Statistics APIs
- [x] Backend tests

## Phase 5 — Frontend

- [x] Project setup
- [x] Dashboard
- [x] Training plan screen
- [x] Daily training screen
- [x] History screen
- [x] Basic statistics
- [x] Frontend validation
- [x] Responsive layout and installable PWA

## Phase 6 — Integration

- [x] Connect frontend and backend (shared domain services)
- [x] Test complete daily workflow
- [x] Test schedule changes
- [x] Test historical records
- [x] Test edge cases (future dates, Rest/skipped metrics, other users' data)
- [x] Fix integration issues

## Phase 7 — V1 Completion

- [x] End-to-end testing (automated web, API and service tests)
- [x] Clean up code
- [x] Documentation
- [ ] Deployment
- [ ] V1 release

---

# 20. Important Design Decisions

| Decision | Status | Notes |
|---|---|---|
| V1 focuses on simple daily training tracking | Confirmed | Avoid unnecessary complexity |
| Planned and actual training are separate concepts | Confirmed | Planned values snapshotted per session |
| Weekly schedule is configurable | Confirmed | Edited in the app, no code changes |
| Rest is part of the training schedule | Confirmed | Rest activities record no metrics |
| Historical records must not change when plans change | Confirmed | Snapshots + in-place plan edits |
| Advanced analytics are deferred | Confirmed | Consider after V1 |
| One day can hold multiple activities | Confirmed | Ordered planned activities per plan day |
| Training plans have start/end dates | Confirmed | One active plan per dog; plan versions |
| Multiple dogs per user | Confirmed | Each dog owned by a user |
| Skipped sessions are explained in notes | Confirmed | No separate reason field |
| Stack: Django + DRF + MySQL, PWA frontend | Confirmed | See ARCHITECTURE.md §19 |

---

# 21. Open Questions

- [x] What exact weekly routine should be the initial default? — None; each dog's plan is configured by the user.
- [x] Should one day support multiple activities? — Yes.
- [x] Should an activity have a planned duration? — Optional.
- [x] Which activities need distance? — Optional for every activity except Rest.
- [x] Which activities need repetitions? — Optional for every activity except Rest (e.g. hill repeats).
- [ ] Should the user record intensity? — Deferred to V2.
- [ ] Should the user record the dog's condition before/after training? — Use notes for now.
- [x] Should weight be tracked? — Current weight on the dog profile; weight history deferred.
- [x] Should the application support more than one dog? — Yes.
- [x] Should training plans have start/end dates? — Yes.
- [x] How should a skipped session be explained? — In the notes.
- [ ] Should the application support future race dates? — Deferred to V4.

---

# 22. Project Rule

The project remains **issue-driven**: define the problem → create an issue → acceptance criteria → smallest useful change → tests → verify → close → update this plan → next issue. Do not implement future features just because they are listed here.

---

# 23. Current Status

**Project:** Training Tracker

**Version:** V1

**Status:** Feature-complete; automated tests passing; deployment pending.

**Current focus:**

> Use the application for real training and collect feedback.

**Next milestone:**

> Choose a deployment environment and release V1.

---

# 24. Change Log

## 2026-10-18

- Implemented the architecture: modular Django monolith with `dog`, `exercise`, `training_plan`, `training_session` and `statistics` modules.
- New domain model: training plans with start/end dates, plan days, multiple ordered planned activities per day, repetitions.
- Dog profile gained date of birth, weight and notes; exercise types gained descriptions.
- Sessions link to planned activities, keep a planned snapshot, support extra (unplanned) activities, and use statuses `COMPLETED`, `PARTIALLY_COMPLETED`, `SKIPPED` (`PLANNED` derived).
- Added REST API (`/api/...`) with Django REST Framework, sharing the same services as the web UI.
- Statistics by week / month / all time, including training days, rest days and average duration.
- Web app is responsive and installable as a PWA with an offline page.
- Migrated the existing weekly plan and sessions to the new structure; tables renamed to the architecture's names.
- Added distance (km) to plans and sessions; added Bike/Cycle activity; redesigned UI with dark mode, streaks, progress ring and one-tap Done.

## 2026-09-29

- Created initial project plan.
- Defined the project as a simple Greyhound daily training tracker.
- Established the initial concept of planned vs actual training.
- Defined initial activities: Running, Walking, Swimming, Hill Climbing, Rest.
- Defined configurable weekly training schedule, basic daily training records and V1 scope.
- Deferred advanced race analytics, GPS, health monitoring, AI, and wearable integrations.
