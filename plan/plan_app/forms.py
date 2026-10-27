from django import forms
from django.utils.translation import gettext_lazy as _

from .models import Dog, PlannedActivity, TrainingPlan, TrainingPlanDay, TrainingSession, WeightEntry

DATE_INPUT = forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d')


class ExerciseTypeSelect(forms.Select):
    def create_option(self, name, value, *args, **kwargs):
        option = super().create_option(name, value, *args, **kwargs)
        if value and not value.instance.tracks_metrics:
            option['attrs']['data-no-metrics'] = ''
        return option


class DogForm(forms.ModelForm):
    class Meta:
        model = Dog
        fields = ['name', 'breed', 'date_of_birth', 'weight_kg', 'weekly_calorie_goal_kcal', 'notes']
        widgets = {'date_of_birth': DATE_INPUT, 'notes': forms.Textarea(attrs={'rows': 3})}


class WeightEntryForm(forms.ModelForm):
    class Meta:
        model = WeightEntry
        fields = ['date', 'weight_kg', 'notes']
        widgets = {'date': DATE_INPUT}


class TrainingPlanForm(forms.ModelForm):
    class Meta:
        model = TrainingPlan
        fields = ['name', 'start_date', 'end_date']
        widgets = {'start_date': DATE_INPUT, 'end_date': DATE_INPUT}


class NewTrainingPlanForm(forms.Form):
    name = forms.CharField(label=_('Name'), max_length=100)
    start_date = forms.DateField(label=_('Start date'), widget=DATE_INPUT)


class PlannedActivityForm(forms.ModelForm):
    class Meta:
        model = PlannedActivity
        fields = ['exercise_type', 'planned_duration_minutes', 'planned_distance_km', 'planned_repetitions', 'notes']
        widgets = {
            'exercise_type': ExerciseTypeSelect,
            'notes': forms.TextInput(attrs={'placeholder': _('e.g. 10 min + 5 min rest + 10 min')}),
        }

    def __init__(self, *args, exercise_choices=None, **kwargs):
        super().__init__(*args, **kwargs)
        if exercise_choices is not None:
            self.fields['exercise_type'].choices = exercise_choices


class BasePlannedActivityFormSet(forms.BaseInlineFormSet):
    def get_queryset(self):
        if 'activities' in getattr(self.instance, '_prefetched_objects_cache', {}):
            return self.instance.activities.all()
        return super().get_queryset()


PlannedActivityFormSet = forms.inlineformset_factory(
    TrainingPlanDay, PlannedActivity, form=PlannedActivityForm, formset=BasePlannedActivityFormSet,
    extra=0, can_delete=True,
)


class TrainingSessionForm(forms.ModelForm):
    status = forms.ChoiceField(label=_('Status'), choices=TrainingSession.Status.choices, widget=forms.RadioSelect)

    class Meta:
        model = TrainingSession
        fields = [
            'exercise_type', 'status', 'actual_duration_minutes', 'actual_distance_km', 'actual_repetitions', 'notes',
        ]
        widgets = {
            'exercise_type': ExerciseTypeSelect,
            'notes': forms.Textarea(attrs={'rows': 3, 'placeholder': _('How did the session go?')}),
        }
