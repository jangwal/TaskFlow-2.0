from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('projects', views.ProjectViewSet, basename='project')
router.register('tasks', views.TaskViewSet, basename='task')

urlpatterns = [
    path('auth/register/', views.register),
    path('auth/login/', views.login),
    path('auth/me/', views.me),
    path('users/', views.list_users),
    path('dashboard/', views.dashboard),
    path('', include(router.urls)),
]
