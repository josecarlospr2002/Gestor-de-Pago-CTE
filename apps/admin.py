from django import forms
from django.core.exceptions import ValidationError
from django.contrib import admin, messages
from django.urls import path
from django.http import JsonResponse
from django.forms.models import BaseInlineFormSet
from django.db.models import Sum
from datetime import date
from .models import Proveedores, SolicitudesDePago, ConceptoNormal, ConceptoSalario, OperacionesEmitidas
from django.utils.html import format_html
from django.shortcuts import render, redirect, get_object_or_404

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
            ),
            "descripcion": forms.Textarea(
                attrs={
                    "rows": 3,
                    "cols": 50,
                    "style": "resize:none;"
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = kwargs.get('instance')
        if not instance or not instance.pk:
            self.fields['estado'].choices = [("Activo", "Activo")]
        else:
            if instance.estado == "Activo":
                self.fields['estado'].choices = [
                    ("Activo", "Activo"),
                    ("Emitido", "Emitido"),
                    ("Cancelado", "Cancelado"),
                ]


# Filtro por Año (Solicitudes)
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


# Filtro por Mes (Solicitudes)
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


# Filtro por Año (Operaciones Emitidas)
class AñoFilterOE(admin.SimpleListFilter):
    title = 'Año'
    parameter_name = 'año'

    def lookups(self, request, model_admin):
        años = OperacionesEmitidas.objects.dates('fecha_inicial', 'year')
        return [(a.year, a.year) for a in años]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(fecha_inicial__year=self.value())
        return queryset


# Filtro por Mes (Operaciones Emitidas)
class MesFilterOE(admin.SimpleListFilter):
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
            return queryset.filter(fecha_inicial__month=self.value())
        return queryset


# Filtro por Tipo de Operación
class TipoOperacionFilter(admin.SimpleListFilter):
    title = 'Tipo de Operación'
    parameter_name = 'tipo_operacion'

    def lookups(self, request, model_admin):
        return [
            ("Cheques", "Cheques"),
            ("Transferencias", "Transferencias"),
            ("Inversiones", "Inversiones"),
        ]

    def queryset(self, request, queryset):
        if self.value() == "Cheques":
            return queryset.filter(solicitud__forma_de_pago="Cheque")
        if self.value() == "Transferencias":
            return queryset.filter(solicitud__forma_de_pago="Transferencia")
        if self.value() == "Inversiones":
            return queryset.filter(solicitud__inversiones=True)
        return queryset


# Inlines para Conceptos Normales
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


# Inlines para Conceptos Salario
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

    mostrar_beneficiario.short_description = "Beneficiario:"
    mostrar_beneficiario.admin_order_field = "ident_del_prov"

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context['show_history'] = False
        return super().change_view(request, object_id, form_url, extra_context=extra_context)


@admin.register(SolicitudesDePago)
class SolicitudesDePagoAdmin(admin.ModelAdmin):
    form = SolicitudesDePagoForm
    inlines = [ConceptoNormalInline, ConceptoSalarioInline]

    list_display = (
        'numero_de_H90',
        'mostrar_beneficiario',
        'mostrar_importe',
        'mostrar_fecha',
        'mostrar_conceptos_pago',
        'mostrar_estado',
    )

    list_filter = (
        'cuenta_de_empresa',
        'forma_de_pago',
        MesFilter,
        AñoFilter,
        'estado',
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
        "estado",
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

    def mostrar_estado(self, obj):
        if obj.estado == "Cancelado":
            return format_html('<span style="display:none;">Cancelado</span>Cancelado')
        elif obj.estado == "Emitido":
            return format_html('<span style="display:none;">Emitido</span>Emitido')
        return format_html('<span style="display:none;">Activo</span>Activo')

    mostrar_estado.short_description = "Estado"
    mostrar_estado.admin_order_field = "estado"

    def get_row_class(self, obj):
        if obj.estado == "Cancelado":
            return 'cancelado'
        elif obj.estado == "Emitido":
            return 'emitido'
        return ''

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.estado in ("Cancelado", "Emitido"):
            campos = [field.name for field in self.model._meta.fields]
            campos.append('importe_total_letras')
            return campos
        return self.readonly_fields

    def mostrar_beneficiario(self, obj):
        return obj.identificador_del_proveedor
    mostrar_beneficiario.short_description = "Beneficiario"
    mostrar_beneficiario.admin_order_field = "identificador_del_proveedor__ident_del_prov"

    def mostrar_fecha(self, obj):
        return obj.fecha_del_modelo.strftime("%d/%m/%Y")
    mostrar_fecha.short_description = "Fecha"
    mostrar_fecha.admin_order_field = "fecha_del_modelo"

    def mostrar_importe(self, obj):
        if obj.importe_total is not None:
            s = f"{float(obj.importe_total):,.2f}"
            return s.replace(",", " ").replace(".", ",")
        return "0,00"
    mostrar_importe.short_description = "Importe"
    mostrar_importe.admin_order_field = "importe_total"

    def mostrar_conceptos_pago(self, obj):
        partes = []
        normales = obj.conceptos_normales.all()
        if normales.exists():
            concepto = normales.first().concepto
            numeros = [c.numero for c in normales if c.numero]
            numeros_str = ", ".join(numeros) if numeros else ""
            texto = concepto
            if numeros_str:
                texto += " " + numeros_str
            partes.append(texto)
        salarios = obj.conceptos_salarios.all()
        if salarios.exists():
            conceptos_salarios = sorted(set(c.concepto for c in salarios))
            texto = ", ".join(conceptos_salarios)
            partes.append(texto)
        resultado = " | ".join(partes) if partes else "—"
        if obj.descripcion:
            resultado += f" | {obj.descripcion}"
        return resultado

    mostrar_conceptos_pago.short_description = "Conceptos de Pago"
    mostrar_conceptos_pago.admin_order_field = "descripcion"

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        response = super().changelist_view(request, extra_context=extra_context)
        try:
            queryset = response.context_data['cl'].queryset
        except (AttributeError, KeyError):
            return response
        cantidad_pagos = queryset.count()
        importe_total = queryset.aggregate(total=Sum('importe_total'))['total'] or 0
        importe_inversiones = queryset.aggregate(total=Sum('importe_inversiones'))['total'] or 0
        def formato(valor):
            if valor is not None:
                s = f"{float(valor):,.2f}"
                return s.replace(",", " ").replace(".", ",")
            return "0,00"
        extra_context['cantidad_pagos'] = cantidad_pagos
        extra_context['importe_total_display'] = formato(importe_total)
        extra_context['importe_inversiones_display'] = formato(importe_inversiones)
        response.context_data.update(extra_context)
        return response

    def save_model(self, request, obj, form, change):
        año = obj.fecha_del_modelo.year
        if obj.numero_de_H90:
            existe = SolicitudesDePago.objects.filter(
                forma_de_pago=obj.forma_de_pago,
                cuenta_de_empresa=obj.cuenta_de_empresa,
                fecha_del_modelo__year=año,
                numero_de_H90=obj.numero_de_H90
            ).exclude(pk=obj.pk).exists()
            if existe:
                raise ValidationError(
                    f"Ya existe un H90 con número {obj.numero_de_H90} para "
                    f"{obj.forma_de_pago} - {obj.cuenta_de_empresa} en {año}."
                )
        super().save_model(request, obj, form, change)

    def save_related(self, request, form, formsets, change):
        normales = any(getattr(fs, "has_normales", False) for fs in formsets)
        salarios = any(getattr(fs, "has_salarios", False) for fs in formsets)
        if normales and salarios:
            raise ValidationError("No puede dejar llenas ni vacías ambas tablas. Solo una puede contener datos.")
        if not normales and not salarios:
            raise ValidationError("No puede dejar llenas ni vacías ambas tablas. Solo una puede contener datos.")
        super().save_related(request, form, formsets, change)
        obj = form.instance
        total, mensaje = obj.calcular_importe_total()
        obj.importe_total = total
        obj.save(update_fields=["importe_total", "importe_inversiones"])
        if mensaje:
            messages.warning(request, mensaje)

    def response_change(self, request, obj):
        if obj.estado == "Emitido" and not hasattr(obj, '_operacion_creada'):
            return redirect('admin:solicitudesdepago_emitir', pk=obj.pk)
        return super().response_change(request, obj)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path("get-next-h90/", self.admin_site.admin_view(self.get_next_h90), name="solicitudesdepago_get_next_h90"),
            path("get-proveedor/<int:pk>/", self.admin_site.admin_view(self.get_proveedor), name="solicitudesdepago_get_proveedor"),
            path("emitir-h90/<int:pk>/", self.admin_site.admin_view(self.emitir_h90), name="solicitudesdepago_emitir"),
        ]
        return custom_urls + urls

    def emitir_h90(self, request, pk):
        solicitud = get_object_or_404(SolicitudesDePago, pk=pk)

        if request.method == "POST":
            numero_serie = request.POST.get("numero_serie")
            fecha_inicial = request.POST.get("fecha_inicial")

            if not numero_serie or not fecha_inicial:
                messages.error(request, "Debe completar Número de Serie y Fecha Inicial.")
                return redirect('admin:apps_solicitudesdepago_change', pk)

            solicitud.estado = "Emitido"
            solicitud._operacion_creada = True
            solicitud.save()

            OperacionesEmitidas.objects.create(
                solicitud=solicitud,
                fecha_emision=date.today(),
                numero_operacion=f"H90-{solicitud.numero_de_H90}-{solicitud.forma_de_pago}-{solicitud.cuenta_de_empresa}-{solicitud.fecha_del_modelo.year}",
                estado="Tránsito",
                importe_emitido=solicitud.importe_total,
                numero_serie=numero_serie,
                fecha_inicial=fecha_inicial,
            )

            messages.success(request, f"H90 N° {solicitud.numero_de_H90} emitido correctamente.")
            return redirect('admin:apps_solicitudesdepago_changelist')

        return render(request, 'admin/apps/solicitudesdepago/emitir_modal.html', {
            'solicitud': solicitud,
            'opts': self.model._meta,
        })

    def get_next_h90(self, request):
        forma = request.GET.get("forma")
        cuenta = request.GET.get("cuenta")
        fecha = request.GET.get("fecha")
        if not forma or not fecha:
            return JsonResponse({"numero": ""})
        from datetime import datetime
        año = datetime.strptime(fecha, "%Y-%m-%d").year
        ultimo = SolicitudesDePago.objects.filter(
            forma_de_pago=forma,
            cuenta_de_empresa=cuenta,
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

    def has_delete_permission(self, request, obj=None):
        return False

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        obj = self.get_object(request, object_id)
        extra_context['show_history'] = False
        if obj and obj.estado in ("Cancelado", "Emitido"):
            extra_context['show_save'] = False
            extra_context['show_save_and_continue'] = False
            extra_context['show_save_and_add_another'] = False
            extra_context['show_delete_link'] = False
            extra_context['show_close'] = True
        return super().change_view(request, object_id, form_url, extra_context=extra_context)


@admin.register(OperacionesEmitidas)
class OperacionesEmitidasAdmin(admin.ModelAdmin):
    list_display = (
        'mostrar_h90',
        'mostrar_no_cheque',
        'fecha_inicial_formateada',
        'importe_emitido',
        'estado',
        'fecha_final_formateada',
        'mostrar_concepto',
        'mostrar_suministrador',
        'mostrar_estado_operacion',
    )
    list_display_links = list(list_display).copy()
    list_filter = (
        'solicitud__cuenta_de_empresa',
        TipoOperacionFilter,
        MesFilterOE,
        AñoFilterOE,
        'estado',
    )
    search_fields = ()

    class Media:
        js = ('js/operaciones_fecha_final.js',)

    def mostrar_h90(self, obj):
        return obj.solicitud.numero_de_H90
    mostrar_h90.short_description = "H90"
    mostrar_h90.admin_order_field = "solicitud__numero_de_H90"

    def mostrar_no_cheque(self, obj):
        return obj.numero_serie
    mostrar_no_cheque.short_description = "No. Cheque"
    mostrar_no_cheque.admin_order_field = "numero_serie"

    def fecha_inicial_formateada(self, obj):
        return obj.fecha_inicial.strftime("%d/%m/%Y")
    fecha_inicial_formateada.short_description = "Fecha Inicial"
    fecha_inicial_formateada.admin_order_field = "fecha_inicial"

    def fecha_final_formateada(self, obj):
        if obj.fecha_final:
            return obj.fecha_final.strftime("%d/%m/%Y")
        return "—"
    fecha_final_formateada.short_description = "Fecha Final"
    fecha_final_formateada.admin_order_field = "fecha_final"

    def mostrar_concepto(self, obj):
        solicitud = obj.solicitud
        partes = []
        normales = solicitud.conceptos_normales.all()
        if normales.exists():
            concepto = normales.first().concepto
            numeros = [c.numero for c in normales if c.numero]
            numeros_str = ", ".join(numeros) if numeros else ""
            texto = concepto
            if numeros_str:
                texto += " " + numeros_str
            partes.append(texto)
        salarios = solicitud.conceptos_salarios.all()
        if salarios.exists():
            conceptos_salarios = sorted(set(c.concepto for c in salarios))
            texto = ", ".join(conceptos_salarios)
            partes.append(texto)
        resultado = " | ".join(partes) if partes else "—"
        if solicitud.descripcion:
            resultado += f" | {solicitud.descripcion}"
        return resultado
    mostrar_concepto.short_description = "Concepto"
    mostrar_concepto.admin_order_field = "solicitud__descripcion"

    def mostrar_suministrador(self, obj):
        return obj.solicitud.identificador_del_proveedor
    mostrar_suministrador.short_description = "Suministrador"
    mostrar_suministrador.admin_order_field = "solicitud__identificador_del_proveedor__ident_del_prov"

    def mostrar_estado_operacion(self, obj):
        if obj.estado == "Cancelado":
            return format_html('<span style="display:none;">Cancelado</span>Cancelado')
        elif obj.estado == "Debitado":
            return format_html('<span style="display:none;">Debitado</span>Debitado')
        return format_html('<span style="display:none;">Tránsito</span>Tránsito')
    mostrar_estado_operacion.short_description = ""

    def get_row_class(self, obj):
        if obj.estado == "Cancelado":
            return 'cancelado'
        return ''