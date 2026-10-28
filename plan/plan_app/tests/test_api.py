from rest_framework.test import APIClient

from plan_app.models import Dog

from .base import TrackerTestCase


class ApiTests(TrackerTestCase):
    def setUp(self):
        super().setUp()
        self.api = APIClient()
        self.api.force_authenticate(self.user)

    def test_authentication_required(self):
        self.assertEqual(APIClient().get('/api/dogs').status_code, 403)

    def test_dogs_are_shared_and_camel_cased(self):
        response = self.api.post('/api/dogs', {'name': 'Aayesha', 'weightKg': '28.125'}, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()['weightKg'], '28.125')
        self.assertTrue(Dog.objects.filter(name='Aayesha', owner=self.user).exists())
        self.api.force_authenticate(self.other_user)
        self.assertEqual(self.api.get(f'/api/dogs/{self.dog.pk}').status_code, 200)
        self.assertEqual(self.api.patch(f'/api/dogs/{self.dog.pk}', {'notes': 'Fit'}, format='json').status_code, 200)

    def test_normal_users_cannot_change_exercise_types_or_plans(self):
        self.api.force_authenticate(self.other_user)
        self.assertEqual(self.api.get('/api/exercise-types').status_code, 200)
        self.assertEqual(self.api.post('/api/exercise-types', {'name': 'Sprint'}, format='json').status_code, 403)
        self.assertEqual(self.api.get(f'/api/training-plans/{self.plan.pk}/days').status_code, 200)
        self.assertEqual(self.api.put(f'/api/training-plans/{self.plan.pk}/days', [], format='json').status_code, 403)
        self.assertEqual(self.api.post(f'/api/training-plans/{self.plan.pk}/activate').status_code, 403)
        response = self.api.post('/api/training/sessions', {'plannedActivityId': self.swim.pk, 'status': 'COMPLETED'},
                                 format='json')
        self.assertEqual(response.status_code, 201)

    def test_today_record_and_history_flow(self):
        today = self.api.get('/api/training/today').json()
        self.assertEqual([a['status'] for a in today['activities']], ['PLANNED', 'PLANNED'])
        self.assertEqual(today['activities'][0]['plannedActivityId'], self.swim.pk)

        response = self.api.post('/api/training/sessions', {
            'plannedActivityId': self.swim.pk, 'actualDurationMinutes': 18,
            'status': 'PARTIALLY_COMPLETED', 'notes': 'Good session',
        }, format='json')
        self.assertEqual(response.status_code, 201, response.content)
        self.assertEqual(response.json()['plannedDurationMinutes'], 20)

        today = self.api.get('/api/training/today').json()
        self.assertEqual(today['activities'][0]['status'], 'PARTIALLY_COMPLETED')
        history = self.api.get('/api/training/history', {'status': 'PARTIALLY_COMPLETED'}).json()
        self.assertEqual(history['count'], 1)

    def test_backend_validates_sessions(self):
        skipped = self.api.post('/api/training/sessions', {
            'plannedActivityId': self.swim.pk, 'status': 'SKIPPED', 'actualDurationMinutes': 5,
        }, format='json')
        self.assertEqual(skipped.status_code, 400)
        self.assertIn('actualDurationMinutes', skipped.json())
        bad_status = self.api.post('/api/training/sessions', {
            'plannedActivityId': self.swim.pk, 'status': 'PLANNED',
        }, format='json')
        self.assertEqual(bad_status.status_code, 400)
        other_dog = Dog.objects.create(owner=self.other_user, name='Rex')
        mismatched = self.api.post('/api/training/sessions', {
            'dogId': other_dog.pk, 'plannedActivityId': self.swim.pk, 'status': 'COMPLETED',
        }, format='json')
        self.assertEqual(mismatched.status_code, 400)

    def test_plan_days_can_be_replaced(self):
        url = f'/api/training-plans/{self.plan.pk}/days'
        response = self.api.put(url, [{'dayOfWeek': 0, 'activities': [
            {'exerciseTypeId': self.types['Running'].pk, 'plannedDistanceKm': '5', 'plannedDurationMinutes': 30},
            {'exerciseTypeId': self.types['Hill Climbing'].pk, 'plannedRepetitions': 6},
        ]}], format='json')
        self.assertEqual(response.status_code, 200, response.content)
        monday = next(day for day in response.json() if day['dayOfWeek'] == 0)
        self.assertEqual([a['summary'] for a in monday['activities']],
                         ['Running — 5 km · 30 min', 'Hill Climbing — 6 reps'])
        entry = self.dog.audit_entries.get(username='owner')
        self.assertEqual([(c['field'], c['new']) for c in entry.changes],
                         [('Monday', 'Running — 5 km · 30 min; Hill Climbing — 6 reps')])
        self.api.put(url, [{'dayOfWeek': 0, 'activities': monday['activities']}], format='json')
        self.assertEqual(self.dog.audit_entries.filter(username='owner').count(), 1)

    def test_plan_dates_are_validated(self):
        response = self.api.post('/api/training-plans', {
            'dogId': self.dog.pk, 'name': 'Bad', 'startDate': '2026-10-10', 'endDate': '2026-10-01',
        }, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('endDate', response.json())

    def test_statistics(self):
        self.api.post('/api/training/sessions', {'plannedActivityId': self.swim.pk, 'status': 'COMPLETED'},
                      format='json')
        stats = self.api.get('/api/statistics', {'period': 'week'}).json()
        self.assertEqual((stats['trainingDays'], stats['completed'], stats['totalMinutes']), (1, 1, 20))
        self.assertEqual(stats['byExercise'][0]['exercise'], 'Swimming')
