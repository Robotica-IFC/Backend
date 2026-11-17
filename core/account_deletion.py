from django.db import transaction
from django.db.models import Q
from rest_framework.exceptions import NotFound, ValidationError

from core.models import Convite, Equipe, Post, User


def account_teams(user):
    return Equipe.objects.filter(
        Q(professores__user=user) | Q(criador__user=user),
    ).distinct()


def account_deletion_blocker(user, teams=None):
    professor = getattr(user, 'professor_profile', None)
    if professor is None:
        return ''
    if teams is None:
        teams = account_teams(user)
    blocked = [team.nome for team in teams if not team.professores.exclude(pk=professor.pk).exists()]
    if not blocked:
        return ''
    return (
        'Você só pode excluir sua conta se cada equipe tiver mais de um professor responsável. '
        'Adicione outro professor responsável antes de continuar. '
        f'Equipes sem outro responsável: {", ".join(blocked)}.'
    )


@transaction.atomic
def delete_account(user_id):
    user = User.objects.select_for_update().filter(pk=user_id).first()
    if user is None:
        raise NotFound('Conta não encontrada.')
    # As saídas, remoções e transferências de professores também bloqueiam a equipe.
    team_ids = account_teams(user).values_list('pk', flat=True)
    teams = list(Equipe.objects.select_for_update().filter(pk__in=team_ids).order_by('pk'))
    blocker = account_deletion_blocker(user, teams)
    if blocker:
        raise ValidationError({'detail': blocker})

    professor = getattr(user, 'professor_profile', None)
    if professor:
        for team in teams:
            if team.criador_id == professor.pk:
                # Mantém a responsabilidade com o professor há mais tempo na equipe.
                team.criador_id = (
                    team.professores.through.objects
                    .filter(
                        equipe_id=team.pk,
                    )
                    .exclude(professor_id=professor.pk)
                    .order_by('id')
                    .values_list('professor_id', flat=True)
                    .first()
                )
                team.save(update_fields=['criador'])

    # Essas relações usam PROTECT: a exclusão permanente inclui os registros da conta.
    Convite.objects.filter(
        Q(aluno__user=user) | Q(professor__user=user) | Q(convidante__user=user),
    ).delete()
    Post.objects.filter(Q(aluno_criador__user=user) | Q(professor_criador__user=user)).delete()
    # O CASCADE do vínculo OneToOne remove também Aluno e/ou Professor.
    user.delete()
