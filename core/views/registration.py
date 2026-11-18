import json
from datetime import timedelta

from django.contrib.auth.hashers import check_password, make_password
from django.db import transaction
from django.utils import timezone
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response

from core.email_verification import send_verification_code
from core.models import CadastroPendente


class RegistrationDeliveryError(Exception):
    pass


def start_registration(serializer, tipo):
    data = serializer.validated_data
    now = timezone.now()
    email = data['email'].strip()
    if CadastroPendente.objects.filter(
        email__iexact=email, expira_em__gt=now, verification_code_created_at__gt=now - timedelta(seconds=60),
    ).exists():
        return Response({'detail': 'Um código já foi enviado. Aguarde 60 segundos antes de tentar novamente.'}, status=429)
    payload = {
        key: None if value is None else serializer.fields[key].to_representation(value)
        for key, value in data.items() if key != 'password'
    }
    payload['email'] = email
    try:
        with transaction.atomic():
            CadastroPendente.objects.filter(expira_em__lte=now).delete()
            pending = CadastroPendente.objects.create(
                email=email, tipo=tipo, dados=json.loads(JSONRenderer().render(payload)),
                senha_hash=make_password(data['password']), expira_em=now + timedelta(hours=24),
            )
            try:
                send_verification_code(pending)
            except Exception as error:
                raise RegistrationDeliveryError from error
    except RegistrationDeliveryError:
        return Response({
            'detail': 'Não foi possível enviar o código. Nenhuma conta foi criada. Tente novamente.',
        }, status=503)
    return Response({
        'email': email, 'tipo': tipo, 'registration_token': str(pending.pk),
        'verification_required': True,
        'detail': 'Enviamos um código para seu e-mail. Sua conta será criada após a confirmação.',
    }, status=202)


def get_pending_registration(data):
    return CadastroPendente.objects.select_for_update().filter(
        pk=data['registration_token'], email__iexact=data['email'],
    ).first()


def verify_pending_registration(request, data):
    from core.serializers import AlunoSerializer, ProfessorSerializer, UserRegistrationSerializer
    from core.serializers.user import MyTokenObtainPairSerializer

    with transaction.atomic():
        pending = get_pending_registration(data)
        now = timezone.now()
        if pending is None or now >= pending.expira_em:
            return Response({'detail': 'Cadastro expirado ou já concluído. Inicie um novo cadastro.', 'code': 'registration_expired'}, status=400)
        created = pending.verification_code_created_at
        if not created or now >= created + timedelta(minutes=10):
            return Response({'detail': 'Código expirado. Solicite um novo.'}, status=400)
        if pending.verification_attempts >= 5:
            return Response({'detail': 'Muitas tentativas. Aguarde o código expirar e solicite outro.'}, status=429)
        if not check_password(data['codigo'], pending.verification_code_hash):
            pending.verification_attempts += 1
            pending.save(update_fields=['verification_attempts'])
            return Response({'detail': 'Código inválido.'}, status=400)
        serializer_class = {'aluno': AlunoSerializer, 'professor': ProfessorSerializer, 'usuario': UserRegistrationSerializer}[pending.tipo]
        serializer = serializer_class(
            # A senha em texto não é armazenada; a criação usa apenas o hash interno.
            data={**pending.dados, 'password': 'verified-registration'},
            context={
                'request': request, 'email_verified_registration': True,
                'registration_password_hash': pending.senha_hash,
            },
        )
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        user = instance if pending.tipo == 'usuario' else instance.user
        pending.delete()
        refresh = MyTokenObtainPairSerializer.get_token(user)
        return Response({'access': str(refresh.access_token), 'refresh': str(refresh), 'registration_completed': True})


def resend_pending_registration(data):
    try:
        with transaction.atomic():
            pending = get_pending_registration(data)
            now = timezone.now()
            if pending is None or now >= pending.expira_em:
                return Response({'detail': 'Cadastro expirado ou já concluído. Inicie um novo cadastro.', 'code': 'registration_expired'}, status=400)
            created = pending.verification_code_created_at
            if created and now < created + timedelta(seconds=60):
                return Response({'detail': 'Aguarde 60 segundos entre os envios.'}, status=429)
            if created and pending.verification_attempts >= 5 and now < created + timedelta(minutes=10):
                return Response({'detail': 'Aguarde o código expirar para solicitar outro.'}, status=429)
            if not created or now >= created + timedelta(minutes=10):
                pending.verification_attempts = 0
                pending.save(update_fields=['verification_attempts'])
            try:
                send_verification_code(pending)
            except Exception as error:
                raise RegistrationDeliveryError from error
    except RegistrationDeliveryError:
        return Response({'detail': 'Não foi possível enviar o código. Tente novamente mais tarde.'}, status=503)
    return Response({'detail': 'Enviamos um novo código para seu e-mail.'})
