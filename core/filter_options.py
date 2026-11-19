from core.models import Categoria, Equipe, Instituicao


def resource_filter_options():
    return {
        'instituicoes': list(Instituicao.objects.order_by('nome').values('id', 'nome')),
        'equipes': list(Equipe.objects.order_by('nome').values('id', 'nome')),
        'categorias': list(Categoria.objects.order_by('nome').values('id', 'nome')),
    }
