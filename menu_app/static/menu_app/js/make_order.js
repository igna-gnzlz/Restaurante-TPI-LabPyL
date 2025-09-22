// Funcionalidad a todos los botones más
document.querySelectorAll(".wrapper .plus").forEach(plusBtn => {
    plusBtn.addEventListener("click", async () => {
        const wrapper = plusBtn.closest(".wrapper");
        const productId = wrapper.dataset.productId;
        const url = wrapper.dataset.incUrl;

        try {
            const response = await fetch(url, {
                method: "POST",
                headers: {
                    "X-CSRFToken": getCookie("csrftoken"),
                    "X-Requested-With": "XMLHttpRequest",
                },
            });

            const data = await response.json();

            if (data.success) {
                // Actualizo la cantidad y subtotal
                document.querySelector(`#cart-quant-prod-${productId}`).textContent = data.quantity;
                document.querySelector(`#cart-subtotal-prod-${productId}`).textContent = `$${data.subtotal}`;
                // Actualizo el monto del total carrito
                document.querySelector("#cart-total").textContent = `$${data.total_cart}`;

                toastNoRedirect(data.message, "success");
            } else {
                toastNoRedirect(data.message, "error");
            }

        } catch (error) {
            console.error("Error al actualizar carrito:", error);
            toastNoRedirect("Error inesperado", "error");
        }
    });
});