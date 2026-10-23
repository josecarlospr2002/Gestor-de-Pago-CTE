from django.contrib.admin import AdminSite
from django.db.models import Sum

from .models import Ingreso

CUENTAS_VALIDAS = ("CUP", "ANIR", "PRESUPUESTO")
CUENTA_DEFAULT = "CUP"


def formato_es(valor):
    if valor is None:
        valor = 0
    s = f"{float(valor):,.2f}"
    return s.replace(",", " ").replace(".", ",")


def _calcular_saldos(cuenta):
    saldo_banco = (
                      Ingreso.objects
                          .filter(cuenta_de_empresa=cuenta)
                          .aggregate(total=Sum("importe"))["total"]
                  ) or 0

    return {
        "saldo_empresa": "0,00",
        "saldo_empresa_calculado": "0,00",
        "saldo_banco": formato_es(saldo_banco),
        "transito": "0,00",
        "saldo_inversiones": "0,00",
        "saldo_operaciones": "0,00",
    }


_index_original = AdminSite.index


def _index_con_dashboard(self, request, extra_context=None):
    cuenta = request.GET.get("cuenta", CUENTA_DEFAULT)
    if cuenta not in CUENTAS_VALIDAS:
        cuenta = CUENTA_DEFAULT

    extra_context = extra_context or {}
    extra_context["cuenta_actual"] = cuenta
    extra_context["cuentas"] = CUENTAS_VALIDAS
    extra_context.update(_calcular_saldos(cuenta))

    return _index_original(self, request, extra_context=extra_context)


AdminSite.index = _index_con_dashboard
