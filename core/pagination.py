from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

class EquipePagination(PageNumberPagination):
    page_size = 4
    page_size_query_param = 'page_size'
    max_page_size = 15

    def get_paginated_response(self, data):
        return Response({
            "total": self.page.paginator.count,
            "paginas": self.page.paginator.num_pages,
            "pagina_atual": self.page.number,
            "items": data
        })