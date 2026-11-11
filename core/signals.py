from django.db.models.signals import post_save
from django.dispatch import receiver

from core.models import Notificacao, Post, Projeto


def notificar_equipe(projeto, tipo, using, post=None):
    equipe = projeto.equipe
    # O mesmo usuário pode ter os dois perfis: recebe apenas um aviso por evento.
    destinatarios = set(
        equipe.alunos.using(using).filter(ativo=True, user__is_active=True).values_list('user_id', flat=True)
    )
    destinatarios.update(
        equipe.professores.using(using).filter(ativo=True, user__is_active=True).values_list('user_id', flat=True)
    )
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
        notificar_equipe(instance, Notificacao.Tipo.PROJETO, using)


@receiver(post_save, sender=Post, dispatch_uid='notificar_novo_post')
def novo_post(sender, instance, created, raw, using, **kwargs):
    if created and not raw and instance.projeto_id:
        notificar_equipe(instance.projeto, Notificacao.Tipo.POST, using, post=instance)
