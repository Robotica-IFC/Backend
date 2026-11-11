import logging
import secrets

from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone

logger = logging.getLogger(__name__)


def send_verification_code(user, *, password_reset=False):
    code = f"{secrets.randbelow(1000000):06d}"
    prefix = 'password_reset' if password_reset else 'verification'
    created_field = 'password_reset_created_at' if password_reset else 'verification_code_created_at'
    setattr(user, f'{prefix}_code_hash', make_password(code))
    setattr(user, created_field, timezone.now())
    # Attempts are reset only after expiry, so resending cannot bypass the limit.
    fields = [f'{prefix}_code_hash', created_field]
    if password_reset:
        user.password_reset_token_hash = ''
        fields.append('password_reset_token_hash')
    user.save(update_fields=fields)
    purpose = 'para redefinir a senha' if password_reset else 'de verificação'
    send_mail(
        'Redefina sua senha' if password_reset else 'Confirme seu e-mail',
        f'Seu código {purpose} é: {code}\nEle expira em 10 minutos.',
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
        html_message=render_to_string('core/emails/verification_code.html', {
            'code': code, 'password_reset': password_reset,
        }),
    )


def send_initial_code(user):
    try:
        send_verification_code(user)
    except Exception:
        # Keep the account pending and let the user retry delivery using resend.
        logger.exception('Falha ao enviar código de confirmação para usuário %s', user.pk)
