import django.db.models.deletion
from django.db import migrations, models


def notify_pending_invitations(apps, schema_editor):
    Convite = apps.get_model('core', 'Convite')
    Notificacao = apps.get_model('core', 'Notificacao')
    alias = schema_editor.connection.alias
    pending = Convite.objects.using(alias).filter(status='P', notificacao__isnull=True).select_related(
        'aluno', 'professor', 'equipe',
    )
    for convite in pending.iterator():
        recipient = convite.aluno if convite.aluno_id else convite.professor
        if recipient is not None:
            Notificacao.objects.using(alias).create(
                destinatario_id=recipient.user_id,
                convite_id=convite.pk,
                tipo='CONVITE',
                titulo='Convite para participar de uma equipe',
                mensagem=f'A equipe {convite.equipe.nome} convidou você para participar.',
            )


def remove_invitation_notifications(apps, schema_editor):
    Notificacao = apps.get_model('core', 'Notificacao')
    Notificacao.objects.using(schema_editor.connection.alias).filter(tipo='CONVITE').delete()


class Migration(migrations.Migration):
    dependencies = [('core', '0023_professor_cpf_optional')]

    operations = [
        migrations.AlterField(
            model_name='notificacao',
            name='projeto',
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.CASCADE,
                related_name='notificacoes', to='core.projeto',
            ),
        ),
        migrations.AddField(
            model_name='notificacao',
            name='convite',
            field=models.OneToOneField(
                blank=True, null=True, on_delete=django.db.models.deletion.CASCADE,
                related_name='notificacao', to='core.convite',
            ),
        ),
        migrations.AlterField(
            model_name='notificacao',
            name='tipo',
            field=models.CharField(
                choices=[('PROJETO', 'Novo projeto'), ('POST', 'Novo post'), ('CONVITE', 'Convite para equipe')],
                max_length=10,
            ),
        ),
        migrations.RunPython(notify_pending_invitations, remove_invitation_notifications),
    ]
