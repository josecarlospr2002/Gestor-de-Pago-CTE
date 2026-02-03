from django.db import models
from django.core.validators import RegexValidator, MinValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from num2words import num2words
import datetime


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
    numero_de_H90 = models.IntegerField(
        verbose_name="H90:",
        null=True,
        blank=True,
        help_text="Número consecutivo por forma de pago y año. Editable, pero no puede repetirse."
    )
    fecha_del_modelo = models.DateField(
        verbose_name="Fecha del Modelo"
    )
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

    inversiones = models.BooleanField(
        default=False,
        verbose_name="Inversiones",
        help_text="Marque si esta solicitud corresponde a inversiones."
    )

    importe_inversiones = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        editable=False,
        verbose_name="Importe de Inversiones"
    )

    descripcion = models.TextField(
        verbose_name="Descripción",
        blank=True,
        null=True,
        help_text="Opcional: escriba cualquier detalle adicional sobre la solicitud."
    )

    @property
    def importe_total_letras(self):
        if self.importe_total is None:
            return ""
        entero = int(self.importe_total)
        centavos = int(round((self.importe_total - entero) * 100))
        texto_entero = num2words(entero, lang='es')
        texto_centavos = num2words(centavos, lang='es')
        return f"{texto_entero} pesos con {texto_centavos} centavos"

    def calcular_importe_total(self):
        normales = self.conceptos_normales.all()
        salarios = self.conceptos_salarios.all()

        if normales.exists() and salarios.exists():
            return 0, "No se pueden guardar datos en ambas tablas a la vez."

        if normales.exists():
            primer_concepto = normales.first().concepto
            if primer_concepto == "Ninguno":
                return sum(c.importe for c in normales), None
            if all(c.concepto == primer_concepto for c in normales):
                total = sum(c.importe for c in normales)
                return total, None
            else:
                return 0, "Los conceptos normales son distintos, no se realizó la suma."

        if salarios.exists():
            total = sum(c.importe for c in salarios)
            return total, None

        return 0, "Debe existir al menos un concepto en alguna tabla."

    def clean(self):
        """Validaciones de fecha y unicidad por forma de pago + año"""
        super().clean()
        hoy = timezone.now().date()

        # Asegurar que fecha_del_modelo sea un date
        fecha = self.fecha_del_modelo
        if isinstance(fecha, datetime.datetime):
            fecha = fecha.date()

        if fecha > hoy:
            raise ValidationError({
                "fecha_del_modelo": "La fecha no puede ser futura. Solo se permiten hoy o fechas anteriores."
            })

        # Validación de unicidad de H90 por forma de pago + año
        año = fecha.year
        if self.numero_de_H90:
            existe = SolicitudesDePago.objects.filter(
                forma_de_pago=self.forma_de_pago,
                fecha_del_modelo__year=año,
                numero_de_H90=self.numero_de_H90
            ).exclude(pk=self.pk).exists()
            if existe:
                raise ValidationError({
                    "numero_de_H90": f"Ya existe un H90 con número {self.numero_de_H90} para {self.forma_de_pago} en {año}."
                })

    def save(self, *args, **kwargs):
        if self.identificador_del_proveedor:
            self.nombre_del_proveedor = self.identificador_del_proveedor.tit_de_la_cuenta
            self.codigo_del_proveedor = self.identificador_del_proveedor.codigo
            self.cuenta_bancaria = self.identificador_del_proveedor.cuenta_banc
            self.direccion_proveedor = self.identificador_del_proveedor.direccion

        año = self.fecha_del_modelo.year
        if not self.numero_de_H90:  # si el usuario no lo asigna manualmente
            ultimo = SolicitudesDePago.objects.filter(
                forma_de_pago=self.forma_de_pago,
                fecha_del_modelo__year=año
            ).order_by('-numero_de_H90').first()
            self.numero_de_H90 = (ultimo.numero_de_H90 + 1) if ultimo else 1

        # Lógica de inversiones
        if self.inversiones:
            self.importe_inversiones = self.importe_total
        else:
            self.importe_inversiones = 0

        super().save(*args, **kwargs)

    def __str__(self):
        return f"H90 {self.numero_de_H90} - {self.forma_de_pago}"


class ConceptoNormal(models.Model):
    CONCEPTO_CHOICES = (
        ("Factura", "Factura"),
        ("Prefactura", "Prefactura"),
        ("Cotización", "Cotización"),
        ("Ninguno", "Ninguno"),
    )
    solicitud = models.ForeignKey(
        SolicitudesDePago,
        on_delete=models.CASCADE,
        related_name="conceptos_normales"
    )
    concepto = models.CharField(max_length=20, choices=CONCEPTO_CHOICES, verbose_name="Concepto")

    numero = models.CharField(
        max_length=50,
        verbose_name="Número",
        null=True,
        blank=True,
        help_text="Puede contener números, letras, espacios o caracteres especiales."
    )

    importe = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name="Importe"
    )

    class Meta:
        verbose_name = "Concepto normal"
        verbose_name_plural = "Conceptos normales"
        ordering = ("concepto", "numero")

    def clean(self):
        super().clean()
        if self.concepto in ["Factura", "Prefactura", "Cotización"]:
            if not self.numero:
                raise ValidationError({
                    "numero": f"El campo Número es obligatorio para el concepto {self.concepto}."
                })
        elif self.concepto == "Ninguno":
            if self.numero:
                raise ValidationError({
                    "numero": "El campo Número debe quedar vacío cuando el concepto es 'Ninguno'."
                })

    def __str__(self):
        return f"{self.concepto} #{self.numero if self.numero else '-'} - {self.importe}"


class ConceptoSalario(models.Model):
    CONCEPTO_CHOICES = (
        ("Salario", "Salario"),
        ("Vacaciones", "Vacaciones"),
        ("Subsidio", "Subsidio"),
        ("Prima", "Prima"),
        ("Pago de Utilidades", "Pago de Utilidades"),
        ("Reembolso", "Reembolso"),
    )
    solicitud = models.ForeignKey(
        SolicitudesDePago,
        on_delete=models.CASCADE,
        related_name="conceptos_salarios"
    )
    concepto = models.CharField(max_length=30, choices=CONCEPTO_CHOICES, verbose_name="Concepto")
    numero = models.PositiveIntegerField(verbose_name="Número", null=True, blank=True)  # debe quedar vacío
    importe = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name="Importe"
    )

    class Meta:
        verbose_name = "Concepto salario"
        verbose_name_plural = "Conceptos salario"
        ordering = ("concepto",)

    def __str__(self):
        return f"{self.concepto} - {self.importe}"
