from django.contrib import admin
from django.urls import path
from django.shortcuts import redirect

from apps.views import inicializar_saldos, generar_pdf_h90, generar_pdf_operaciones

urlpatterns = [
    path('', lambda request: redirect('admin/login/')),
    path('admin/inicializar-saldos/', inicializar_saldos, name='inicializar_saldos'),

    path('admin/imprimir-h90/<int:pk>/', generar_pdf_h90, name='imprimir_h90'),

    path('admin/imprimir-operaciones/', generar_pdf_operaciones, name='imprimir_operaciones'),

    path('admin/', admin.site.urls),
]