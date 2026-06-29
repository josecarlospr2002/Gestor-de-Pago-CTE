document.addEventListener("DOMContentLoaded", function() {
    var tipoSelect = document.getElementById("id_tipo_ingreso");
    var debitarCheck = document.getElementById("id_debitar");
    var fechaDebitoInput = document.getElementById("id_fecha_debito");

    function actualizarDebito() {
        if (tipoSelect && debitarCheck && fechaDebitoInput) {
            if (tipoSelect.value === "Transferencia") {
                debitarCheck.parentElement.style.display = "";
                fechaDebitoInput.parentElement.style.display = "";
                if (debitarCheck.checked && !fechaDebitoInput.value) {
                    var today = new Date().toISOString().split('T')[0];
                    fechaDebitoInput.value = today;
                }
            } else {
                debitarCheck.parentElement.style.display = "none";
                debitarCheck.checked = false;
                fechaDebitoInput.value = "";
            }
        }
    }

    if (tipoSelect) {
        tipoSelect.addEventListener("change", actualizarDebito);
    }

    if (debitarCheck) {
        debitarCheck.addEventListener("change", function() {
            if (this.checked && !fechaDebitoInput.value) {
                var today = new Date().toISOString().split('T')[0];
                fechaDebitoInput.value = today;
            } else if (!this.checked) {
                fechaDebitoInput.value = "";
            }
        });
    }

    actualizarDebito();
});