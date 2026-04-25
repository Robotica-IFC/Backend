from attr import field
from rest_framework.serializers import ModelSerializer, SlugRelatedField

from uploader.models import Image
from core.models import Equipe

class EquipeSerializer(ModelSerializer):
      
      image_perfil = SlugRelatedField(
        queryset=Image.objects.all(),
        slug_field='attachment_key',
        required=False,
        allow_null=True
    )
      class Meta:
        model = Equipe
        fields = '__all__'
    

