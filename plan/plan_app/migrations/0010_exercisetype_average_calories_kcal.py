import django.core.validators
from decimal import Decimal
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('plan_app', '0009_dog_weight_three_decimals'),
    ]

    operations = [
        migrations.AddField(
            model_name='exercisetype',
            name='average_calories_kcal',
            field=models.DecimalField(blank=True, decimal_places=1, max_digits=6, null=True, validators=[django.core.validators.MinValueValidator(Decimal('0'))], verbose_name='average calories (kcal)'),
        ),
    ]
