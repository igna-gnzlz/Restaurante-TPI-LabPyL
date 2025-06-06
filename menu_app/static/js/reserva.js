document.getElementById('modalMiReserva').addEventListener('show.bs.modal', function () {
    const contenido = document.getElementById('contenidoMiReserva');
    contenido.innerHTML = 'Cargando...';

    fetch('/api/mi-reserva/')
        .then(response => {
            if (!response.ok) {
                throw new Error('Error en la respuesta del servidor');
            }
            return response.json();
        })
        .then(data => {
            if (data.error) {
                contenido.innerHTML = `<p>Error: ${data.error}</p>`;
            } else if (data.reserva) {
                const r = data.reserva;
                contenido.innerHTML = `
                    <div class="card">
                        <div class="card-body">
                            <h5 class="card-title">Reserva</h5>
                            <p><strong>Fecha:</strong> ${r.fecha}</p>
                            <p><strong>Hora:</strong> ${r.hora}</p>
                            <p><strong>Mesa:</strong> ${r.mesa}</p>
                            <p><strong>Estado:</strong> ${r.estado}</p>
                        </div>
                    </div>`;
            } else {
                contenido.innerHTML = `
                    <div class="card text-center text-danger">
                        <div class="card-body">
                            <h5 class="card-title">Sin reservas aún!</h5>
                            <i class="bi bi-x-circle" style="font-size: 3rem;"></i>
                        </div>
                    </div>`;
            }
        })
        .catch(error => {
            contenido.innerHTML = `<p>Error al cargar la reserva: ${error.message}</p>`;
        });
});
