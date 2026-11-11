from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [('core', '0014_alter_postcomment_id_alter_postlike_id')]

    operations = [
        migrations.AddField(
            model_name='equipe',
            name='criador',
            field=models.ForeignKey(
                to='core.professor', related_name='equipes_criadas',
                on_delete=django.db.models.deletion.PROTECT,
                null=True, blank=True,
            ),
        ),
    ]
