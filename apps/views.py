from django.contrib.admin.views.decorators import staff_member_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect
from django.contrib import messages
from decimal import Decimal, InvalidOperation
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from io import BytesIO
from .models import SolicitudesDePago

from .models import SaldoInicial

CUENTAS = ("CUP", "ANIR", "PRESUPUESTO")
CAMPOS = (
    ("saldo_empresa", "Saldo de Empresa"),
    ("saldo_empresa_calculado", "Saldo de Empresa Calculado"),
    ("saldo_banco", "Saldo de Banco"),
    ("transito", "Tránsito"),
    ("saldo_inversiones", "Saldo de Inversiones"),
    ("saldo_operaciones", "Saldo de Operaciones"),
)


@staff_member_required
def inicializar_saldos(request):
    if not request.user.is_superuser:
        raise PermissionDenied("Solo el superusuario puede inicializar los saldos.")

    actuales_por_cuenta = {}
    for cuenta in CUENTAS:
        try:
            si = SaldoInicial.objects.get(cuenta_de_empresa=cuenta)
            actuales_por_cuenta[cuenta] = {c: getattr(si, c) for c, _ in CAMPOS}
        except SaldoInicial.DoesNotExist:
            actuales_por_cuenta[cuenta] = {c: Decimal("0") for c, _ in CAMPOS}

    errores = {}

    if request.method == "POST":
        nuevos_valores = {}
        for cuenta in CUENTAS:
            nuevos_valores[cuenta] = {}
            for campo, _ in CAMPOS:
                clave = f"{cuenta}__{campo}"
                raw = request.POST.get(clave, "").strip().replace(",", ".")
                if raw == "":
                    raw = "0"
                try:
                    valor = Decimal(raw)
                    if valor < 0:
                        errores[clave] = "El valor no puede ser negativo."
                        valor = Decimal("0")
                except InvalidOperation:
                    errores[clave] = "Valor numérico inválido."
                    valor = Decimal("0")
                nuevos_valores[cuenta][campo] = valor

        if not errores:
            for cuenta in CUENTAS:
                SaldoInicial.objects.update_or_create(
                    cuenta_de_empresa=cuenta,
                    defaults=nuevos_valores[cuenta],
                )
            messages.success(request, "Saldos iniciales guardados correctamente.")
            return redirect("admin:index")

        actuales_por_cuenta = nuevos_valores

    bloques = []
    for cuenta in CUENTAS:
        filas = []
        for campo, etiqueta in CAMPOS:
            clave = f"{cuenta}__{campo}"
            filas.append({
                "clave": clave,
                "etiqueta": etiqueta,
                "valor": actuales_por_cuenta[cuenta][campo],
                "error": errores.get(clave),
            })
        bloques.append({"cuenta": cuenta, "filas": filas})

    context = {
        "bloques": bloques,
        "titulo": "Inicializar Saldos",
        "opts": {"app_label": "apps"},
        "has_permission": True,
    }
    return render(request, "admin/inicializar_saldos.html", context)


def generar_pdf_h90(request, pk):

    try:
        solicitud = SolicitudesDePago.objects.get(pk=pk)
    except SolicitudesDePago.DoesNotExist:
        return HttpResponse("Solicitud no encontrada", status=404)

    template = get_template('admin/h90_pdf.html')

    context = {
        'solicitud': solicitud,
    }
    html = template.render(context)

    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)

    if not pdf.err:
        response = HttpResponse(result.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="H90_{solicitud.numero_de_H90}.pdf"'
        return response

    return HttpResponse('Error al generar el PDF', status=500)