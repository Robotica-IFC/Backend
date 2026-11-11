from rest_framework import serializers
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import PostComment
from core.serializers.aluno import AlunoSerializer
from core.serializers.categoria import CategoriaSerializer
from core.serializers.equipe import EquipeSerializer
from core.serializers.estoque import ItemSerializer
from core.serializers.instituicao import InstituicaoSerializer
from core.serializers.post import PostCreateSerializer
from core.serializers.professor import ProfessorSerializer
from core.serializers.projeto import ProjetoSerializer
from core.serializers.sugestao_projeto import SugestaoProjetoSerializer
from core.serializers.user import UserRegistrationSerializer, UserSerializer, VerifyEmailSerializer
from uploader.helpers.files import (
    CONTENT_TYPE_GIF,
    CONTENT_TYPE_ICO,
    CONTENT_TYPE_JPG,
    CONTENT_TYPE_PDF,
    CONTENT_TYPE_PNG,
    CONTENT_TYPE_WEBP,
)


class CommentInputSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostComment
        fields = ['texto']


FORM_SERIALIZERS = {
    'equipe': EquipeSerializer,
    'projeto': ProjetoSerializer,
    'item': ItemSerializer,
    'categoria': CategoriaSerializer,
    'instituicao': InstituicaoSerializer,
    'post': PostCreateSerializer,
    'comentario': CommentInputSerializer,
    'sugestao': SugestaoProjetoSerializer,
    'usuario': UserSerializer,
    'registro': UserRegistrationSerializer,
    'aluno': AlunoSerializer,
    'professor': ProfessorSerializer,
    'verificacao': VerifyEmailSerializer,
}


def form_limits():
    forms = {}
    for resource, serializer_class in FORM_SERIALIZERS.items():
        fields = {}
        for name, field in serializer_class().fields.items():
            if field.read_only or not isinstance(field, (serializers.CharField, serializers.IntegerField)):
                continue
            rule = {'required': field.required, 'allow_blank': getattr(field, 'allow_blank', False)}
            for attribute in ('max_length', 'min_length', 'min_value', 'max_value'):
                value = getattr(field, attribute, None)
                if value is not None:
                    # Preserve integer bounds even when the browser cannot represent them exactly.
                    rule[attribute] = str(value) if abs(value) > 2**53 - 1 else value
            rule['type'] = 'integer' if isinstance(field, serializers.IntegerField) else 'text'
            fields[name] = rule
        forms[resource] = fields
    return forms


class FormLimitsView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        return Response({
            'forms': form_limits(),
            'uploads': {
                'image_types': [
                    CONTENT_TYPE_JPG,
                    CONTENT_TYPE_PNG,
                    CONTENT_TYPE_WEBP,
                    CONTENT_TYPE_GIF,
                    CONTENT_TYPE_ICO,
                ],
                'document_types': [CONTENT_TYPE_PDF],
            },
        })
