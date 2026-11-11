from rest_framework.permissions import BasePermission, SAFE_METHODS


def is_team_teacher(user, team):
    return bool(user and user.is_authenticated and (
        user.is_staff or team.professores.filter(user=user).exists()
    ))


def is_team_member(user, team):
    return bool(user and user.is_authenticated and (
        user.is_staff or team.professores.filter(user=user).exists()
        or team.alunos.filter(user=user).exists()
    ))


class CanEditTeam(BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.method in SAFE_METHODS or is_team_teacher(request.user, obj)


class CanEditProject(BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.method in SAFE_METHODS or is_team_teacher(request.user, obj.equipe)


def can_manage_post(user, post):
    if not user or not user.is_authenticated or not post.projeto_id:
        return False
    team = post.projeto.equipe
    # A participação atual é obrigatória, mesmo para autores e administradores.
    if not is_team_member(user, team):
        return False
    if team.professores.filter(user=user).exists():
        return True
    return bool(
        post.aluno_criador_id
        and post.aluno_criador.user_id == user.pk
        and team.alunos.filter(user=user).exists()
    )


class CanEditPost(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS or view.action in {'curtir', 'comentarios', 'excluir_comentario'}:
            return True
        return can_manage_post(request.user, obj)
