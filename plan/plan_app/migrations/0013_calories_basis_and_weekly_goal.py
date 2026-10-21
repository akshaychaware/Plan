import django.core.validators
from decimal import Decimal
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('plan_app', '0012_trainingsession_calories_kcal'),
    ]

    operations = [
        migrations.AddField(
            model_name='exercisetype',
            name='calories_basis',
            field=models.CharField(choices=[('SESSION', 'Per session'), ('DISTANCE', 'Per distance (km)'), ('DURATION', 'Per duration (min)')], default='SESSION', max_length=10),
        ),
        migrations.AddField(
            model_name='exercisetype',
            name='calories_basis_amount',
            field=models.DecimalField(blank=True, decimal_places=2, help_text='The km or minutes the average calories refer to, e.g. 2 for "50 kcal per 2 km".', max_digits=6, null=True, validators=[django.core.validators.MinValueValidator(Decimal('0.01'))], verbose_name='calories basis amount'),
        ),
        migrations.AddField(
            model_name='dog',
            name='weekly_calorie_goal_kcal',
            field=models.PositiveIntegerField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(100000)], verbose_name='weekly calorie goal (kcal)'),
        ),
    ]
