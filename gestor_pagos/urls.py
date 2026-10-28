from django.contrib import admin
from django.urls import path
from django.shortcuts import redirect

from apps.views import inicializar_saldos


urlpatterns = [
    path('', lambda request: redirect('admin/login/')),
    path('admin/inicializar-saldos/', inicializar_saldos, name='inicializar_saldos'),
    path('admin/', admin.site.urls),
]