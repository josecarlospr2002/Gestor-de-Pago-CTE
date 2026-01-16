from django.core.exceptions import ValidationError
from django.contrib import admin, messages
from django.urls import path
from django.http import JsonResponse
from django.forms.models import BaseInlineFormSet
from datetime import date

from .models import Proveedores, SolicitudesDePago, ConceptoDePago


# Formset para validar que exista al menos un concepto válido
class ConceptoDePagoInlineFormset(BaseInlineFormSet):
    def clean(self):
        super().clean()
        valid_forms = [
            form for form in self.forms
            if form.cleaned_data and not form.cleaned_data.get("DELETE", False)
        ]
        if len(valid_forms) < 1:
            raise ValidationError("Debes agregar al menos un concepto de pago con número e importe.")


class ConceptoDePagoInline(admin.TabularInline):
    model = ConceptoDePago
    formset = ConceptoDePagoInlineFormset
    extra = 0
    fields = ("concepto", "numero", "importe")


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


@admin.register(SolicitudesDePago)
class SolicitudesDePagoAdmin(admin.ModelAdmin):
    list_display = (
        'numero_de_H90',
        'fecha_del_modelo',
        'forma_de_pago',
        'cuenta_de_empresa',
        "identificador_del_proveedor",
        'nombre_del_proveedor',
        'importe_total',   # solo este, sin letras ni descripción
    )

    fields = (
        'numero_de_H90',
        'fecha_del_modelo',
        'forma_de_pago',
        'cuenta_de_empresa',
        "identificador_del_proveedor",
        'nombre_del_proveedor',
        "codigo_del_proveedor",
        "cuenta_bancaria",
        "direccion_proveedor",
        "importe_total",
        "importe_total_letras",  # se ve en el formulario
        "descripcion",           # se ve en el formulario
    )

    readonly_fields = (
        'numero_de_H90',
        "nombre_del_proveedor",
        "codigo_del_proveedor",
        "cuenta_bancaria",
        "direccion_proveedor",
        "importe_total",
        "importe_total_letras",  # solo lectura
    )

    search_fields = (
        'numero_de_H90',
        'forma_de_pago',
        'cuenta_de_empresa',
        'identificador_del_proveedor__ident_del_prov',
        'identificador_del_proveedor__tit_de_la_cuenta',
    )

    list_display_links = list(list_display).copy()
    inlines = [ConceptoDePagoInline]

    class Media:
        js = ("js/h90_autofill.js",)

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)

        obj = form.instance
        # Recalcular importe total si hay conceptos
        if obj.conceptos.exists():
            total, mensaje = obj.calcular_importe_total()
            obj.importe_total = total
            obj.save(update_fields=["importe_total"])
            if mensaje:
                messages.warning(request, mensaje)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "get-next-h90/",
                self.admin_site.admin_view(self.get_next_h90),
                name="solicitudesdepago_get_next_h90",
            ),
            path(
                "get-proveedor/<int:pk>/",
                self.admin_site.admin_view(self.get_proveedor),
                name="solicitudesdepago_get_proveedor",
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

        nuevo = ultimo.numero_de_H90 + 1 if ultimo else 1
        return JsonResponse({"numero": nuevo})

    def get_proveedor(self, request, pk):
        proveedor = Proveedores.objects.get(pk=pk)
        data = {
            "titular": proveedor.tit_de_la_cuenta,
            "codigo": proveedor.codigo,
            "cuenta_bancaria": proveedor.cuenta_banc,
            "direccion": proveedor.direccion,
        }
        return JsonResponse(data)
