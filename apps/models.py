from django.db import models

class Proveedores(models.Model):
    ident_del_prov = models.CharField(max_length=255, verbose_name="Identificador del Prov:")
    tit_de_la_cuenta = models.CharField(max_length=255, verbose_name="Titular de la Cuenta:")
    abrev_del_tit = models.CharField(max_length=255, verbose_name="Abreviatura:")
    codigo = models.CharField(max_length=255, verbose_name="Código:")
    cuenta_banc = models.FloatField(verbose_name="Cuenta Bancaria:")
    direccion = models.CharField(max_length=255, verbose_name="Dirección:")

    def __str__(self):
        return self.ident_del_prov
