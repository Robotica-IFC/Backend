from urllib.parse import urlsplit

import magic
from django.conf import settings

CONTENT_TYPE_ICO = "image/x-icon"
CONTENT_TYPE_JPG = "image/jpeg"
CONTENT_TYPE_PNG = "image/png"
CONTENT_TYPE_WEBP = "image/webp"
CONTENT_TYPE_GIF = "image/gif"


CONTENT_TYPE_PDF = "application/pdf"


def get_file_url(file, request=None):
    url = file.url
    if request is None:
        return url
    if settings.MODE == 'DEVELOPMENT':
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
