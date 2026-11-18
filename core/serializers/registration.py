from django.db import IntegrityError, transaction
from rest_framework import serializers

from core.models import User


EMAIL_ALREADY_REGISTERED = (
    'Já existe uma conta com este e-mail. Entre na sua conta ou recupere sua senha.'
)


def validate_registration_email(email, instance=None):
    email = email.strip()
    users = User.objects.filter(email__iexact=email)
    if instance is not None:
        users = users.exclude(pk=instance.user_id)
    if users.exists():
        raise serializers.ValidationError(EMAIL_ALREADY_REGISTERED, code='email_already_exists')
    return email


def create_registration_user(*, password_hash=None, **data):
    try:
        # O savepoint permite retornar o aviso também em cadastros simultâneos.
        with transaction.atomic():
            if password_hash is not None:
                data.pop('password', None)
                data['email'] = User.objects.normalize_email(data['email'])
                return User.objects.create(password=password_hash, **data)
            return User.objects.create_user(**data)
    except IntegrityError:
        if User.objects.filter(email__iexact=data['email']).exists():
            raise serializers.ValidationError({'email': [EMAIL_ALREADY_REGISTERED]}) from None
        raise
