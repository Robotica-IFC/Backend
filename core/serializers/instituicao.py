from rest_framework.serializers import ModelSerializer

from core.models import Instituicao


class InstituicaoSerializer(ModelSerializer):
    class Meta:
        model = Instituicao
        fields = '__all__'


class InstituicaoListRetrieveSerializer(ModelSerializer):
    class Meta:
        model = Instituicao
        fields = "__all__"
        depth = 2
