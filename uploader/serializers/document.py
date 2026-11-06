from PIL import Image as PILImage
from rest_framework import serializers

from uploader.helpers.files import (
    CONTENT_TYPE_GIF,
    CONTENT_TYPE_JPG,
    CONTENT_TYPE_PDF,
    CONTENT_TYPE_PNG,
    CONTENT_TYPE_WEBP,
    get_content_type,
    get_file_url,
)
from uploader.models import Document


class DocumentUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ["attachment_key", "file", "description", "uploaded_on", "content_type"]
        read_only_fields = ["attachment_key", "uploaded_on", "content_type"]
        extra_kwargs = {"file": {"write_only": True}}

    def validate_file(self, value):
        content_type = get_content_type(value)
        valid_content_types = [
            CONTENT_TYPE_PDF, CONTENT_TYPE_JPG, CONTENT_TYPE_PNG, CONTENT_TYPE_WEBP, CONTENT_TYPE_GIF,
        ]
        if content_type not in valid_content_types:
            raise serializers.ValidationError('Selecione um PDF ou uma imagem JPG, PNG, WEBP ou GIF válida.')
        if content_type.startswith('image/'):
            try:
                with PILImage.open(value) as image:
                    image.verify()
            except (OSError, ValueError, PILImage.DecompressionBombError) as error:
                raise serializers.ValidationError('Imagem inválida ou corrompida.') from error
            finally:
                value.seek(0)
        return value

    def create(self, validated_data):
        validated_data['content_type'] = get_content_type(validated_data['file'])
        return super().create(validated_data)


class DocumentSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = ["url", "description", "uploaded_on", "attachment_key", "public_id", "content_type"]
        read_only_fields = ["url", "attachment_key", "uploaded_on"]

    def create(self, validated_data):
        raise NotImplementedError("Use DocumentUploadSerializer to create document files.")

    def get_url(self, obj):
        file_format = 'pdf' if obj.content_type == CONTENT_TYPE_PDF else None
        return get_file_url(obj.file, self.context.get('request'), file_format=file_format)
