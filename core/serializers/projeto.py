from rest_framework.serializers import ModelSerializer

from core.models import Projeto


class ProjetoSerializer(ModelSerializer):
    model = Projeto
    fields = '__all__'


class ProjetoListRetrieveSerializer(ModelSerializer):
    model = Projeto
    fields = '__all__'
