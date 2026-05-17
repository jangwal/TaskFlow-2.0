from rest_framework import generics, status, viewsets
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.utils import timezone
from django.db.models import Q

from .models import Project, ProjectMember, Task
from .serializers import (
    UserSerializer, RegisterSerializer,
    ProjectSerializer, ProjectMemberSerializer, TaskSerializer
)
from .permissions import IsProjectMember, IsProjectAdmin, get_user_role


# ─── Auth Views ────────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response({
            'user': UserSerializer(user).data,
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    username = request.data.get('username')
    password = request.data.get('password')
    user = authenticate(username=username, password=password)
    if user:
        refresh = RefreshToken.for_user(user)
        return Response({
            'user': UserSerializer(user).data,
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        })
    return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['GET'])
def me(request):
    return Response(UserSerializer(request.user).data)


@api_view(['GET'])
def list_users(request):
    users = User.objects.all()
    return Response(UserSerializer(users, many=True).data)


# ─── Dashboard ─────────────────────────────────────────────────────

@api_view(['GET'])
def dashboard(request):
    user = request.user
    # Projects the user is part of (owner or member)
    member_project_ids = ProjectMember.objects.filter(user=user).values_list('project_id', flat=True)
    projects = Project.objects.filter(Q(owner=user) | Q(id__in=member_project_ids)).distinct()

    # Tasks assigned to user
    my_tasks = Task.objects.filter(assigned_to=user)
    today = timezone.now().date()

    return Response({
        'total_projects': projects.count(),
        'total_tasks': my_tasks.count(),
        'completed_tasks': my_tasks.filter(status='done').count(),
        'overdue_tasks': my_tasks.exclude(status='done').filter(due_date__lt=today).count(),
        'in_progress_tasks': my_tasks.filter(status='in_progress').count(),
        'recent_tasks': TaskSerializer(
            Task.objects.filter(
                Q(project__in=projects)
            ).order_by('-created_at')[:5], many=True
        ).data,
    })


# ─── Project ViewSet ───────────────────────────────────────────────

class ProjectViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        member_ids = ProjectMember.objects.filter(user=user).values_list('project_id', flat=True)
        return Project.objects.filter(Q(owner=user) | Q(id__in=member_ids)).distinct()

    def perform_create(self, serializer):
        project = serializer.save(owner=self.request.user)
        # Creator is automatically an admin member
        ProjectMember.objects.create(project=project, user=self.request.user, role='admin')

    def destroy(self, request, *args, **kwargs):
        project = self.get_object()
        if project.owner != request.user:
            return Response({'error': 'Only owner can delete project'}, status=403)
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=['get'])
    def tasks(self, request, pk=None):
        project = self.get_object()
        tasks = Task.objects.filter(project=project)
        return Response(TaskSerializer(tasks, many=True).data)

    @action(detail=True, methods=['post'])
    def add_member(self, request, pk=None):
        project = self.get_object()
        role = get_user_role(project, request.user)
        if project.owner != request.user and role != 'admin':
            return Response({'error': 'Admin access required'}, status=403)

        user_id = request.data.get('user_id')
        member_role = request.data.get('role', 'member')
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=404)

        member, created = ProjectMember.objects.get_or_create(
            project=project, user=user,
            defaults={'role': member_role}
        )
        if not created:
            member.role = member_role
            member.save()
        return Response(ProjectMemberSerializer(member).data)

    @action(detail=True, methods=['delete'], url_path='remove_member/(?P<user_id>[^/.]+)')
    def remove_member(self, request, pk=None, user_id=None):
        project = self.get_object()
        role = get_user_role(project, request.user)
        if project.owner != request.user and role != 'admin':
            return Response({'error': 'Admin access required'}, status=403)
        ProjectMember.objects.filter(project=project, user_id=user_id).delete()
        return Response(status=204)

    @action(detail=True, methods=['patch'], url_path='update_member/(?P<user_id>[^/.]+)')
    def update_member_role(self, request, pk=None, user_id=None):
        project = self.get_object()
        if project.owner != request.user:
            return Response({'error': 'Only owner can change roles'}, status=403)
        try:
            member = ProjectMember.objects.get(project=project, user_id=user_id)
            member.role = request.data.get('role', member.role)
            member.save()
            return Response(ProjectMemberSerializer(member).data)
        except ProjectMember.DoesNotExist:
            return Response({'error': 'Member not found'}, status=404)


# ─── Task ViewSet ──────────────────────────────────────────────────

class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        member_ids = ProjectMember.objects.filter(user=user).values_list('project_id', flat=True)
        qs = Task.objects.filter(
            Q(project__owner=user) | Q(project_id__in=member_ids)
        ).distinct()

        # Filters
        project_id = self.request.query_params.get('project')
        if project_id:
            qs = qs.filter(project_id=project_id)

        status_filter = self.request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)

        assigned_to_me = self.request.query_params.get('mine')
        if assigned_to_me:
            qs = qs.filter(assigned_to=user)

        return qs.order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def update(self, request, *args, **kwargs):
        task = self.get_object()
        project = task.project
        user = request.user
        role = get_user_role(project, user)

        # Members can only update status of tasks assigned to them
        if project.owner != user and role != 'admin':
            allowed_fields = {'status'}
            if not set(request.data.keys()).issubset(allowed_fields):
                return Response({'error': 'Members can only update task status'}, status=403)
            if task.assigned_to != user:
                return Response({'error': 'You can only update your own tasks'}, status=403)

        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        task = self.get_object()
        project = task.project
        user = request.user
        role = get_user_role(project, user)
        if project.owner != user and role != 'admin':
            return Response({'error': 'Admin access required'}, status=403)
        return super().destroy(request, *args, **kwargs)
