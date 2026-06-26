document.addEventListener("DOMContentLoaded", function() {
    var estadoSelect = document.getElementById("id_estado");
    var fechaFinalInput = document.getElementById("id_fecha_final");

    if (estadoSelect && fechaFinalInput) {
        estadoSelect.addEventListener("change", function() {
            if (this.value === "Debitado" || this.value === "Cancelado") {
                if (!fechaFinalInput.value) {
                    var today = new Date().toISOString().split('T')[0];
                    fechaFinalInput.value = today;
                }
            } else if (this.value === "Tránsito") {
                fechaFinalInput.value = "";
            }
        });
    }
});