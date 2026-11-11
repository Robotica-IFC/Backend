from django.core.management.base import BaseCommand, CommandError
from core.models import Equipe, Professor


class Command(BaseCommand):
    help = 'Define o professor criador de uma equipe antiga que ainda não possui criador.'

    def add_arguments(self, parser):
        parser.add_argument('equipe_id', help='UUID da equipe')
        parser.add_argument('email', help='E-mail do professor criador')

    def handle(self, *args, **options):
        equipe = Equipe.objects.filter(pk=options['equipe_id']).first()
        if equipe is None:
            raise CommandError('Equipe não encontrada.')
        if equipe.criador_id:
            raise CommandError('A equipe já tem criador definido. Não é possível transferir o criador por este comando.')
        professor = Professor.objects.filter(user__email__iexact=options['email']).first()
        if not professor or not equipe.professores.filter(pk=professor.pk).exists():
            raise CommandError('O professor informado precisa ser membro da equipe.')
        equipe.criador = professor
        equipe.save(update_fields=['criador'])
        self.stdout.write(self.style.SUCCESS('Criador definido com sucesso.'))
