from rest_framework.permissions import BasePermission
from .models import ProjectMember


def get_user_role(project, user):
    try:
        return ProjectMember.objects.get(project=project, user=user).role
    except ProjectMember.DoesNotExist:
        return None


class IsProjectMember(BasePermission):
    def has_object_permission(self, request, view, obj):
        project = obj if hasattr(obj, 'members') else obj.project
        if project.owner == request.user:
            return True
        return ProjectMember.objects.filter(project=project, user=request.user).exists()


class IsProjectAdmin(BasePermission):
    def has_object_permission(self, request, view, obj):
        project = obj if hasattr(obj, 'members') else obj.project
        if project.owner == request.user:
            return True
        return ProjectMember.objects.filter(project=project, user=request.user, role='admin').exists()
