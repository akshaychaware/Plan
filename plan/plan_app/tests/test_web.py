from datetime import timedelta
from decimal import Decimal

from django.urls import reverse

from plan_app.models import Dog, TrainingSession

from .base import TrackerTestCase


class WebTests(TrackerTestCase):
    def setUp(self):
        self.client.force_login(self.user)

    def url(self, name, *args):
        return reverse(f'plan_app:{name}', args=[self.dog.pk, *args])

    def record_url(self, day, activity=''):
        return f"{self.url('session_record')}?date={day:%Y-%m-%d}&activity={activity}"

    def test_login_required(self):
        self.client.logout()
        self.assertRedirects(self.client.get(self.url('dog_detail')), f"{reverse('login')}?next=/dogs/{self.dog.pk}/")

    def test_normal_user_sees_everything_but_plan_and_history_are_read_only(self):
        self.client.force_login(self.other_user)
        self.assertContains(self.client.get(reverse('plan_app:dog_list')), 'Luna')
        self.assertContains(self.client.get(self.url('dog_detail')), 'View plan')

        plan_page = self.client.get(self.url('plan_edit'))
        self.assertContains(plan_page, 'Read only')
        self.assertNotContains(plan_page, 'day0-TOTAL_FORMS')
        self.assertEqual(self.client.post(self.url('plan_edit'), {}).status_code, 403)
        self.assertEqual(self.client.post(self.url('plan_new'), {}).status_code, 403)

        self.client.post(self.url('session_quick_log', self.swim.pk))
        session = self.dog.sessions.get()
        self.assertNotContains(self.client.get(self.url('session_history')), self.url('session_edit', session.pk))
        response = self.client.post(self.url('session_edit', session.pk), {
            'exercise_type': self.swim.exercise_type_id, 'status': 'PARTIALLY_COMPLETED', 'actual_duration_minutes': 12,
        })
        self.assertEqual(response.status_code, 302)
        session.refresh_from_db()
        self.assertEqual(session.status, 'PARTIALLY_COMPLETED')

    def test_dashboard_shows_todays_activities(self):
        response = self.client.get(self.url('dog_detail'), {'period': 'month'})
        self.assertContains(response, 'Swimming — 20 min')
        self.assertContains(response, 'Walking — 1 km')
        self.assertEqual(response.context['stats']['period'], 'month')
        self.assertContains(response, 'Monthly progress')
        self.assertContains(response, f'class="back-link" href="{reverse("plan_app:dog_list")}"')
        self.assertIn(response.context['month_progress']['target'], (8, 10))

    def test_record_flow_walks_through_each_planned_activity(self):
        self.assertEqual(self.client.get(self.record_url(self.today)).context['session'].planned_activity, self.swim)
        response = self.client.post(self.record_url(self.today, self.swim.pk), {
            'exercise_type': self.swim.exercise_type_id, 'status': 'COMPLETED', 'actual_duration_minutes': 18,
        })
        self.assertRedirects(response, f"{self.url('session_record')}?date={self.today:%Y-%m-%d}")
        response = self.client.post(self.record_url(self.today, self.walk.pk), {
            'exercise_type': self.walk.exercise_type_id, 'status': 'SKIPPED', 'notes': 'Tired',
        })
        self.assertRedirects(response, self.url('dog_detail'))
        self.assertEqual(
            list(self.dog.sessions.order_by('planned_activity__sequence').values_list('status', flat=True)),
            ['COMPLETED', 'SKIPPED'],
        )
        session = self.dog.sessions.get(planned_activity=self.swim)
        self.assertEqual(self.client.get(self.url('session_edit', session.pk)).context['session'], session)

    def test_extra_activity_and_future_date(self):
        self.client.post(self.record_url(self.today, 'extra'), {
            'exercise_type': self.types['Running'].pk, 'status': 'COMPLETED', 'actual_duration_minutes': 15,
        })
        self.assertTrue(self.dog.sessions.filter(planned_activity__isnull=True, exercise_type__name='Running').exists())
        response = self.client.get(self.record_url(self.today + timedelta(days=1)))
        self.assertRedirects(response, self.url('session_record'))

    def test_quick_log(self):
        url = self.url('session_quick_log', self.swim.pk)
        self.assertEqual(self.client.get(url).status_code, 405)
        self.client.post(url)
        self.client.post(url)
        self.assertEqual(self.dog.sessions.filter(status=TrainingSession.Status.COMPLETED).count(), 1)

    def test_plan_editor_creates_plan_with_activities(self):
        dog = Dog.objects.create(owner=self.user, name='Aayesha')
        data = {'plan-name': 'Weekly plan', 'plan-start_date': f'{self.today:%Y-%m-%d}', 'plan-end_date': ''}
        for day in range(7):
            data |= {f'day{day}-TOTAL_FORMS': '0', f'day{day}-INITIAL_FORMS': '0',
                     f'day{day}-MIN_NUM_FORMS': '0', f'day{day}-MAX_NUM_FORMS': '1000'}
        data |= {'day1-TOTAL_FORMS': '2',
                 'day1-0-exercise_type': self.types['Swimming'].pk, 'day1-0-planned_duration_minutes': '20',
                 'day1-0-notes': '10 min + 5 min rest + 10 min',
                 'day1-1-exercise_type': self.types['Walking'].pk, 'day1-1-planned_distance_km': '1'}
        url = reverse('plan_app:plan_edit', args=[dog.pk])
        self.assertContains(self.client.get(url), 'day0-TOTAL_FORMS')
        self.assertRedirects(self.client.post(url, data), reverse('plan_app:dog_detail', args=[dog.pk]))
        plan = dog.training_plans.get()
        tuesday = plan.days.get(day_of_week=1)
        self.assertEqual([a.summary for a in tuesday.activities.all()], ['Swimming — 20 min', 'Walking — 1 km'])
        self.assertEqual(plan.days.count(), 7)

    def test_dog_profile_edit_and_history(self):
        self.client.post(self.url('dog_edit'), {'name': 'Luna', 'breed': 'Greyhound', 'weight_kg': '25.400'})
        self.dog.refresh_from_db()
        self.assertEqual(str(self.dog.weight_kg), '25.400')
        self.client.post(self.url('session_quick_log', self.swim.pk))
        response = self.client.get(self.url('session_history'), {'status': 'COMPLETED'})
        self.assertEqual(len(response.context['page']), 1)
        self.assertContains(response, '70 kcal')
        self.client.post(self.url('session_quick_log', self.walk.pk))
        days = self.client.get(self.url('session_history')).context['days']
        self.assertEqual([(len(d['sessions']), d['calories_kcal']) for d in days], [(2, Decimal('97.5'))])

    def test_pwa_endpoints(self):
        self.client.logout()
        response = self.client.get(reverse('plan_app:service_worker'))
        self.assertEqual(response['Content-Type'], 'application/javascript')
        self.assertContains(response, 'training-tracker-v2')
        self.assertEqual(self.client.get(reverse('plan_app:offline')).status_code, 200)
