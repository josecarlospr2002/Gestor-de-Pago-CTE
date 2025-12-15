from django.contrib import admin
# from django.utils.html import format_html

from .models import Proveedores

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

    search_fields = ('ident_del_prov', 'tit_de_la_cuenta', 'codigo')

    def changelist_view(self, request, extra_context=None):
        total = Proveedores.objects.count()
        extra_context = extra_context or {}
        extra_context['total_proveedores'] = total
        return super().changelist_view(request, extra_context=extra_context)
