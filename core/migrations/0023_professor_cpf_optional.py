from django.db import migrations, models


def normalize_empty_cpf(apps, schema_editor):
    Professor = apps.get_model('core', 'Professor')
    Professor.objects.using(schema_editor.connection.alias).filter(cpf='').update(cpf=None)


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0022_merge_20261117_0845'),
    ]

    operations = [
        migrations.AlterField(
            model_name='professor',
            name='cpf',
            field=models.CharField(blank=True, max_length=11, null=True, unique=True),
        ),
        migrations.RunPython(normalize_empty_cpf, migrations.RunPython.noop),
    ]
