from django.contrib import admin
from django.urls import path
from django.http import JsonResponse
from datetime import date

from .models import *

@admin.register(Proveedores)
class ProveedoresAdmin(admin.ModelAdmin):
    list_display = (
        'ident_del_prov',
        'tit_de_la_cuenta',
        'abrev_del_tit',
        'codigo',
        'cuenta_banc',
        'direccion'
    )

    search_fields = ('ident_del_prov', 'tit_de_la_cuenta', 'codigo', 'cuenta_banc')
    list_display_links = list(list_display).copy()

    def changelist_view(self, request, extra_context=None):
        total = Proveedores.objects.count()
        extra_context = extra_context or {}
        extra_context['total_proveedores'] = total
        return super().changelist_view(request, extra_context=extra_context)


@admin.register(SolicitudesDePago)
class SolicitudesDePagoAdmin(admin.ModelAdmin):

    fields = (
        'numero_de_H90',
        'fecha_del_modelo',
        'forma_de_pago',
        'cuenta_de_empresa',
        "identificador_del_proveedor",
    )

    list_display = (
        'numero_de_H90',
        'fecha_del_modelo',
        'forma_de_pago',
        'cuenta_de_empresa',
        "identificador_del_proveedor",
        "nombre_del_proveedor",
        "codigo_del_proveedor",
        "cuenta_bancaria",
        "direccion_proveedor",
    )

    readonly_fields = (
        'numero_de_H90',
        "nombre_del_proveedor",
        "codigo_del_proveedor",
        "cuenta_bancaria",
        "direccion_proveedor",
    )

    search_fields = ('numero_de_H90', 'forma_de_pago',)
    list_display_links = list(list_display).copy()

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "get-next-h90/",
                self.admin_site.admin_view(self.get_next_h90),
                name="solicitudesdepago_get_next_h90",
            ),
        ]
        return custom_urls + urls

    def get_next_h90(self, request):
        forma = request.GET.get("forma")
        año = date.today().year

        if not forma:
            return JsonResponse({"numero": ""})

        ultimo = SolicitudesDePago.objects.filter(
            forma_de_pago=forma,
            fecha_del_modelo__year=año
        ).order_by('-numero_de_H90').first()

        if ultimo:
            nuevo = ultimo.numero_de_H90 + 1
        else:
            nuevo = 1

        return JsonResponse({"numero": nuevo})

    class Media:
        js = ("js/h90_autofill.js",)
