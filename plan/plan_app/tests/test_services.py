from datetime import timedelta

from django.core.exceptions import ValidationError

from plan_app.models import Dog, PlannedActivity, TrainingSession
from plan_app.statistics.services import summarize, week_progress
from plan_app.training_plan import services as plans
from plan_app.training_session import services as sessions

from .base import TrackerTestCase

Status = TrainingSession.Status


class TrainingPlanServiceTests(TrackerTestCase):
    def test_multiple_activities_per_day_in_sequence(self):
        entry = sessions.day_entries(self.dog, self.today)
        self.assertEqual([a['planned'] for a in entry['activities']], [self.swim, self.walk])
        self.assertEqual({a['status'] for a in entry['activities']}, {TrainingSession.PLANNED})

    def test_save_week_updates_in_place_and_preserves_history(self):
        session = sessions.record_session(
            dog=self.dog, day=self.today, planned_activity=self.swim, status=Status.COMPLETED
        )
        plans.save_week(self.plan, {self.today.weekday(): [
            {'id': self.swim.pk, 'exercise_type': self.types['Swimming'], 'planned_duration_minutes': 30},
        ]})
        session.refresh_from_db()
        self.assertEqual(session.planned_activity_id, self.swim.pk)
        self.assertEqual(session.planned_summary, 'Swimming — 20 min')
        self.assertFalse(PlannedActivity.objects.filter(pk=self.walk.pk).exists())

    def test_start_new_plan_versions_the_schedule(self):
        new_plan = plans.start_new_plan(self.dog, name='Autumn block', start_date=self.today)
        self.plan.refresh_from_db()
        self.assertFalse(self.plan.is_active)
        self.assertEqual(self.plan.end_date, self.today - timedelta(days=1))
        self.assertEqual(plans.plan_for_date(self.dog, self.today), new_plan)
        self.assertEqual(plans.plan_for_date(self.dog, self.today - timedelta(days=7)), self.plan)
        self.assertEqual(plans.planned_activities_for(self.dog, self.today).count(), 2)
        with self.assertRaises(ValidationError):
            plans.start_new_plan(self.dog, name='Too early', start_date=self.today)

    def test_rest_rejects_metrics(self):
        rest = PlannedActivity(training_plan_day=self.swim.training_plan_day, exercise_type=self.types['Rest'],
                               planned_duration_minutes=10)
        with self.assertRaises(ValidationError):
            rest.full_clean()


class TrainingSessionServiceTests(TrackerTestCase):
    def test_skipped_clears_planned_defaults_and_rejects_metrics(self):
        session = sessions.record_session(dog=self.dog, day=self.today, planned_activity=self.swim, status=Status.SKIPPED)
        self.assertIsNone(session.actual_duration_minutes)
        self.assertEqual(session.planned_duration_minutes, 20)
        with self.assertRaises(ValidationError):
            sessions.save_session(session, actual_duration_minutes=5)

    def test_rejects_future_dates_and_foreign_planned_activities(self):
        with self.assertRaises(ValidationError):
            sessions.record_session(dog=self.dog, day=self.today + timedelta(days=1),
                                    exercise_type=self.types['Walking'], status=Status.COMPLETED)
        other_dog = Dog.objects.create(owner=self.other_user, name='Rex')
        with self.assertRaises(ValidationError):
            sessions.record_session(dog=other_dog, day=self.today, planned_activity=self.swim, status=Status.COMPLETED)

    def test_complete_as_planned_is_idempotent(self):
        first = sessions.complete_as_planned(self.dog, self.swim, self.today)
        self.assertEqual((first.status, first.actual_duration_minutes), (Status.COMPLETED, 20))
        self.assertIsNone(sessions.complete_as_planned(self.dog, self.swim, self.today))


class StatisticsServiceTests(TrackerTestCase):
    def test_summary_counts_training_and_rest_days(self):
        record = sessions.record_session
        record(dog=self.dog, day=self.today, planned_activity=self.swim, status=Status.COMPLETED,
               actual_duration_minutes=18)
        record(dog=self.dog, day=self.today, planned_activity=self.walk, status=Status.SKIPPED)
        record(dog=self.dog, day=self.today - timedelta(days=1), exercise_type=self.types['Rest'],
               status=Status.COMPLETED)
        record(dog=self.dog, day=self.today - timedelta(days=2), exercise_type=self.types['Swimming'],
               status=Status.PARTIALLY_COMPLETED, actual_duration_minutes=10)

        stats = summarize(self.dog, 'all', self.today)
        self.assertEqual(
            (stats['training_days'], stats['rest_days'], stats['completed'], stats['partially_completed'],
             stats['skipped'], stats['streak']),
            (2, 1, 2, 1, 1, 3),
        )
        swimming = next(row for row in stats['by_exercise'] if row['exercise'] == 'Swimming')
        self.assertEqual((swimming['sessions'], swimming['total_minutes'], swimming['average_minutes']), (2, 28, 14))

        progress = week_progress(sessions.week_overview(self.dog, self.today))
        self.assertEqual((progress['done'], progress['target']), (1, 2))
