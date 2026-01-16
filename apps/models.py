from django.db import models
from django.core.validators import RegexValidator, MinValueValidator
from num2words import num2words  # librería para convertir números a palabras


class Proveedores(models.Model):
    ident_del_prov = models.CharField(max_length=255, verbose_name="Identificador del Prov:")
    tit_de_la_cuenta = models.CharField(max_length=255, verbose_name="Titular de la Cuenta:")
    abrev_del_tit = models.CharField(max_length=255, verbose_name="Abreviatura:")
    codigo = models.CharField(max_length=255, verbose_name="Código:")
    cuenta_banc = models.CharField(
        max_length=16,
        verbose_name="Cuenta Bancaria:",
        validators=[
            RegexValidator(
                regex=r'^\d{16}$',
                message="La cuenta bancaria debe contener exactamente 16 dígitos numéricos."
            )
        ]
    )
    direccion = models.CharField(max_length=255, verbose_name="Dirección:")

    class Meta:
        verbose_name = "Proveedor"
        verbose_name_plural = "Proveedores"

    def __str__(self):
        return f"{self.ident_del_prov}"


class SolicitudesDePago(models.Model):
    numero_de_H90 = models.IntegerField(verbose_name="H90:", null=True, blank=True)
    fecha_del_modelo = models.DateField(verbose_name="Fecha del Modelo")
    forma_de_pago = models.CharField(
        max_length=255,
        choices=(("Transferencia", "Transferencia"), ("Cheque", "Cheque")),
        verbose_name="Forma de Pago:"
    )
    cuenta_de_empresa = models.CharField(
        max_length=255,
        choices=(("CUP", "CUP"), ("ANIR", "ANIR"), ("PRESUPUESTO", "PRESUPUESTO")),
        verbose_name="Cuenta de Empresa:"
    )
    identificador_del_proveedor = models.ForeignKey(
        Proveedores,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="solicitudes_de_pago"
    )
    nombre_del_proveedor = models.CharField(max_length=100, blank=True, null=True)
    codigo_del_proveedor = models.CharField(max_length=20, blank=True, null=True)
    cuenta_bancaria = models.CharField(max_length=50, blank=True, null=True)
    direccion_proveedor = models.TextField(blank=True, null=True)

    importe_total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        editable=False,
        verbose_name="Importe Total"
    )

    @property
    def importe_total_letras(self):
        """Convierte el importe total a letras en español."""
        if self.importe_total is None:
            return ""
        entero = int(self.importe_total)
        centavos = int(round((self.importe_total - entero) * 100))
        texto_entero = num2words(entero, lang='es')
        texto_centavos = num2words(centavos, lang='es')
        return f"{texto_entero} pesos con {texto_centavos} centavos"

    # 👉 Nuevo campo opcional
    descripcion = models.TextField(
        verbose_name="Descripción",
        blank=True,
        null=True,
        help_text="Opcional: escriba cualquier detalle adicional sobre la solicitud."
    )

    def calcular_importe_total(self):
        conceptos = self.conceptos.all()
        if not conceptos.exists():
            return 0, None

        primer_concepto = conceptos.first().concepto
        if all(c.concepto == primer_concepto for c in conceptos):
            total = sum(c.importe for c in conceptos)
            return total, None
        else:
            return 0, "Los conceptos son distintos, no se realizó la suma."

    def save(self, *args, **kwargs):
        # Copiar datos del proveedor si existe
        if self.identificador_del_proveedor:
            self.nombre_del_proveedor = self.identificador_del_proveedor.tit_de_la_cuenta
            self.codigo_del_proveedor = self.identificador_del_proveedor.codigo
            self.cuenta_bancaria = self.identificador_del_proveedor.cuenta_banc
            self.direccion_proveedor = self.identificador_del_proveedor.direccion

        # Asignar/actualizar número de H90 por forma de pago y año
        año = self.fecha_del_modelo.year
        if self.pk:
            original = SolicitudesDePago.objects.get(pk=self.pk)
            if original.forma_de_pago != self.forma_de_pago or original.fecha_del_modelo.year != año:
                ultimo = SolicitudesDePago.objects.filter(
                    forma_de_pago=self.forma_de_pago,
                    fecha_del_modelo__year=año
                ).order_by('-numero_de_H90').first()
                self.numero_de_H90 = (ultimo.numero_de_H90 + 1) if ultimo else 1
        else:
            ultimo = SolicitudesDePago.objects.filter(
                forma_de_pago=self.forma_de_pago,
                fecha_del_modelo__year=año
            ).order_by('-numero_de_H90').first()
            self.numero_de_H90 = (ultimo.numero_de_H90 + 1) if ultimo else 1

        super().save(*args, **kwargs)

    def __str__(self):
        return f"H90 {self.numero_de_H90} - {self.forma_de_pago}"


class ConceptoDePago(models.Model):
    CONCEPTO_CHOICES = (
        ("Factura", "Factura"),
        ("Prefactura", "Prefactura"),
        ("Cotización", "Cotización"),
        ("Ninguno", "Ninguno"),
    )
    solicitud = models.ForeignKey(
        SolicitudesDePago,
        on_delete=models.CASCADE,
        related_name="conceptos"
    )
    concepto = models.CharField(max_length=20, choices=CONCEPTO_CHOICES, verbose_name="Concepto")
    numero = models.PositiveIntegerField(verbose_name="Número")
    importe = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name="Importe"
    )

    class Meta:
        verbose_name = "Concepto de pago"
        verbose_name_plural = "Conceptos de pago"
        ordering = ("concepto", "numero")

    def __str__(self):
        return f"{self.concepto} #{self.numero} - {self.importe}"
