from django.db import migrations, models


def preserve_existing_accounts(apps, schema_editor):
    # Existing accounts keep access; only new registrations require confirmation.
    apps.get_model('core', 'User').objects.using(schema_editor.connection.alias).update(email_verified=True)
    for name in ('Aluno', 'Professor'):
        apps.get_model('core', name).objects.using(schema_editor.connection.alias).update(email_verificado=True)


class Migration(migrations.Migration):
    dependencies = [('core', '0009_alter_item_categoria')]
    operations = [
        migrations.AddField(model_name='user', name='email_verified', field=models.BooleanField(default=False)),
        migrations.AddField(model_name='user', name='verification_code_hash', field=models.CharField(max_length=128, blank=True, default='')),
        migrations.AddField(model_name='user', name='verification_code_created_at', field=models.DateTimeField(null=True, blank=True)),
        migrations.AddField(model_name='user', name='verification_attempts', field=models.PositiveSmallIntegerField(default=0)),
        migrations.RunPython(preserve_existing_accounts, migrations.RunPython.noop),
    ]
