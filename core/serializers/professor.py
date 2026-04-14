from attr import field
from django.contrib.auth.hashers import make_password
from rest_framework.serializers import ModelSerializer

from core.models import Professor
from uploader.helpers import files

class ProfessorSerializer(ModelSerializer):
    class Meta:
        model = Professor
        fields = "__all__"

    def create(self, validated_data):
       validated_data["senha"] = make_password(validated_data["senha"])
       return super().create(validated_data)
    
class ProfessorListSerializer(ModelSerializer):
    class Meta:
        model = Professor
        fields = '__all__'
        depth = 1

class ProfessorRetrieveSerializer(ModelSerializer):
    class Meta:
        model = Professor
        fields = 'attachment_key', 'file'
        depth = 1