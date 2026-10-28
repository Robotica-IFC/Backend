from datetime import timedelta
from django.contrib.auth.hashers import check_password
from django.db import transaction
from django.utils import timezone
from rest_framework.views import APIView
from core.email_verification import send_verification_code, send_initial_code
from core.serializers.user import MyTokenObtainPairSerializer, VerifyEmailSerializer, VerificationEmailSerializer
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from core.models import User
from core.serializers import UserRegistrationSerializer, UserSerializer


class UserViewSet(ModelViewSet):
    queryset = User.objects.all().order_by('id')
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Dados do usuário autenticado",
        description="Retorna os dados do usuário autenticado.",
        responses={200: UserSerializer, 401: None},
    )
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        """ Retorna os dados do usuário autenticado."""
        user = request.user
        serializer = UserSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class UserRegistrationView(CreateAPIView):
    """Endpoint para registro de novos usuários."""

    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        user = serializer.save()
        send_initial_code(user)


class EmailVerificationView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = VerifyEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            user = User.objects.select_for_update().filter(email__iexact=serializer.validated_data['email']).first()
            if not user or not user.is_active or user.email_verified:
                return Response({'detail': 'Verificação indisponível para este e-mail.'}, status=400)
            if not user.verification_code_created_at or timezone.now() >= user.verification_code_created_at + timedelta(minutes=10):
                return Response({'detail': 'Código expirado. Solicite um novo.'}, status=400)
            if user.verification_attempts >= 5:
                return Response({'detail': 'Muitas tentativas. Aguarde o código expirar e solicite outro.'}, status=429)
            if not check_password(serializer.validated_data['codigo'], user.verification_code_hash):
                user.verification_attempts += 1
                user.save(update_fields=['verification_attempts'])
                return Response({'detail': 'Código inválido.'}, status=400)
            user.email_verified = True
            user.verification_code_hash = ''
            user.save(update_fields=['email_verified', 'verification_code_hash'])
            if hasattr(user, 'aluno_profile'):
                user.aluno_profile.__class__.objects.filter(user=user).update(email_verificado=True)
            if hasattr(user, 'professor_profile'):
                user.professor_profile.__class__.objects.filter(user=user).update(email_verificado=True)
            refresh = MyTokenObtainPairSerializer.get_token(user)
        return Response({'access': str(refresh.access_token), 'refresh': str(refresh)})


class ResendVerificationCodeView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = VerificationEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            user = User.objects.select_for_update().filter(email__iexact=serializer.validated_data['email']).first()
            if user and user.is_active and not user.email_verified:
                now = timezone.now()
                created = user.verification_code_created_at
                if created and now < created + timedelta(seconds=60):
                    return Response({'detail': 'Aguarde 60 segundos entre os envios.'}, status=429)
                if created and user.verification_attempts >= 5 and now < created + timedelta(minutes=10):
                    return Response({'detail': 'Aguarde o código expirar para solicitar outro.'}, status=429)
                if not created or now >= created + timedelta(minutes=10):
                    user.verification_attempts = 0
                    user.save(update_fields=['verification_attempts'])
                try:
                    send_verification_code(user)
                except Exception:
                    return Response({'detail': 'Não foi possível enviar o e-mail. Tente novamente mais tarde.'}, status=503)
        return Response({'detail': 'Se houver uma conta pendente, um código será enviado.'})
