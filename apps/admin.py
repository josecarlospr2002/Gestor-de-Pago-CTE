from django.contrib import admin

from .models import Proveedores

# Register your models here.

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