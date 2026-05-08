from rest_framework.serializers import ModelSerializer, SlugRelatedField
from uploader.models import Image
from core.models import Equipe


class ImageSerializer(ModelSerializer):
    class Meta:
        model = Image
        fields = ['attachment_key', 'file']

class EquipeSerializer(ModelSerializer):
    image_perfil = ImageSerializer(read_only=True)

    class Meta:
        model = Equipe
        fields = '__all__'
        depth = 1   
