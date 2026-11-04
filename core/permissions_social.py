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


class CanEditPost(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return bool(
            request.user.is_staff or
            (obj.aluno_criador_id and obj.aluno_criador.user_id == request.user.pk) or
            (obj.professor_criador_id and obj.professor_criador.user_id == request.user.pk)
        )
