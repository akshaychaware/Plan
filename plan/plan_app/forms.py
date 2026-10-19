from django import forms

from .models import Dog, PlannedActivity, TrainingPlan, TrainingPlanDay, TrainingSession

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
        fields = ['name', 'breed', 'date_of_birth', 'weight_kg', 'notes']
        widgets = {'date_of_birth': DATE_INPUT, 'notes': forms.Textarea(attrs={'rows': 3})}


class TrainingPlanForm(forms.ModelForm):
    class Meta:
        model = TrainingPlan
        fields = ['name', 'start_date', 'end_date']
        widgets = {'start_date': DATE_INPUT, 'end_date': DATE_INPUT}


class NewTrainingPlanForm(forms.Form):
    name = forms.CharField(max_length=100)
    start_date = forms.DateField(widget=DATE_INPUT)


class PlannedActivityForm(forms.ModelForm):
    class Meta:
        model = PlannedActivity
        fields = ['exercise_type', 'planned_duration_minutes', 'planned_distance_km', 'planned_repetitions', 'notes']
        widgets = {
            'exercise_type': ExerciseTypeSelect,
            'notes': forms.TextInput(attrs={'placeholder': 'e.g. 10 min + 5 min rest + 10 min'}),
        }


PlannedActivityFormSet = forms.inlineformset_factory(
    TrainingPlanDay, PlannedActivity, form=PlannedActivityForm, extra=0, can_delete=True
)


class TrainingSessionForm(forms.ModelForm):
    status = forms.ChoiceField(choices=TrainingSession.Status.choices, widget=forms.RadioSelect)

    class Meta:
        model = TrainingSession
        fields = [
            'exercise_type', 'status', 'actual_duration_minutes', 'actual_distance_km', 'actual_repetitions', 'notes',
        ]
        widgets = {
            'exercise_type': ExerciseTypeSelect,
            'notes': forms.Textarea(attrs={'rows': 3, 'placeholder': 'How did the session go?'}),
        }
