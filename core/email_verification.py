import logging
import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone

logger = logging.getLogger(__name__)


def send_verification_code(user):
    code = f"{secrets.randbelow(1000000):06d}"
    user.verification_code_hash = make_password(code)
    user.verification_code_created_at = timezone.now()
    # Attempts are reset only after expiry, so resending cannot bypass the limit.
    user.save(update_fields=['verification_code_hash', 'verification_code_created_at'])
    send_mail(
        'Confirme seu e-mail',
        f'Seu código de verificação é: {code}\nEle expira em 10 minutos.',
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
        html_message=render_to_string('core/emails/verification_code.html', {'code': code}),
    )


def send_initial_code(user):
    try:
        send_verification_code(user)
    except Exception:
        # Keep the account pending and let the user retry delivery using resend.
        logger.exception('Falha ao enviar código de confirmação para usuário %s', user.pk)
