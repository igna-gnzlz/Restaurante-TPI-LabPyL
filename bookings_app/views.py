from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView
from django.utils import timezone
from .models import Booking
from menu_app.models import Order   # Importa el modelo Order si no lo tienes arriba

class BookingListView(LoginRequiredMixin, ListView):
    model = Booking
    template_name = 'bookings_app/my_reservation.html'
    context_object_name = 'bookings'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        hoy = timezone.now().date()
        # Reserva próxima: la más cercana en el futuro o hoy, no rechazada
        proxima_reserva = (
            Booking.objects
            .filter(user=self.request.user, date__gte=hoy)
            .exclude(approved=False)  # Excluye rechazadas
            .order_by('date')
            .first()
        )
        # Reservas pasadas: todas las reservas con fecha anterior a hoy
        reservas_pasadas = (
            Booking.objects
            .filter(user=self.request.user, date__lt=hoy)
            .order_by('-date')
        )
        context['proxima_reserva'] = proxima_reserva
        context['reservas_pasadas'] = reservas_pasadas
        return context

    def get_queryset(self):
        return Booking.objects.filter(user=self.request.user)
    

class UserOrdersHistoryView(LoginRequiredMixin, ListView):
    model = Order
    template_name = 'bookings_app/orders_history.html'
    context_object_name = 'orders'

    def get_queryset(self):
        # Ordena por fecha descendente (más reciente primero)
        return Order.objects.filter(user=self.request.user).order_by('-buyDate')