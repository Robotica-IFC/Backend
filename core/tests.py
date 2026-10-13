from django.test import TestCase

from core.models import Equipe, Estoque
from core.serializers import EquipeListRetrieveSerializer, EstoqueSerializer


class EstoqueSerializerTests(TestCase):
    def test_duplicate_equipe_stock_is_rejected(self):
        equipe = Equipe.objects.create(nome='Equipe Alpha')
        Estoque.objects.create(equipe=equipe)

        serializer = EstoqueSerializer(data={'equipe': str(equipe.id)})

        self.assertFalse(serializer.is_valid())
        self.assertIn('equipe', serializer.errors)

    def test_equipe_retrieve_includes_estoque_id(self):
        equipe = Equipe.objects.create(nome='Equipe Beta')
        estoque = Estoque.objects.create(equipe=equipe)

        serializer = EquipeListRetrieveSerializer(equipe)

        self.assertEqual(serializer.data['estoque_id'], estoque.id)
