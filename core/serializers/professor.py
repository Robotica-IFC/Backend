from django.contrib.auth.hashers import make_password
from rest_framework.serializers import ModelSerializer, SlugRelatedField

from core.models import Professor
from uploader.models import Image


class ProfessorSerializer(ModelSerializer):

    imagem_perfil = SlugRelatedField(
        queryset=Image.objects.all(),
        slug_field='attachment_key',
        required=False,
        allow_null=True
    )

    class Meta:
        model = Professor
        fields = "__all__"

    def create(self, validated_data):
       validated_data["senha"] = make_password(validated_data["senha"])  # noqa: E111
       return super().create(validated_data)  # noqa: E111


class ProfessorListSerializer(ModelSerializer):
    class Meta:
        model = Professor
        fields = '__all__'
        depth = 1


class ProfessorRetrieveSerializer(ModelSerializer):
    class Meta:
        model = Professor
        fields = '__all__'
        depth = 1
