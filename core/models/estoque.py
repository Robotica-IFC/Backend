from django.db import models

from uploader.models import Image


class Estoque(models.Model):
    equipe = models.OneToOneField(
        'core.equipe',
        on_delete=models.CASCADE,
        related_name='estoque',
        null=True,
        blank=True
    )

    def __str__(self):
        if self.equipe:
            return f'Estoque da equipe {self.equipe.nome}'
        return f'Estoque #{self.id} (Sem equipe)'


class Item(models.Model):
    class CategoriaItem(models.TextChoices):
        SENSORES = 'SENSORES', 'Sensores'
        ATUADORES = 'ATUADORES', 'Atuadores e Motores'
        MICROCONTROLADORES = 'MICROCONTROLADORES', 'Microcontroladores e Placas'
        ELETRONICA = 'ELETRONICA', 'Componentes Eletrônicos'
        ESTRUTURA = 'ESTRUTURA', 'Peças Estruturais e Chassi'
        ALIMENTACAO = 'ALIMENTACAO', 'Baterias e Alimentação'
        FERRAMENTAS = 'FERRAMENTAS', 'Ferramentas e Equipamentos'
        CABEAMENTO = 'CABEAMENTO', 'Cabos e Conectores'
        FIXACAO = 'FIXACAO', 'Parafusos e Fixadores'
        IMPRESSAO_3D = 'IMPRESSAO_3D', 'Filamentos e Peças 3D'
        OUTROS = 'OUTROS', 'Outros'

    estoque = models.ForeignKey(
        Estoque,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='itens'
    )
    nome = models.CharField(max_length=100)
    quantidade = models.PositiveIntegerField(default=0)
    descricao = models.TextField(blank=True, null=True)
    imagem = models.ForeignKey(
        Image,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='itens'
    )
    categoria = models.CharField(
        max_length=30,
        choices=CategoriaItem.choices,
        default=CategoriaItem.OUTROS,
    )

    def __str__(self):
        return f'{self.nome} ({self.get_categoria_display()}) - {self.quantidade}'