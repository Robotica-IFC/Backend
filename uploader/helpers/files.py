from urllib.parse import urlsplit

import magic
from django.core.files.storage import FileSystemStorage

CONTENT_TYPE_ICO = "image/x-icon"
CONTENT_TYPE_JPG = "image/jpeg"
CONTENT_TYPE_PNG = "image/png"
CONTENT_TYPE_WEBP = "image/webp"
CONTENT_TYPE_GIF = "image/gif"


CONTENT_TYPE_PDF = "application/pdf"


def get_file_url(file, request=None, *, file_format=None):
    name = file.name
    # Cloudinary salva PDFs como recursos image, cujo public_id não inclui a
    # extensão. A entrega do documento original precisa do sufixo .pdf na URL.
    if (
        file_format
        and getattr(file.storage, 'RESOURCE_TYPE', None) == 'image'
        and not name.lower().endswith(f'.{file_format}')
    ):
        name = f'{name}.{file_format}'
    url = file.storage.url(name)
    if request is None:
        return url
    if isinstance(file.storage, FileSystemStorage):
        # Os anexos locais são servidos pelo mesmo host e porta da API.
        url = urlsplit(url).path
    return request.build_absolute_uri(url)


def get_content_type(file):
    if hasattr(file, "temporary_file_path"):
        content_type = magic.from_file(file.temporary_file_path(), mime=True)
    else:
        content_type = magic.from_buffer(file.read(), mime=True)

    if hasattr(file, "seek") and callable(file.seek):
        file.seek(0)

    return content_type
