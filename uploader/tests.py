
from tempfile import TemporaryDirectory
from urllib.parse import urlsplit

from cloudinary_storage.storage import MediaCloudinaryStorage, RawMediaCloudinaryStorage
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory, SimpleTestCase, override_settings
from django.urls import path
from django.views.static import serve
from rest_framework import status
from rest_framework.test import APITestCase

from uploader.helpers.files import get_file_url
from uploader.models import Document
from uploader.serializers.document import DocumentSerializer


@override_settings(MODE='PRODUCTION', MEDIA_URL='/media/')
class DocumentURLTests(SimpleTestCase):
    def serialize_document(self, name, storage):
        document = Document(file=name)
        document.file.storage = storage
        request = RequestFactory().get('/', HTTP_HOST='backend.example:8000')
        url = DocumentSerializer(document, context={'request': request}).data['url']
        assert document.url == get_file_url(document.file, file_format='pdf')
        return url

    def test_existing_cloudinary_pdf_public_id_delivers_original_pdf(self):
        url = self.serialize_document('media/documents/existing_public_id', MediaCloudinaryStorage())

        assert '/image/upload/' in url
        assert url.endswith('/media/documents/existing_public_id.pdf')

    def test_cloudinary_pdf_extension_is_not_duplicated(self):
        url = self.serialize_document('media/documents/proposta.pdf', MediaCloudinaryStorage())

        assert url.endswith('/media/documents/proposta.pdf')
        assert not url.endswith('.pdf.pdf')

    def test_raw_cloudinary_public_id_is_preserved(self):
        url = self.serialize_document('media/documents/proposta.pdf', RawMediaCloudinaryStorage())

        assert '/raw/upload/' in url
        assert url.endswith('/media/documents/proposta.pdf')

    @override_settings(MODE='DEVELOPMENT')
    def test_local_pdf_uses_api_host_and_preserves_filename(self):
        storage = FileSystemStorage(base_url='http://localhost:19003/media/')

        url = self.serialize_document('documents/proposta.pdf', storage)

        assert url == 'http://backend.example:8000/media/documents/proposta.pdf'

    def test_image_urls_keep_their_original_format(self):
        document = Document(file='media/images/avatar.png')
        document.file.storage = MediaCloudinaryStorage()

        assert get_file_url(document.file).endswith('/media/images/avatar.png')

    @override_settings(MODE='DEVELOPMENT')
    def test_cloudinary_pdf_keeps_cloudinary_host_in_development(self):
        url = self.serialize_document('media/documents/proposta', MediaCloudinaryStorage())

        assert urlsplit(url).hostname == 'res.cloudinary.com'
        assert url.endswith('/media/documents/proposta.pdf')

    @override_settings(MODE='DEVELOPMENT')
    def test_cloudinary_profile_image_keeps_cloudinary_host_in_development(self):
        document = Document(file='media/images/avatar')
        document.file.storage = MediaCloudinaryStorage()
        request = RequestFactory().get('/', HTTP_HOST='backend.example:8000')

        url = get_file_url(document.file, request)

        assert urlsplit(url).hostname == 'res.cloudinary.com'
        assert url.endswith('/media/images/avatar')

    def test_image_attachment_is_not_delivered_as_a_pdf(self):
        document = Document(file='media/documents/foto', content_type='image/png')
        document.file.storage = MediaCloudinaryStorage()

        url = DocumentSerializer(document).data['url']

        assert urlsplit(url).hostname == 'res.cloudinary.com'
        assert url.endswith('/media/documents/foto')
        assert document.url == url


def serve_test_media(request, path):
    return serve(request, path, document_root=settings.MEDIA_ROOT)


urlpatterns = [path('media/<path:path>', serve_test_media)]


@override_settings(MODE='DEVELOPMENT', DEBUG=True)
class LocalDocumentUploadTests(APITestCase):
    def test_uploaded_pdf_can_be_opened_using_its_serialized_url(self):
        content = b'%PDF-1.4\n1 0 obj\n<<>>\nendobj\n%%EOF'
        with TemporaryDirectory() as media_root, override_settings(
            MEDIA_ROOT=media_root,
            MEDIA_URL='/media/',
            STORAGES={'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'}},
        ):
            upload = self.client.post('/api/media/documents/', {
                'file': SimpleUploadedFile('proposta.pdf', content, 'application/pdf'),
            }, format='multipart')
            assert upload.status_code == status.HTTP_201_CREATED
            document = Document.objects.get(attachment_key=upload.data['attachment_key'])
            request = RequestFactory().get('/', HTTP_HOST='backend.example:8000')
            url = DocumentSerializer(document, context={'request': request}).data['url']
            assert url.startswith('http://backend.example:8000/media/documents/')

            with override_settings(ROOT_URLCONF=__name__):
                response = self.client.get(urlsplit(url).path)
                assert response.status_code == status.HTTP_200_OK
                assert response['Content-Type'] == 'application/pdf'
                assert b''.join(response.streaming_content) == content
                response.close()
