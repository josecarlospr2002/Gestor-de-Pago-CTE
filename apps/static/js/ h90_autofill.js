document.addEventListener("DOMContentLoaded", function() {
  const provSelect = document.getElementById("id_identificador_del_proveedor");
  const nombreInput = document.getElementById("id_nombre_del_proveedor");
  const codigoInput = document.getElementById("id_codigo_del_proveedor");
  const cuentaInput = document.getElementById("id_cuenta_bancaria");
  const direccionInput = document.getElementById("id_direccion_proveedor");

  if (provSelect) {
    provSelect.addEventListener("change", function() {
      const pk = this.value;

      if (!pk) {
        if (nombreInput) nombreInput.value = "";
        if (codigoInput) codigoInput.value = "";
        if (cuentaInput) cuentaInput.value = "";
        if (direccionInput) direccionInput.value = "";
        return;
      }

      fetch(`/admin/apps/solicitudesdepago/get-proveedor/${pk}/`)
        .then(resp => resp.json())
        .then(data => {
          if (nombreInput) nombreInput.value = data.titular || "";
          if (codigoInput) codigoInput.value = data.codigo || "";
          if (cuentaInput) cuentaInput.value = data.cuenta_bancaria || "";
          if (direccionInput) direccionInput.value = data.direccion || "";
        })
        .catch(() => {
          console.error("Error al obtener datos del proveedor");
        });
    });
  }
});
