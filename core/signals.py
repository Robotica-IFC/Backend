from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from core.models import Convite, Notificacao, Post, Projeto


def notificar_equipe(projeto, tipo, using, post=None, autor_id=None):
    equipe = projeto.equipe
    # O mesmo usuário pode ter os dois perfis: recebe apenas um aviso por evento.
    destinatarios = set(
        equipe.alunos.using(using).filter(ativo=True, user__is_active=True).values_list('user_id', flat=True)
    )
    destinatarios.update(
        equipe.professores.using(using).filter(ativo=True, user__is_active=True).values_list('user_id', flat=True)
    )
    destinatarios.discard(autor_id)
    titulo = 'Novo projeto na sua equipe' if tipo == Notificacao.Tipo.PROJETO else 'Novo post no projeto'
    mensagem = (
        f'A equipe {equipe.nome} criou o projeto {projeto.titulo}.'
        if tipo == Notificacao.Tipo.PROJETO
        else f'Uma nova publicação foi adicionada ao projeto {projeto.titulo}, da equipe {equipe.nome}.'
    )
    Notificacao.objects.using(using).bulk_create([
        Notificacao(
            destinatario_id=user_id, projeto=projeto, post=post,
            tipo=tipo, titulo=titulo, mensagem=mensagem,
        )
        for user_id in destinatarios
    ])


@receiver(post_save, sender=Projeto, dispatch_uid='notificar_novo_projeto')
def novo_projeto(sender, instance, created, raw, using, **kwargs):
    if created and not raw:
        notificar_equipe(
            instance, Notificacao.Tipo.PROJETO, using,
            autor_id=getattr(instance, '_autor_notificacao_id', None),
        )


@receiver(post_save, sender=Post, dispatch_uid='notificar_novo_post')
def novo_post(sender, instance, created, raw, using, **kwargs):
    if created and not raw and instance.projeto_id:
        criador = instance.aluno_criador or instance.professor_criador
        notificar_equipe(
            instance.projeto, Notificacao.Tipo.POST, using, post=instance,
            autor_id=criador.user_id if criador else None,
        )


@receiver(post_save, sender=Convite, dispatch_uid='notificar_convite_equipe')
def convite_equipe(sender, instance, created, raw, using, **kwargs):
    if raw:
        return
    if created and instance.status == Convite.StatusChoices.PENDENTE:
        destinatario = instance.aluno if instance.aluno_id else instance.professor
        if destinatario is not None:
            Notificacao.objects.using(using).create(
                destinatario_id=destinatario.user_id,
                convite=instance,
                tipo=Notificacao.Tipo.CONVITE,
                titulo='Convite para participar de uma equipe',
                mensagem=f'A equipe {instance.equipe.nome} convidou você para participar.',
            )
    elif instance.status != Convite.StatusChoices.PENDENTE:
        Notificacao.objects.using(using).filter(convite=instance, lida_em__isnull=True).update(
            lida_em=timezone.now(),
        )
