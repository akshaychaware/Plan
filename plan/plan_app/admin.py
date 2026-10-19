from django.contrib import admin

from .models import Dog, ExerciseType, PlannedActivity, TrainingPlan, TrainingPlanDay, TrainingSession


@admin.register(Dog)
class DogAdmin(admin.ModelAdmin):
    list_display = ['name', 'breed', 'date_of_birth', 'weight_kg', 'owner']


@admin.register(ExerciseType)
class ExerciseTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'tracks_metrics', 'description']


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
    ]
    list_filter = ['dog', 'status', 'exercise_type']
    date_hierarchy = 'date'
