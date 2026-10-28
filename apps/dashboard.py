from decimal import Decimal

from django.contrib.admin import AdminSite
from django.db.models import Sum

from .models import (
    Ingreso, OperacionesEmitidas, ServicioBancario, AjusteInversiones, SaldoInicial,
)

CUENTAS_VALIDAS = ("CUP", "ANIR", "PRESUPUESTO")
CUENTA_DEFAULT = "CUP"


def formato_es(valor):
    if valor is None:
        valor = 0
    s = f"{float(valor):,.2f}"
    return s.replace(",", " ").replace(".", ",")


def _obtener_saldo_inicial(cuenta):

    campos = (
        "saldo_empresa",
        "saldo_empresa_calculado",
        "saldo_banco",
        "transito",
        "saldo_inversiones",
        "saldo_operaciones",
    )
    try:
        si = SaldoInicial.objects.get(cuenta_de_empresa=cuenta)
        return {c: getattr(si, c) for c in campos}
    except SaldoInicial.DoesNotExist:
        return {c: Decimal("0") for c in campos}


def _saldos_iniciales_listos():
    """True solo si existen los 3 SaldoInicial (CUP, ANIR, PRESUPUESTO)."""
    cuentas_requeridas = set(CUENTAS_VALIDAS)
    cuentas_cargadas = set(
        SaldoInicial.objects.values_list("cuenta_de_empresa", flat=True)
    )
    return cuentas_requeridas.issubset(cuentas_cargadas)


def _calcular_saldos(cuenta):

    base = _obtener_saldo_inicial(cuenta)

    ingresos = Ingreso.objects.filter(cuenta_de_empresa=cuenta)

    venta_reint_cred = ingresos.filter(
        tipo_ingreso__in=["Venta", "Reintegro", "Crédito"]
    )
    transferencias = ingresos.filter(tipo_ingreso="Transferencia")
    transferencias_debitadas = transferencias.filter(fecha_debito__isnull=False)
    inversiones_ingreso = ingresos.filter(tipo_ingreso="Inversiones")

    def suma(qs, campo="importe"):
        return qs.aggregate(total=Sum(campo))["total"] or Decimal("0")

    venta_reint_cred_total = suma(venta_reint_cred)
    transferencias_total = suma(transferencias)
    transferencias_debitadas_total = suma(transferencias_debitadas)
    inversiones_ingreso_total = suma(inversiones_ingreso)

    afectan_saldos = OperacionesEmitidas.objects.filter(
        solicitud__cuenta_de_empresa=cuenta,
        estado__in=["Tránsito", "Debitado"],
    )
    solo_transito = afectan_saldos.filter(estado="Tránsito")
    solo_debitadas = afectan_saldos.filter(estado="Debitado")

    afectan_normales = afectan_saldos.filter(solicitud__inversiones=False)
    afectan_inversiones = afectan_saldos.filter(solicitud__inversiones=True)

    afectan_normales_total = suma(afectan_normales, "importe_emitido")
    afectan_inversiones_total = suma(afectan_inversiones, "importe_emitido")
    afectan_total = afectan_normales_total + afectan_inversiones_total

    transito_total = suma(solo_transito, "importe_emitido")
    debitadas_total = suma(solo_debitadas, "importe_emitido")

    servicios_total = suma(
        ServicioBancario.objects.filter(cuenta_de_empresa=cuenta)
    )

    ajustes_total = suma(
        AjusteInversiones.objects.filter(cuenta_de_empresa=cuenta)
    )

    saldo_banco = (
        base["saldo_banco"]
        + venta_reint_cred_total
        + transferencias_debitadas_total
        - debitadas_total
        - servicios_total
    )

    saldo_empresa = (
        base["saldo_empresa"]
        + venta_reint_cred_total
        + transferencias_total
        - afectan_total
        - servicios_total
    )

    saldo_empresa_calculado = (
        base["saldo_empresa_calculado"]
        + venta_reint_cred_total
        + transferencias_debitadas_total
        - afectan_total
        - servicios_total
    )

    saldo_operaciones = (
        base["saldo_operaciones"]
        + venta_reint_cred_total
        + transferencias_total
        - inversiones_ingreso_total
        - afectan_normales_total
        - servicios_total
        + ajustes_total
    )

    saldo_inversiones = (
        base["saldo_inversiones"]
        + inversiones_ingreso_total
        - afectan_inversiones_total
        - ajustes_total
    )

    transito = base["transito"] + transito_total

    return {
        "saldo_empresa": formato_es(saldo_empresa),
        "saldo_empresa_calculado": formato_es(saldo_empresa_calculado),
        "saldo_banco": formato_es(saldo_banco),
        "transito": formato_es(transito),
        "saldo_inversiones": formato_es(saldo_inversiones),
        "saldo_operaciones": formato_es(saldo_operaciones),
    }


_index_original = AdminSite.index


def _index_con_dashboard(self, request, extra_context=None):
    cuenta = request.GET.get("cuenta", CUENTA_DEFAULT)
    if cuenta not in CUENTAS_VALIDAS:
        cuenta = CUENTA_DEFAULT

    extra_context = extra_context or {}
    extra_context["cuenta_actual"] = cuenta
    extra_context["cuentas"] = CUENTAS_VALIDAS
    extra_context["saldos_listos"] = _saldos_iniciales_listos()
    extra_context.update(_calcular_saldos(cuenta))

    return _index_original(self, request, extra_context=extra_context)


AdminSite.index = _index_con_dashboard