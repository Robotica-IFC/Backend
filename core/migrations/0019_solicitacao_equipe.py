from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0018_merge_home_highlights'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='SolicitacaoEquipe',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('P', 'Pendente'), ('A', 'Aceita'), ('R', 'Recusada')], default='P', max_length=1)),
                ('criada_em', models.DateTimeField(auto_now_add=True)),
                ('equipe', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='solicitacoes', to='core.equipe')),
                ('solicitante', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='solicitacoes_equipes', to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['-criada_em']},
        ),
        migrations.AddConstraint(
            model_name='solicitacaoequipe',
            constraint=models.UniqueConstraint(fields=('equipe', 'solicitante'), name='unique_solicitacao_equipe_usuario'),
        ),
    ]
