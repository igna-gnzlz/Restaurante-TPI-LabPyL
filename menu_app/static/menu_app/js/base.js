// Config de los toasts
function toastRedirect(message, url, icon = "success") {
    Swal.fire({
        toast: true,
        position: "top-end",
        icon: icon,
        title: message,
        showCloseButton: true,
        showConfirmButton: false,
        timer: 3000,
        timerProgressBar: true,
        didOpen: (toast) => {
            // Cambiar el cursor para que se note clickable
            toast.style.cursor = "pointer";

            // Al hacer hover, pausar timer y darle efecto de clickable (scale + opacidad)
            toast.addEventListener("mouseenter", () => {
                Swal.stopTimer();
                if (icon == "success") {
                    toast.style.transform = "scale(0.95)";
                }

            });
            toast.addEventListener("mouseleave", () => {
                Swal.resumeTimer();
                toast.style.transform = "scale(1)";
            });

            // Click en el toast (excepto la X) redirige
            toast.addEventListener("click", (event) => {
                if (!event.target.closest('.swal2-close')) {
                    window.location.href = url;
                }
            });
        }
    });
}

function toastNoRedirect(message, icon = "warning") {
    Swal.fire({
        toast: true,
        position: "top-end",
        icon: icon,
        title: message,
        showCloseButton: true,
        showConfirmButton: false,
        timer: 3000,
        timerProgressBar: true,
        didOpen: (toast) => {
            toast.addEventListener('mouseenter', Swal.stopTimer)
            toast.addEventListener('mouseleave', Swal.resumeTimer)
        }
    });
}

// Meto los toasts en todos los botones en cualquier template "hijo"
document.addEventListener("DOMContentLoaded", function () {
    const btnsAddToOrder = document.querySelectorAll(".add-to-order-btn");
    const btnsDecFromCart = document.querySelectorAll(".dec-from-cart-btn");
    const btnsDeleteFromCart = document.querySelectorAll(".delete-from-cart-btn");

    btnsAddToOrder.forEach(button => {
        button.addEventListener("click", function () {
            const url = this.dataset.url;

            fetch(url, {
                method: "POST",
                headers: {
                    "X-CSRFToken": getCookie("csrftoken"),
                    "X-Requested-With": "XMLHttpRequest",
                },
                body: ""
            })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        toastRedirect(data.message, urls.makeOrder, "success");
                    } else {
                        if (data.message === "Seleccione primero una reserva.") {
                            toastRedirect(data.message, urls.makeOrder, "warning");
                            return;
                        }
                        toastNoRedirect(data.message, "error");
                    }
                })
                .catch(error => {
                    toastNoRedirect("Error al agregar producto", "error");
                    console.error("Error:", error);
                });
        });
    });

    btnsDecFromCart.forEach(button => {
        button.addEventListener("click", function () {
            const url = this.dataset.url;
            const productId = this.dataset.productId;

            fetch(url, {
                method: "POST",
                headers: {
                    "X-CSRFToken": getCookie("csrftoken"),
                    "Content-Type": "application/json"
                }
            })
                .then(res => res.json())
                .then(data => {
                    if (data.success) {
                        toastNoRedirect(data.message, "success");

                        if (data.cart_empty) {
                            // reemplazar todo el carrito por el aviso
                            document.querySelector("#cart-items").innerHTML = `
    <div class="alert alert-warning">Todavía no hay productos en el carrito.</div>
    `;
                            // Ocultar total y botón de confirmar
                            const cartTotal = document.querySelector("#cart-total");
                            if (cartTotal) {
                                cartTotal.closest("h4").remove();
                            }

                            const confirmBtn = document.getElementById("confirm-order-container");
                            if (confirmBtn) {
                                confirmBtn.remove();
                            }
                        } else {
                            if (!data.product_removed) {
                                // Actualizar cantidad del producto y subtotal
                                document.querySelector(`#cart-quant-prod-${productId}`).textContent = data.quantity;
                                document.querySelector(`#cart-subtotal-prod-${productId}`).textContent = `$${data.subtotal}`;
                            } else {
                                // Eliminar fila completa si quitó todo el producto
                                document.querySelector(`#row-product-${productId}`).remove();
                            }

                            // Actualizar total carrito
                            document.querySelector("#cart-total").textContent = data.total_cart;
                        }
                    }
                })
                .catch(err => console.error("Error al decrementar producto del carrito:", err));
        });
    });
});

// Helper CSRF
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
        const cookies = document.cookie.split(";");
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + "=")) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}