



document.addEventListener("DOMContentLoaded", function () {
    const formaPago = document.getElementById("id_forma_de_pago");
    const h90 = document.getElementById("id_numero_de_H90");

    if (!formaPago || !h90) return;

    formaPago.addEventListener("change", function () {
        const forma = formaPago.value;

        if (!forma) {
            h90.value = "";
            return;
        }

        fetch(`get-next-h90/?forma=${encodeURIComponent(forma)}`)
            .then(response => response.json())
            .then(data => {
                h90.value = data.numero || "";
            })
            .catch(err => {
                console.error("Error obteniendo el próximo H90:", err);
            });
    });
});
