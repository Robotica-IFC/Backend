from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response


from app import services
from core.models import Convite
from core.serializers.convite import (
    CreateConviteSerializer,
    ConfirmConviteSerializer,
    ConviteSerializer,
)

from core.models import Equipe

User = get_user_model()


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def enviar_convite(request, equipe_id):
    equipe = get_object_or_404(Equipe, pk=equipe_id)

    serializer = CreateConviteSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    aluno = get_object_or_404(
        User,
        pk=serializer.validated_data["alunoId"]
    )

    try:
        convite = services.criar_convite(
            equipe=equipe,
            aluno=aluno,
            enviadoPor=request.user,
        )
    except services.ConviteError as e:
        return Response(
            {"detail": str(e)},
            status=status.HTTP_400_BAD_REQUEST,
        )

    return Response(
        ConviteSerializer(convite).data,
        status=status.HTTP_201_CREATED,
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def listar_meus_convites(request):
    convites = Convite.objects.filter(
        aluno=request.user,
        status=Convite.Status.PENDING,
    )

    return Response(
        ConviteSerializer(convites, many=True).data
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def iniciar_aceitacao_convite(request, convite_id):
    convite = get_object_or_404(
        Convite,
        pk=convite_id,
    )

    try:
        services.iniciar_aceitacao(
            convite=convite,
            aluno=request.user,
        )
    except services.ConviteError as e:
        return Response(
            {"detail": str(e)},
            status=status.HTTP_400_BAD_REQUEST,
        )

    return Response({
        "detail": "Código de confirmação enviado por email."
    })


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def confirmar_convite(request, convite_id):
    convite = get_object_or_404(
        Convite,
        pk=convite_id,
    )

    serializer = ConfirmConviteSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    try:
        convite = services.confirmar_aceitacao(
            convite=convite,
            aluno=request.user,
            codigo=serializer.validated_data["code"],
        )
    except services.ConviteError as e:
        return Response(
            {"detail": str(e)},
            status=status.HTTP_400_BAD_REQUEST,
        )

    return Response(
        ConviteSerializer(convite).data
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def recusar_convite(request, convite_id):
    convite = get_object_or_404(
        Convite,
        pk=convite_id,
    )

    try:
        convite = services.recusar_convite(
            convite=convite,
            aluno=request.user,
        )
    except services.ConviteError as e:
        return Response(
            {"detail": str(e)},
            status=status.HTTP_400_BAD_REQUEST,
        )

    return Response(
        ConviteSerializer(convite).data
    )