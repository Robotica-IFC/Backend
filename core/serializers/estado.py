from rest_framework.serializers import ModelSerializer

from core.models import Estado


class EstadoSerializer(ModelSerializer):
    class Meta:
        model = Estado
        fields = "__all__"