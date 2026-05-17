from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse
import os

def serve_index(request, path=''):
    html_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates', 'index.html')
    with open(html_path, 'r', encoding='utf-8') as f:
        content = f.read()
    return HttpResponse(content, content_type='text/html')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('', serve_index),
    path('<path:path>', serve_index),
]