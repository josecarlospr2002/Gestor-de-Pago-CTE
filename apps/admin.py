from django import forms
from django.core.exceptions import ValidationError
from django.contrib import admin, messages
from django.urls import path
from django.http import JsonResponse
from django.forms.models import BaseInlineFormSet
from datetime import date

from .models import Proveedores, SolicitudesDePago, ConceptoNormal, ConceptoSalario


# --- Formulario personalizado para SolicitudesDePago ---
class SolicitudesDePagoForm(forms.ModelForm):
    class Meta:
        model = SolicitudesDePago
        fields = "__all__"


# --- Inlines para Conceptos Normales ---
class ConceptoNormalInlineFormset(BaseInlineFormSet):
    def clean(self):
        super().clean()
        self.has_normales = False
        valid_forms = [
            form for form in self.forms
            if form.cleaned_data and not form.cleaned_data.get("DELETE", False)
        ]
        if valid_forms:
            self.has_normales = True
            conceptos = [form.cleaned_data.get("concepto") for form in valid_forms]
            if len(set(conceptos)) > 1:
                raise ValidationError("En conceptos normales, todos deben ser iguales.")


class ConceptoNormalInline(admin.TabularInline):
    model = ConceptoNormal
    formset = ConceptoNormalInlineFormset
    extra = 0
    fields = ("concepto", "numero", "importe")


# --- Inlines para Conceptos Salario ---
class ConceptoSalarioInlineFormset(BaseInlineFormSet):
    def clean(self):
        super().clean()
        self.has_salarios = False
        valid_forms = [
            form for form in self.forms
            if form.cleaned_data and not form.cleaned_data.get("DELETE", False)
        ]
        if valid_forms:
            self.has_salarios = True
            for form in valid_forms:
                if form.cleaned_data.get("numero"):
                    raise ValidationError("En conceptos de salario, el campo Número debe quedar vacío.")

            # Validación extra: si hay conceptos de salario, forma de pago debe ser Cheque
            if self.instance.forma_de_pago != "Cheque":
                raise ValidationError("Cuando se registran conceptos de salario, la forma de pago obligatoriamente debe ser Cheque.")


class ConceptoSalarioInline(admin.TabularInline):
    model = ConceptoSalario
    formset = ConceptoSalarioInlineFormset
    extra = 0
    fields = ("concepto", "importe")


# --- Admin de Proveedores ---
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


# --- Admin de Solicitudes ---
@admin.register(SolicitudesDePago)
class SolicitudesDePagoAdmin(admin.ModelAdmin):
    form = SolicitudesDePagoForm
    inlines = [ConceptoNormalInline, ConceptoSalarioInline]

    list_display = (
        'numero_de_H90',
        'fecha_del_modelo',
        'forma_de_pago',
        'cuenta_de_empresa',
        "identificador_del_proveedor",
        'nombre_del_proveedor',
        'importe_total',
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
        "importe_total_letras",
        "descripcion",
    )

    readonly_fields = (
        'numero_de_H90',
        "nombre_del_proveedor",
        "codigo_del_proveedor",
        "cuenta_bancaria",
        "direccion_proveedor",
        "importe_total",
        "importe_total_letras",
    )

    search_fields = (
        'numero_de_H90',
        'forma_de_pago',
        'cuenta_de_empresa',
        'identificador_del_proveedor__ident_del_prov',
        'identificador_del_proveedor__tit_de_la_cuenta',
    )

    list_display_links = list(list_display).copy()

    def save_related(self, request, form, formsets, change):
        normales = any(getattr(fs, "has_normales", False) for fs in formsets)
        salarios = any(getattr(fs, "has_salarios", False) for fs in formsets)

        # Validaciones globales: bloquean el guardado
        if normales and salarios:
            raise ValidationError("No puede llenar datos en ambas tablas al mismo tiempo.")

        if not normales and not salarios:
            raise ValidationError("Debe agregar al menos un concepto en una de las tablas.")

        super().save_related(request, form, formsets, change)

        obj = form.instance
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
