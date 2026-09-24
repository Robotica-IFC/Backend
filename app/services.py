from django.db import transaction, IntegrityError
from django.utils import timezone

from core.models.convite import (
    Convite,
    maximo_convites_equipe,
    maximo_tentativas,
)
from . import email


class ConviteError(Exception):
    """Erro de regra de negócio para a view transformar em resposta 400."""


def professor_e_membro_equipe(usuario, equipe):
    return equipe.professores.filter(id=usuario.id).exists()


@transaction.atomic
def criar_convite(*, equipe, aluno, enviadoPor):
    if not professor_e_membro_equipe(enviadoPor, equipe):
        raise ConviteError(
            "Só um professor participante da equipe pode enviar convites."
        )

    # Bloqueia a equipe enquanto verificamos/criamos o convite.
    equipe_bloqueada = (
        equipe.__class__.objects
        .select_for_update()
        .get(pk=equipe.pk)
    )

    if equipe_bloqueada.alunos.filter(id=aluno.id).exists():
        raise ConviteError(
            "Esse aluno já faz parte dessa equipe."
        )

    convites_ativos = Convite.objects.filter(
        equipe=equipe_bloqueada,
        status__in=[
            Convite.Status.PENDING,
            Convite.Status.AWAITING_CONFIRMATION,
        ],
    ).count()

    if convites_ativos >= maximo_convites_equipe:
        raise ConviteError(
            f"Limite de {maximo_convites_equipe} convites pendentes atingido. "
            "Aguarde os alunos responderem antes de enviar mais."
        )

    convite_ativo = Convite.objects.filter(
        equipe=equipe_bloqueada,
        aluno=aluno,
        status__in=[
            Convite.Status.PENDING,
            Convite.Status.AWAITING_CONFIRMATION,
        ],
    ).exists()

    if convite_ativo:
        raise ConviteError(
            "Já existe um convite ativo para esse aluno nessa equipe."
        )

    try:
        convite = Convite.objects.create(
            equipe=equipe_bloqueada,
            aluno=aluno,
            enviadoPor=enviadoPor,
        )
    except IntegrityError:
        raise ConviteError(
            "Já existe um convite ativo para esse aluno nessa equipe."
        )

    email.enviar_email_convite(convite)

    return convite


def iniciar_aceitacao(*, convite, aluno):
    if convite.aluno_id != aluno.id:
        raise ConviteError(
            "Esse convite não pertence a esse usuário."
        )

    codigo_ainda_valido = (
        convite.status == Convite.Status.AWAITING_CONFIRMATION
        and convite.codigoExpiracao
        and timezone.now() <= convite.codigoExpiracao
        and convite.tentativas < maximo_tentativas
    )

    if codigo_ainda_valido:
        raise ConviteError(
            "Já existe um código válido enviado. "
            "Aguarde expirar para pedir outro."
        )

    if convite.status not in (
        Convite.Status.PENDING,
        Convite.Status.AWAITING_CONFIRMATION,
    ):
        raise ConviteError("Convite não está mais pendente.")

    codigo = convite.geradorCodigoAleatorio()

    email.enviar_email_codigo_confirmacao(convite, codigo)

    return convite


def confirmar_aceitacao(*, convite, aluno, codigo):
    if convite.aluno_id != aluno.id:
        raise ConviteError(
            "Esse convite não pertence a esse usuário."
        )

    ok, mensagem_erro = convite.checarConfirmacao(codigo)

    if not ok:
        raise ConviteError(mensagem_erro)

    convite.status = Convite.Status.ACCEPTED
    convite.resposta = timezone.now()

    convite.save(
        update_fields=["status", "resposta"]
    )

    convite.equipe.alunos.add(aluno)

    email.enviar_email_resposta(convite)

    return convite


def recusar_convite(*, convite, aluno):
    if convite.aluno_id != aluno.id:
        raise ConviteError(
            "Esse convite não pertence a esse usuário."
        )

    if not convite.is_active():
        raise ConviteError(
            "Convite já foi respondido."
        )

    convite.status = Convite.Status.DECLINED
    convite.resposta = timezone.now()

    convite.save(
        update_fields=["status", "resposta"]
    )

    email.enviar_email_resposta(convite)

    return convite