# Training Tracker — User Guide

## 1. Introduction

Training Tracker records a dog's daily training routine.

```text
View today's plan → Perform training → Record actual result → Add notes → Save → Review history
```

# 2. Getting Started

## 2.1 Log in

Open the app in your browser and log in. Accounts are created by the administrator.

## 2.2 Install on your phone (optional)

Training Tracker is an installable web app:

- **Android / Chrome:** menu → *Install app* (or *Add to Home screen*).
- **iPhone / Safari:** Share → *Add to Home Screen*.

It then opens full-screen like a native app. Without a connection it shows an offline page; reconnect to load and save sessions.

## 2.3 Create the Dog

Choose **Add dog** and enter the profile.

```text
Name: Luna
Breed: Greyhound
Date of birth: optional
Weight (kg): optional
Notes: optional
```

You can edit the profile later with **Edit profile** on the dog's dashboard.

# 3. Configure the Training Plan

Open the **Plan** tab. Give the plan a name and start date, then add activities to each day with **Add activity**.

```text
Monday     → Running
Tuesday    → Walking
Wednesday  → Swimming — 20 minutes
Thursday   → Rest
Friday     → Running
Saturday   → Walking
Sunday     → Rest
```

- A day can have **several activities** (for example *Warm-up*, *Running*, *Recovery*). They are done in the order listed.
- Each activity can have an optional duration (minutes), distance (km), repetitions and a short note, such as "10 min + 5 min rest + 10 min".
- Use **Rest** for planned recovery. Rest has no duration or distance.
- Tick **Remove** on an activity to delete it when you save.

Changing the plan never changes sessions you've already recorded.

### Start a new plan version

When the routine changes for a new period, use **Start a new plan version** at the bottom of the Plan page. It copies the current week into a new plan starting on the date you choose and ends the current plan the day before. Past dates keep using the plan that applied at the time.

# 4. View Today's Training

The **Dashboard** shows today's planned activities, each with its status.

```text
Today

Swimming — 20 min        Planned     [Done] [Record]
Walking — 1 km           Planned     [Done] [Record]
```

# 5. Record a Training Session

- **Done** records the activity as *Completed* with the planned values. It takes one tap.
- **Record** opens the entry form, where you can enter what actually happened.

```text
Activity: Swimming
Planned: 20 minutes
Actual: 18 minutes
Status: Partially completed
Notes: Good session
```

The chips at the top of the form switch between that day's activities. After you save one, the app moves on to the next activity that isn't recorded yet.

- **Extra activity** records something that wasn't in the plan.
- **Choose another date** records a past day. Future dates can't be recorded.

# 6. Training Status

| Status | Meaning |
|---|---|
| **Planned** | In the plan, not recorded yet |
| **Completed** | The planned activity was done |
| **Partially completed** | It happened but didn't fully match the plan |
| **Skipped** | It wasn't performed. Duration and distance stay empty, and you can add the reason in the notes |

A past planned activity that was never recorded shows as **Not recorded**.

# 7. Recording Notes

Notes are optional. Keep them short and useful:

```text
Good session.
Dog was energetic today.
Stopped early.
```

# 8. Rest Days

Rest is part of the plan. Record it as *Completed* (tap **Done**). A rest day doesn't need a duration.

# 9. Reviewing Training History

The **History** tab lists every session, newest first, showing planned vs actual, status and notes. Filter by status with the buttons at the top, and tap **Edit** to correct a session.

```text
Tue, 29 Sep 2026   Swimming — 20 min   Swimming — 18 min   Partially completed
Mon, 28 Sep 2026   Rest                Rest                Completed
```

Historical records show what was planned and done on that date.

# 10. Weekly Overview

**This week** on the dashboard shows Monday to Sunday with every activity and a status dot:

- ● green: completed
- ◐ amber: partially completed
- ● red: skipped
- ○ outline: planned (dashed red if the day has passed without a record)

Tap a past day or today to record it. The **Weekly progress** ring shows how many planned training activities (excluding Rest) are done this week.

# 11. Basic Statistics

Switch between **This week**, **This month** and **All time**:

```text
Training days: 5     Rest days: 2
Completed: 4         Partial: 1      Skipped: 1
Completion: 67%      Minutes: 98     Kilometres: 6
```

**Activity breakdown** shows each activity's sessions, total minutes, average minutes and distance:

```text
Swimming — 4 sessions · 78 min (avg 19.5)
```

The header also shows your current **streak**: consecutive days with at least one session that wasn't skipped.

These are descriptive records, not medical or veterinary assessments.

# 12. Changing the Training Plan

Edit the plan whenever the routine changes:

```text
Previous: Wednesday → Swimming — 20 minutes
New:      Wednesday → Swimming — 30 minutes
```

Future sessions use the new plan. Previous records keep "Planned: 20 minutes".

# 13. Recommended Daily Workflow

- **Morning:** open the dashboard and check today's training.
- **During training:** perform the planned activities.
- **After training:** tap **Done**, or **Record** the actual result, status and notes.
- **End of day:** confirm every activity shows a status.

# 14. Example Full Day

```text
Today's plan: Swimming — 20 minutes

After training:
Activity: Swimming
Planned: 20 minutes
Actual: 18 minutes
Status: Partially completed
Notes: Good session.
```

# 15. Dark Mode

Use the moon button at the top of the page to switch between light and dark mode. The app remembers your choice.

# 16. Important Usage Principles

- **Record what actually happened.** Don't change the actual result to match the plan.
- **Keep notes short.**
- **Preserve history.** Plan changes never alter previous records.
- **Keep the routine practical.**

# 17. For Developers: REST API

All features are also available as JSON under `/api` (log in first). See `ARCHITECTURE.md` §14 for endpoints and examples, such as `GET /api/training/today` and `POST /api/training/sessions`.

# 18. Current V1 Workflow

```text
Create Dog → Create Training Plan → Open Dashboard → View Today's Training
→ Perform Training → Done / Record Actual Result → Set Status → Add Notes
→ Save → Review History and Statistics
```
