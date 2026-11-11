from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('core', '0018_merge_home_highlights')]

    operations = [
        migrations.AddField(
            model_name='user', name='password_reset_code_hash',
            field=models.CharField(max_length=128, blank=True, default=''),
        ),
        migrations.AddField(
            model_name='user', name='password_reset_created_at',
            field=models.DateTimeField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='user', name='password_reset_attempts',
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='user', name='password_reset_token_hash',
            field=models.CharField(max_length=128, blank=True, default=''),
        ),
    ]
