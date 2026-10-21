from django.contrib import admin

from .dog.services import sync_current_weight
from .models import Dog, ExerciseType, PlannedActivity, TrainingPlan, TrainingPlanDay, TrainingSession, WeightEntry
from .training_session.services import save_session


@admin.register(Dog)
class DogAdmin(admin.ModelAdmin):
    list_display = ['name', 'breed', 'date_of_birth', 'weight_kg', 'owner']


@admin.register(WeightEntry)
class WeightEntryAdmin(admin.ModelAdmin):
    list_display = ['dog', 'date', 'weight_kg', 'notes']
    list_filter = ['dog']
    date_hierarchy = 'date'

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        sync_current_weight(obj.dog)

    def delete_model(self, request, obj):
        super().delete_model(request, obj)
        sync_current_weight(obj.dog)


@admin.register(ExerciseType)
class ExerciseTypeAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'tracks_metrics', 'average_calories_kcal', 'calories_basis', 'calories_basis_amount', 'description',
    ]


class TrainingPlanDayInline(admin.TabularInline):
    model = TrainingPlanDay
    extra = 0
    show_change_link = True


@admin.register(TrainingPlan)
class TrainingPlanAdmin(admin.ModelAdmin):
    list_display = ['name', 'dog', 'start_date', 'end_date', 'is_active']
    list_filter = ['is_active', 'dog']
    inlines = [TrainingPlanDayInline]


class PlannedActivityInline(admin.TabularInline):
    model = PlannedActivity
    extra = 0


@admin.register(TrainingPlanDay)
class TrainingPlanDayAdmin(admin.ModelAdmin):
    list_display = ['training_plan', 'day_of_week']
    list_filter = ['training_plan']
    inlines = [PlannedActivityInline]


@admin.register(TrainingSession)
class TrainingSessionAdmin(admin.ModelAdmin):
    list_display = [
        'dog', 'date', 'exercise_type', 'actual_duration_minutes', 'actual_distance_km', 'actual_repetitions', 'status',
        'calories_kcal',
    ]
    list_filter = ['dog', 'status', 'exercise_type']
    date_hierarchy = 'date'
    readonly_fields = ['calories_kcal']

    def save_model(self, request, obj, form, change):
        save_session(obj)
