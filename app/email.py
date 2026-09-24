from django.conf import settings
from django.core.mail import send_mail

from core.models import Convite


def enviar_email_convite(convite):
    send_mail(
        subject="Você recebeu um convite para uma equipe",
        message=(
            f"Olá {convite.aluno.name},\n\n"
            f"{convite.enviadoPor.name} convidou você para participar "
            f'da equipe "{convite.equipe.name}".\n'
            "Acesse o site para aceitar ou recusar o convite."
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[convite.aluno.email],
    )


def enviar_email_codigo_confirmacao(convite, codigo):
    send_mail(
        subject="Código de confirmação do convite",
        message=(
            f"Olá {convite.aluno.name},\n\n"
            f"Seu código de confirmação é: {codigo}\n"
            "Ele expira em 15 minutos. Digite-o no site para "
            "confirmar sua entrada na equipe."
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[convite.aluno.email],
    )


def enviar_email_resposta(convite):
    if convite.status == Convite.Status.ACCEPTED:
        acao = "aceitou"
    else:
        acao = "recusou"

    send_mail(
        subject=f"O aluno {acao} o convite para a equipe",
        message=(
            f"Olá {convite.enviadoPor.name},\n\n"
            f"O aluno {convite.aluno.name} {acao} o convite "
            f'para a equipe "{convite.equipe.name}".'
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[convite.enviadoPor.email],
    )