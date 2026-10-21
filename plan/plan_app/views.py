from datetime import date, timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.formats import date_format
from django.utils.translation import gettext as _
from django.views.decorators.http import require_http_methods, require_POST

from .core.access import require_admin
from .dog import services as dog_services
from .forms import (
    DogForm, NewTrainingPlanForm, PlannedActivityFormSet, TrainingPlanForm, TrainingSessionForm, WeightEntryForm,
)
from .models import Dog, TrainingPlan, TrainingSession, TrainingPlanDay, Weekday
from .statistics.services import PERIODS, calorie_goal_progress, personal_records, summarize, week_progress
from .training_plan import services as plan_services
from .training_session import services as session_services


def _get_dog(request, pk):
    return get_object_or_404(Dog, pk=pk)


@login_required
def dog_list(request):
    return render(request, 'plan_app/dog_list.html', {'dogs': Dog.objects.all()})


@login_required
@require_http_methods(['GET', 'POST'])
def dog_form(request, pk=None):
    dog = _get_dog(request, pk) if pk else Dog(owner=request.user)
    form = DogForm(request.POST or None, instance=dog)
    if request.method == 'POST' and form.is_valid():
        form.save()
        if pk:
            messages.success(request, _('%(dog)s updated.') % {'dog': dog})
            return redirect('plan_app:dog_detail', pk=dog.pk)
        messages.success(request, _('%(dog)s added. Now configure the weekly plan.') % {'dog': dog})
        return redirect('plan_app:plan_edit', pk=dog.pk)
    return render(request, 'plan_app/dog_form.html', {'form': form, 'dog': dog if pk else None})


@login_required
def dog_detail(request, pk):
    dog = _get_dog(request, pk)
    today = timezone.localdate()
    period = request.GET.get('period', 'week')
    period = period if period in PERIODS else 'week'
    week = session_services.week_overview(dog, today)
    progress = week_progress(week)
    return render(request, 'plan_app/dog_detail.html', {
        'dog': dog,
        'today': today,
        'today_entry': week[today.weekday()],
        'week': week,
        'days_window': session_services.overview(dog, today - timedelta(days=2), today + timedelta(days=3)),
        'progress': progress,
        'calorie_goal': calorie_goal_progress(progress['calories'], dog.weekly_calorie_goal_kcal),
        'month_progress': week_progress(session_services.month_overview(dog, today)),
        'stats': summarize(dog, period, today),
        'records': personal_records(dog, today),
        'weigh_in': dog_services.weigh_in_status(dog, today),
        'period': period,
        'periods': PERIODS,
        'plan': plan_services.active_plan(dog),
    })


@login_required
@require_http_methods(['GET', 'POST'])
def weight_log(request, pk):
    dog = _get_dog(request, pk)
    today = timezone.localdate()
    form = WeightEntryForm(request.POST or None, initial={'date': today})
    if request.method == 'POST' and form.is_valid():
        dog_services.record_weight(dog, **form.cleaned_data)
        messages.success(request, _('Weight for %(dog)s on %(date)s saved.') % {
            'dog': dog, 'date': date_format(form.cleaned_data['date'], 'j M Y'),
        })
        return redirect('plan_app:weight_log', pk=dog.pk)
    return render(request, 'plan_app/weight_log.html', {
        'dog': dog,
        'form': form,
        'log': dog_services.weight_log(dog, today),
        'weigh_in': dog_services.weigh_in_status(dog, today),
    })


@login_required
@require_POST
def session_quick_log(request, pk, activity_pk):
    dog = _get_dog(request, pk)
    today = timezone.localdate()
    planned = plan_services.planned_activities_for(dog, today).filter(pk=activity_pk).first()
    if planned is None or session_services.complete_as_planned(dog, planned, today) is None:
        messages.info(request, _('Nothing to quick-log for that activity.'))
    else:
        messages.success(request, _('%(activity)s logged as completed.') % {'activity': planned.exercise_type})
    return redirect('plan_app:dog_detail', pk=dog.pk)


@login_required
@require_http_methods(['GET', 'POST'])
def plan_edit(request, pk):
    dog = _get_dog(request, pk)
    if request.method == 'POST':
        require_admin(request.user)
    plan = plan_services.active_plan(dog) or TrainingPlan(dog=dog, start_date=timezone.localdate())
    days = {day.day_of_week: day for day in plan.days.all()} if plan.pk else {}
    plan_form = TrainingPlanForm(request.POST or None, instance=plan, prefix='plan')
    formsets = [
        PlannedActivityFormSet(
            request.POST or None,
            instance=days.get(day, TrainingPlanDay(training_plan=plan, day_of_week=day)),
            prefix=f'day{day}',
        )
        for day in Weekday.values
    ]
    if request.method == 'POST' and all([plan_form.is_valid(), *[fs.is_valid() for fs in formsets]]):
        plan_services.save_plan(plan_form.save(commit=False))
        plan_services.save_week(plan, {
            formset.instance.day_of_week: [
                {**{field: form.cleaned_data.get(field) for field in plan_services.ACTIVITY_FIELDS},
                 'id': form.instance.pk}
                for form in formset.forms if form.cleaned_data and not form.cleaned_data.get('DELETE')
            ]
            for formset in formsets
        })
        messages.success(request, _('Weekly plan saved.'))
        return redirect('plan_app:dog_detail', pk=dog.pk)
    return render(request, 'plan_app/plan_form.html', {
        'dog': dog, 'plan': plan, 'plan_form': plan_form, 'formsets': formsets,
        'new_plan_form': NewTrainingPlanForm(initial={'start_date': timezone.localdate()}),
    })


@login_required
@require_POST
def plan_new(request, pk):
    dog = _get_dog(request, pk)
    require_admin(request.user)
    form = NewTrainingPlanForm(request.POST)
    if form.is_valid():
        try:
            plan_services.start_new_plan(dog, **form.cleaned_data)
            messages.success(request, _('New plan “%(name)s” started.') % {'name': form.cleaned_data['name']})
        except ValidationError as error:
            messages.error(request, ' '.join(error.messages))
    else:
        messages.error(request, _('Enter a plan name and start date.'))
    return redirect('plan_app:plan_edit', pk=dog.pk)


@login_required
@require_http_methods(['GET', 'POST'])
def session_record(request, pk, session_pk=None):
    dog = _get_dog(request, pk)
    today = timezone.localdate()
    if session_pk:
        session = get_object_or_404(dog.sessions, pk=session_pk)
        day = session.date
        entry = session_services.day_entries(dog, day)
    else:
        try:
            day = date.fromisoformat(request.GET.get('date', ''))
        except ValueError:
            day = today
        if day > today:
            messages.error(request, _('Sessions cannot be recorded for future dates.'))
            return redirect('plan_app:session_record', pk=dog.pk)
        entry = session_services.day_entries(dog, day)
        selected = request.GET.get('activity')
        planned_items = [a for a in entry['activities'] if a['planned']]
        match = None if selected == 'extra' else (
            next((a for a in planned_items if str(a['planned'].pk) == selected), None)
            or next((a for a in planned_items if not a['session']), None)
            or next(iter(planned_items), None)
        )
        session = (match and match['session']) or TrainingSession.from_planned(dog, day, match and match['planned'])

    form = TrainingSessionForm(request.POST or None, instance=session)
    if request.method == 'POST' and form.is_valid():
        session_services.save_session(form.save(commit=False))
        messages.success(request, _('%(activity)s on %(date)s saved.') % {
            'activity': session.exercise_type, 'date': date_format(day, 'j M Y'),
        })
        remaining = any(a['planned'] and not a['session'] for a in session_services.day_entries(dog, day)['activities'])
        if remaining:
            return redirect(f"{reverse('plan_app:session_record', args=[dog.pk])}?date={day:%Y-%m-%d}")
        return redirect('plan_app:dog_detail', pk=dog.pk)
    return render(request, 'plan_app/session_form.html', {
        'dog': dog, 'form': form, 'session': session, 'entry': entry, 'day': day, 'today': today,
    })


@login_required
def session_history(request, pk):
    dog = _get_dog(request, pk)
    sessions = dog.sessions.select_related('exercise_type', 'planned_exercise_type')
    status = request.GET.get('status', '')
    if status in TrainingSession.Status.values:
        sessions = sessions.filter(status=status)
    else:
        status = ''
    dates = sessions.order_by('-date').values_list('date', flat=True).distinct()
    page = Paginator(dates, 20).get_page(request.GET.get('page'))
    return render(request, 'plan_app/session_history.html', {
        'dog': dog,
        'page': page,
        'days': session_services.history_days(sessions, page),
        'status': status,
        'statuses': TrainingSession.Status.choices,
    })
