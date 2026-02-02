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
        help_texts = {
            "fecha_del_modelo": "La fecha no puede ser futura. Solo se permiten fechas de hoy o anteriores."
        }
        widgets = {
            "fecha_del_modelo": forms.DateInput(
                format="%Y-%m-%d",
                attrs={
                    "type": "date",
                    "class": "vDateField",
                    "max": date.today().strftime("%Y-%m-%d"),
                    "value": date.today().strftime("%Y-%m-%d"),
                }
            )
        }


# --- Filtro personalizado por Año ---
class AñoFilter(admin.SimpleListFilter):
    title = 'Año'
    parameter_name = 'año'

    def lookups(self, request, model_admin):
        años = SolicitudesDePago.objects.dates('fecha_del_modelo', 'year')
        return [(a.year, a.year) for a in años]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(fecha_del_modelo__year=self.value())
        return queryset


# --- Filtro personalizado por Mes ---
class MesFilter(admin.SimpleListFilter):
    title = 'Mes'
    parameter_name = 'mes'

    def lookups(self, request, model_admin):
        meses = [
            (1, "Enero"), (2, "Febrero"), (3, "Marzo"), (4, "Abril"),
            (5, "Mayo"), (6, "Junio"), (7, "Julio"), (8, "Agosto"),
            (9, "Septiembre"), (10, "Octubre"), (11, "Noviembre"), (12, "Diciembre"),
        ]
        return meses

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(fecha_del_modelo__month=self.value())
        return queryset


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
            if self.instance.forma_de_pago != "Cheque":
                raise ValidationError("Cuando se registran conceptos de salario, la forma de pago debe ser Cheque.")


class ConceptoSalarioInline(admin.TabularInline):
    model = ConceptoSalario
    formset = ConceptoSalarioInlineFormset
    extra = 0
    fields = ("concepto", "importe")


# --- Admin de Proveedores ---
@admin.register(Proveedores)
class ProveedoresAdmin(admin.ModelAdmin):
    list_display = (
        'codigo',
        'mostrar_beneficiario',
        'tit_de_la_cuenta',
        'cuenta_banc',
        'direccion'
    )
    search_fields = ('codigo', 'ident_del_prov', 'tit_de_la_cuenta', 'cuenta_banc')
    list_display_links = list(list_display).copy()

    def mostrar_beneficiario(self, obj):
        return obj.ident_del_prov

    mostrar_beneficiario.short_description = "Beneficiario:"   # 🔥 nombre de la columna
    mostrar_beneficiario.admin_order_field = "ident_del_prov" # 🔥 habilita ordenación alfabética

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
        'inversiones',
        'importe_inversiones',
    )

    # 🔥 Filtros separados: Cuenta, Año y Mes
    list_filter = (
        'cuenta_de_empresa',
        'forma_de_pago',
        MesFilter,
        AñoFilter,
    )

    list_display_links = list(list_display).copy()

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
        "inversiones",
        "importe_inversiones",
        "descripcion",
    )

    readonly_fields = (
        "nombre_del_proveedor",
        "codigo_del_proveedor",
        "cuenta_bancaria",
        "direccion_proveedor",
        "importe_total",
        "importe_total_letras",
        "importe_inversiones",
    )

    def save_model(self, request, obj, form, change):
        año = obj.fecha_del_modelo.year
        if obj.numero_de_H90:
            existe = SolicitudesDePago.objects.filter(
                forma_de_pago=obj.forma_de_pago,
                fecha_del_modelo__year=año,
                numero_de_H90=obj.numero_de_H90
            ).exclude(pk=obj.pk).exists()
            if existe:
                raise ValidationError(
                    f"Ya existe un H90 con número {obj.numero_de_H90} para {obj.forma_de_pago} en {año}."
                )
        super().save_model(request, obj, form, change)

    def save_related(self, request, form, formsets, change):
        normales = any(getattr(fs, "has_normales", False) for fs in formsets)
        salarios = any(getattr(fs, "has_salarios", False) for fs in formsets)

        if normales and salarios:
            raise ValidationError("No puede llenar datos en ambas tablas al mismo tiempo.")
        if not normales and not salarios:
            raise ValidationError("Debe agregar al menos un concepto en alguna de las tablas.")

        super().save_related(request, form, formsets, change)

        obj = form.instance
        total, mensaje = obj.calcular_importe_total()
        obj.importe_total = total
        obj.save(update_fields=["importe_total", "importe_inversiones"])
        if mensaje:
            messages.warning(request, mensaje)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path("get-next-h90/", self.admin_site.admin_view(self.get_next_h90), name="solicitudesdepago_get_next_h90"),
            path("get-proveedor/<int:pk>/", self.admin_site.admin_view(self.get_proveedor), name="solicitudesdepago_get_proveedor"),
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
