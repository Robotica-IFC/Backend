from django.db import transaction
from rest_framework import serializers

from core.models import Aluno, Post, PostImage, Professor
from uploader.models import Image


class ProfessorSimpleSerializer(serializers.ModelSerializer):
    name = serializers.ReadOnlyField(source='user.name')
    username = serializers.ReadOnlyField(source='user.username')
    imagem_perfil = serializers.SerializerMethodField()

    class Meta:
        model = Professor
        fields = ['id', 'name', 'username', 'imagem_perfil']

    def get_imagem_perfil(self, obj):
        if obj.imagem_perfil and hasattr(obj.imagem_perfil, 'file') and obj.imagem_perfil.file:
            return obj.imagem_perfil.file.url
        return None


class AlunoSimpleSerializer(serializers.ModelSerializer):
    name = serializers.ReadOnlyField(source='user.name')
    username = serializers.ReadOnlyField(source='user.username')
    imagem_perfil = serializers.SerializerMethodField()

    class Meta:
        model = Aluno
        fields = ['id', 'name', 'username', 'imagem_perfil']

    def get_imagem_perfil(self, obj):
        if obj.imagem_perfil and hasattr(obj.imagem_perfil, 'file') and obj.imagem_perfil.file:
            return obj.imagem_perfil.file.url
        return None


class PostImageSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()

    class Meta:
        model = PostImage
        fields = ['id', 'url']

    def get_url(self, obj):
        if hasattr(obj, 'image') and obj.image and hasattr(obj.image, 'file') and obj.image.file:
            return obj.image.file.url
        return None


class PostImageCreateSerializer(serializers.Serializer):
    image_id = serializers.UUIDField()


class PostCreateSerializer(serializers.ModelSerializer):
    images = PostImageCreateSerializer(many=True, required=False)

    class Meta:
        model = Post
        fields = ['id', 'legenda', 'projeto', 'criado_em', 'images', 'aluno_criador', 'professor_criador']
        read_only_fields = ['criado_em', 'aluno_criador', 'professor_criador']

    @transaction.atomic
    def create(self, validated_data):
        user = self.context["request"].user
        images_data = validated_data.pop('images', [])

        if hasattr(user, 'aluno_profile'):
            validated_data['aluno_criador'] = user.aluno_profile
        elif hasattr(user, 'professor_profile'):
            validated_data['professor_criador'] = user.professor_profile
        else:
            raise serializers.ValidationError(
                {
                    "criador": (
                        f"O usuário {user.email} não possui um perfil de "
                        "Aluno ou Professor cadastrado para criar posts."
                    )
                }
            )

        post = Post.objects.create(**validated_data)

        if images_data:
            post_images = []
            for img_data in images_data:
                try:
                    img_obj = Image.objects.get(pk=img_data['image_id'])
                    post_images.append(PostImage(post=post, image=img_obj))
                except Image.DoesNotExist:
                    continue

            if post_images:
                PostImage.objects.bulk_create(post_images)

        return post


class PostListRetrieveSerializer(serializers.ModelSerializer):
    images = PostImageSerializer(many=True, read_only=True)
    professor_criador = ProfessorSimpleSerializer(read_only=True)
    aluno_criador = AlunoSimpleSerializer(read_only=True)

    class Meta:
        model = Post
        fields = "__all__"
