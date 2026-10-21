from datetime import timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError

from plan_app.dog import services as dogs
from plan_app.models import Dog, PlannedActivity, TrainingSession
from plan_app.statistics.services import (
    calorie_goal_progress, longest_streak, personal_records, summarize, week_progress,
)
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

    def test_calories_are_snapshotted_when_recorded(self):
        walking = self.types['Walking']
        old_walk = sessions.record_session(dog=self.dog, day=self.today, planned_activity=self.walk,
                                           status=Status.COMPLETED)
        walking.average_calories_kcal = Decimal('30')
        walking.save()

        sessions.save_session(old_walk, notes='Edited later')
        self.assertEqual(old_walk.calories_kcal, Decimal('27.5'))
        self.assertEqual(summarize(self.dog, 'all', self.today)['total_calories_kcal'], Decimal('27.5'))
        sessions.save_session(old_walk, status=Status.SKIPPED)
        self.assertIsNone(old_walk.calories_kcal)
        sessions.save_session(old_walk, status=Status.COMPLETED, actual_distance_km=Decimal('1'))
        self.assertEqual(old_walk.calories_kcal, Decimal('30'))
        new_walk = sessions.record_session(dog=self.dog, day=self.today, exercise_type=walking,
                                           status=Status.COMPLETED, actual_distance_km=Decimal('2'))
        self.assertEqual(new_walk.calories_kcal, Decimal('60'))

    def test_calories_scale_with_distance_and_duration(self):
        record = sessions.record_session
        ride = record(dog=self.dog, day=self.today, exercise_type=self.types['Bike/Cycle'],
                      status=Status.COMPLETED, actual_distance_km=Decimal('4'))
        self.assertEqual(ride.calories_kcal, Decimal('100'))
        sessions.save_session(ride, actual_distance_km=Decimal('3'))
        self.assertEqual(ride.calories_kcal, Decimal('75'))
        swim = record(dog=self.dog, day=self.today, planned_activity=self.swim, status=Status.COMPLETED,
                      actual_duration_minutes=30)
        self.assertEqual(swim.calories_kcal, Decimal('105'))
        no_distance = record(dog=self.dog, day=self.today, exercise_type=self.types['Hill Climbing'],
                             status=Status.COMPLETED)
        self.assertEqual(no_distance.calories_kcal, Decimal('0'))
        rest = record(dog=self.dog, day=self.today, exercise_type=self.types['Rest'], status=Status.COMPLETED)
        self.assertEqual(rest.calories_kcal, Decimal('0'))

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

    def test_calories_count_non_skipped_sessions(self):
        record = sessions.record_session
        record(dog=self.dog, day=self.today, planned_activity=self.swim, status=Status.COMPLETED)
        record(dog=self.dog, day=self.today, planned_activity=self.walk, status=Status.SKIPPED)
        record(dog=self.dog, day=self.today, exercise_type=self.types['Hill Climbing'],
               status=Status.PARTIALLY_COMPLETED, actual_distance_km=Decimal('2'))

        for period in ('week', 'month', 'all'):
            self.assertEqual(summarize(self.dog, period, self.today)['total_calories_kcal'], Decimal('200'))
        for overview in (sessions.week_overview, sessions.month_overview):
            self.assertEqual(week_progress(overview(self.dog, self.today))['calories'], Decimal('200'))

    def test_personal_records(self):
        record, walking = sessions.record_session, self.types['Walking']
        ride_day = self.today - timedelta(days=14)
        record(dog=self.dog, day=ride_day, exercise_type=self.types['Bike/Cycle'], status=Status.COMPLETED,
               actual_distance_km=Decimal('10'))
        record(dog=self.dog, day=self.today - timedelta(days=3), exercise_type=walking, status=Status.SKIPPED)
        for offset in range(3):
            record(dog=self.dog, day=self.today - timedelta(days=offset), exercise_type=walking,
                   status=Status.COMPLETED, actual_distance_km=Decimal('1'))

        records = personal_records(self.dog, self.today)
        self.assertEqual((records['longest_distance'].actual_distance_km, records['longest_distance'].date),
                         (Decimal('10'), ride_day))
        self.assertEqual(records['best_week'], {
            'start': ride_day - timedelta(days=ride_day.weekday()), 'calories_kcal': Decimal('250'),
        })
        self.assertEqual(records['longest_streak'],
                         {'days': 3, 'start': self.today - timedelta(days=2), 'end': self.today})

    def test_longest_streak(self):
        days = [self.today + timedelta(days=offset) for offset in (0, 1, 2, 4, 5)]
        self.assertEqual(longest_streak(days), {'days': 3, 'start': days[0], 'end': days[2]})
        self.assertIsNone(longest_streak([]))

    def test_calorie_goal_progress(self):
        self.assertIsNone(calorie_goal_progress(Decimal('50'), None))
        self.assertEqual(calorie_goal_progress(Decimal('50'), 200),
                         {'calories': Decimal('50'), 'goal': 200, 'remaining': Decimal('150'), 'percent': 25})
        self.assertEqual(calorie_goal_progress(Decimal('250'), 200)['percent'], 100)


class WeightServiceTests(TrackerTestCase):
    def test_weight_log_reminder_and_current_weight(self):
        self.assertTrue(dogs.weigh_in_status(self.dog, self.today)['due'])
        first, second = self.today - timedelta(days=20), self.today - timedelta(days=5)
        dogs.record_weight(self.dog, first, Decimal('25'))
        self.assertTrue(dogs.weigh_in_status(self.dog, self.today)['due'])
        dogs.record_weight(self.dog, second, Decimal('24.6'))
        dogs.record_weight(self.dog, second, Decimal('24.5'), 'Re-weighed')
        walking = self.types['Walking']
        for offset, km in ((10, '1'), (3, '2')):
            sessions.record_session(dog=self.dog, day=self.today - timedelta(days=offset), exercise_type=walking,
                                    status=Status.COMPLETED, actual_distance_km=Decimal(km))

        self.dog.refresh_from_db()
        self.assertEqual(self.dog.weight_kg, Decimal('24.5'))
        status = dogs.weigh_in_status(self.dog, self.today)
        self.assertEqual((status['due'], status['next_due']), (False, second + dogs.WEIGH_IN_INTERVAL))
        log = dogs.weight_log(self.dog, self.today)
        self.assertEqual(
            [(row['entry'].date, row['change_kg'], row['calories_kcal']) for row in log['rows']],
            [(second, Decimal('-0.5'), Decimal('27.5')), (first, None, None)],
        )
        self.assertEqual(log['calories_since_last'], Decimal('55'))
        with self.assertRaises(ValidationError):
            dogs.record_weight(self.dog, self.today + timedelta(days=1), Decimal('24'))
