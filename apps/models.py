from django.db import models
from django.core.validators import RegexValidator


class Proveedores(models.Model):
    ident_del_prov = models.CharField(max_length=255, verbose_name="Identificador del Prov:")
    tit_de_la_cuenta = models.CharField(max_length=255, verbose_name="Titular de la Cuenta:")
    abrev_del_tit = models.CharField(max_length=255, verbose_name="Abreviatura:")
    codigo = models.CharField(max_length=255, verbose_name="Código:")
    cuenta_banc = models.CharField(max_length=16, verbose_name="Cuenta Bancaria:",
                                   validators=[
                                       RegexValidator(
                                           regex=r'^\d{16}$',
                                           message="La cuenta bancaria debe contener exactamente 16 dígitos numéricos."
                                       )
                                   ]
    )
    direccion = models.CharField(max_length=255, verbose_name="Dirección:")

    class Meta:
        verbose_name= "Proveedor"
        verbose_name_plural = "Proveedores"

    def __str__(self):
        return f"{self.ident_del_prov} | {self.tit_de_la_cuenta} | {self.codigo}"


class SolicitudesDePago(models.Model):
    numero_de_H90 = models.IntegerField(verbose_name="H90:", null=True, blank=True)
    fecha_del_modelo = models.DateField(verbose_name="Fecha del Modelo")
    forma_de_pago = models.CharField(max_length=255,
        choices=(("Transferencia", "Transferencia"), ("Cheque", "Cheque")),
        verbose_name="Forma de Pago:"
    )
    cuenta_de_empresa = models.CharField(max_length=255,
         choices=(("CUP", "CUP"), ("ANIR", "ANIR"), ("PRESUPUESTO", "PRESUPUESTO")),
         verbose_name="Cuenta de Empresa:"
    )

    def save(self, *args, **kwargs):
        año = self.fecha_del_modelo.year

        # Detectar si el objeto ya existía
        if self.pk:
            original = SolicitudesDePago.objects.get(pk=self.pk)

            # Si cambió la forma de pago, recalcular número
            if original.forma_de_pago != self.forma_de_pago:
                ultimo = SolicitudesDePago.objects.filter(
                    forma_de_pago=self.forma_de_pago,
                    fecha_del_modelo__year=año
                ).order_by('-numero_de_H90').first()

                if ultimo:
                    self.numero_de_H90 = ultimo.numero_de_H90 + 1
                else:
                    self.numero_de_H90 = 1

        else:
            # Caso normal: objeto nuevo
            ultimo = SolicitudesDePago.objects.filter(
                forma_de_pago=self.forma_de_pago,
                fecha_del_modelo__year=año
            ).order_by('-numero_de_H90').first()

            if ultimo:
                self.numero_de_H90 = ultimo.numero_de_H90 + 1
            else:
                self.numero_de_H90 = 1

        super().save(*args, **kwargs)

    def __str__(self):
        return f"H90 {self.numero_de_H90} - {self.forma_de_pago}"