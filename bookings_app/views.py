from bookings_app.models import Booking, TimeSlot, Table
from bookings_app.mixins import ClienteRequiredMixin
from bookings_app.utils import DateTimeUtils
from bookings_app.helpers import BookingHelpers
from menu_app.models import Order, OrderContainsProduct, OrderContainsCombo
from bookings_app.forms import MakeReservationForm

from django.contrib.auth.mixins import LoginRequiredMixin
from django.template.loader import render_to_string
from django.views.generic import ListView, FormView, DetailView
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.contrib import messages
from django.views import View


class BookingListView(LoginRequiredMixin, ClienteRequiredMixin, ListView):
    model = Booking
    template_name = 'bookings_app/my_reservation.html'
    context_object_name = 'bookings'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        reservas_usuario = Booking.objects.del_usuario(user).select_related('time_slot')

        proxima_reserva = Booking.objects.proxima(base_qs=reservas_usuario)
        
        hoy = DateTimeUtils.get_local_date()
        ahora = DateTimeUtils.get_local_time()
        
        if proxima_reserva:
            card_title = proxima_reserva.get_card_title(hoy, ahora)
        else:
            card_title = "Próxima Reserva"

        reservas_futuras = reservas_usuario.futuras()

        if proxima_reserva:
            reservas_futuras = reservas_futuras.exclude(id=proxima_reserva.id)

        reservas_pendientes = reservas_usuario.pendientes()
        reservas_historial_aprobadas = reservas_usuario.historial_aprobadas()
        reservas_historial_rechazadas = reservas_usuario.rechazadas()
        reservas_sin_confirmar = reservas_usuario.sin_confirmar()

        # Anotar cantidad de pedidos
        reservas_futuras = reservas_futuras.con_cantidad_pedidos()
        reservas_historial_aprobadas = reservas_historial_aprobadas.con_cantidad_pedidos()

        cantidad_pedidos_proxima_reserva = proxima_reserva.get_cantidad_pedidos() if proxima_reserva else 0

        context.update({
            'proxima_reserva': proxima_reserva,
            'card_title': card_title,
            'reservas_futuras': reservas_futuras,
            'reservas_pendientes': reservas_pendientes,
            'reservas_historial_aprobadas': reservas_historial_aprobadas,
            'reservas_historial_rechazadas': reservas_historial_rechazadas,
            'reservas_sin_confirmar': reservas_sin_confirmar,
            'cantidad_pedidos_proxima_reserva': cantidad_pedidos_proxima_reserva,
        })
        
        return context

    def get_queryset(self):
        return Booking.objects.del_usuario(self.request.user)


class GetNextReservationView(LoginRequiredMixin, ClienteRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        reservas_usuario = Booking.objects.del_usuario(request.user).aprobadas()
        proxima_reserva = Booking.objects.proxima(base_qs=reservas_usuario)

        cantidad_pedidos = proxima_reserva.get_cantidad_pedidos() if proxima_reserva else 0
        es_reserva_actual = proxima_reserva.es_reserva_actual if proxima_reserva else False

        card_html = render_to_string('bookings_app/includes/get_next_reservation_card.html', {
            'proxima_reserva': proxima_reserva,
            'cantidad_pedidos_proxima_reserva': cantidad_pedidos,
            'es_reserva_actual': es_reserva_actual
        }, request=request)

        return JsonResponse({'card_html': card_html})


class GetFutureReservationsView(LoginRequiredMixin, ClienteRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        reservas_usuario = Booking.objects.del_usuario(request.user).aprobadas()
        proxima_reserva = Booking.objects.proxima(reservas_usuario)
        reservas_futuras = reservas_usuario.futuras()

        if proxima_reserva:
            reservas_futuras = reservas_futuras.exclude(id=proxima_reserva.id)
        
        reservas_futuras = reservas_futuras.con_cantidad_pedidos()

        card_html = render_to_string(
            'bookings_app/includes/get_future_reservations_card.html',
            {'reservas_futuras': reservas_futuras},
            request=request
        )

        return JsonResponse({'card_html': card_html})



class GetPendingReservationsView(LoginRequiredMixin, ClienteRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        reservas_pendientes = Booking.objects.del_usuario(request.user).pendientes()

        card_html = render_to_string('bookings_app/includes/get_pending_reservations_card.html', {
            'reservas_pendientes': reservas_pendientes
        }, request=request)

        return JsonResponse({'card_html': card_html})


class GetHistoryAprobadasView(LoginRequiredMixin, ClienteRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        reservas_aprobadas = Booking.objects.del_usuario(request.user).historial_aprobadas().con_cantidad_pedidos()

        card_html = render_to_string('bookings_app/includes/get_history_reservations_aprobadas_card.html', {
            'reservas_historial_aprobadas': reservas_aprobadas
        }, request=request)

        return JsonResponse({'card_html': card_html})


class GetHistoryRechazadasView(LoginRequiredMixin, ClienteRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        reservas_rechazadas = Booking.objects.del_usuario(request.user).rechazadas()

        card_html = render_to_string('bookings_app/includes/get_history_reservations_rechazadas_card.html', {
            'reservas_historial_rechazadas': reservas_rechazadas
        }, request=request)

        return JsonResponse({'card_html': card_html})


class DeleteBookingView(ClienteRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        booking_id = kwargs.get('pk')
        booking = get_object_or_404(Booking, id=booking_id, user=request.user)
        booking.delete()
        return JsonResponse({'success': True})


class ReservationOrdersView(LoginRequiredMixin, DetailView):
    model = Booking
    template_name = 'bookings_app/reservation_orders.html'
    context_object_name = 'reserva'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        reserva = self.get_object()

        pedidos = Order.objects.filter(booking=reserva).order_by('buyDate')

        # Enlazar productos
        for pedido in pedidos:
            pedido.items = OrderContainsProduct.objects.filter(order=pedido).select_related('product')
            pedido.combos = OrderContainsCombo.objects.filter(order=pedido).select_related('combo')
        context['pedidos'] = pedidos
        return context
    

class CancelOrderView(LoginRequiredMixin, View):
    def post(self, request, pk):
        order = get_object_or_404(Order, pk=pk, user=request.user)

        if order.state != 'S':
            #messages.error(request, 'Solo se pueden cancelar pedidos en estado "Solicitado".')
            return redirect('bookings_app:reservation_orders', order.booking.pk)

        order.state = 'C'
        order.save()
        #messages.success(request, f'El pedido {order.code} fue cancelado correctamente.')
        return redirect('bookings_app:reservation_orders', order.booking.pk)


class DeleteOrderView(View):
    def post(self, request, pk):
        order = get_object_or_404(Order, pk=pk, user=request.user)

        if order.state == 'S':
            #messages.error(request, 'Los pedidos en estado "Solicitado" no pueden ser eliminados. Cancelalos primero.')
            return redirect('bookings_app:reservation_orders', order.booking.pk)

        booking_pk = order.booking.pk
        order.delete()

        #messages.success(request, f'El pedido fue eliminado correctamente.')
        return redirect('bookings_app:reservation_orders', booking_pk)


class MakeReservationView(LoginRequiredMixin, ClienteRequiredMixin, FormView):
    template_name = "bookings_app/make_reservation.html"
    form_class = MakeReservationForm
    success_url = reverse_lazy("bookings_app:my_reservation")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()

        selected_date = BookingHelpers.get_selected_date_from_request(self.request)
        time_slots = TimeSlot.objects.disponibles_para_fecha(selected_date)

        selected_time_slot = BookingHelpers.get_selected_timeslot_from_request(self.request, time_slots)

        available_tables = Table.objects.disponibles_para_fecha_y_timeslot(
            selected_date, 
            selected_time_slot.id if selected_time_slot else None
        )

        kwargs.update({
            'available_tables': available_tables,
            'time_slot_queryset': time_slots,
            'initial': {'time_slot': selected_time_slot.id if selected_time_slot else None}
        })

        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        today = DateTimeUtils.get_local_datetime()
        selected_date = BookingHelpers.get_selected_date_from_request(self.request)
        time_slots = TimeSlot.objects.disponibles_para_fecha(selected_date)
        selected_time_slot = BookingHelpers.get_selected_timeslot_from_request(self.request, time_slots)

        months = BookingHelpers.get_available_months(today)
        weekdays = BookingHelpers.get_weekdays()
        month_days = BookingHelpers.get_month_calendar(today.year, selected_date.month)

        available_tables = self.get_form().fields['tables'].queryset

        availability_title, availability_subtitle, show_tables = BookingHelpers.get_availability_status(
            selected_date, time_slots, available_tables
        )

        reservas_usuario = Booking.objects.del_usuario(self.request.user).aprobadas()
        proxima_reserva = Booking.objects.proxima(base_qs=reservas_usuario)
        es_reserva_actual = proxima_reserva.es_reserva_actual if proxima_reserva else False

        context.update({
            "months": months,
            "weekdays": weekdays,
            "month_days": month_days,
            "time_slots": time_slots,
            "selected_time_slot": selected_time_slot,
            "current_month": selected_date.month,
            "current_day": selected_date.day,
            "today": today,
            "availability_title": availability_title,
            "availability_subtitle": availability_subtitle,
            "show_tables": show_tables,
            "proxima_reserva": proxima_reserva,
            "es_reserva_actual": es_reserva_actual,
        })

        return context

    def form_valid(self, form):
        # Verifico que no tenga reservas pendientes
        if Booking.objects.del_usuario(self.request.user).pendientes().exists():
            messages.error(self.request, "Operación Denegada: Tiene una reserva pendiente.")
            return self.form_invalid(form)
        
        # Obtengo los datos seleccionados
        selected_date = BookingHelpers.get_selected_date_from_request(self.request)
        mesas_seleccionadas = form.cleaned_data["tables"]
        time_slot = form.cleaned_data["time_slot"]
        # Genero código único para reserva
        new_code = BookingHelpers.generar_codigo_reserva()

        # Creo la reserva y le asigno sus mesas
        reserva = Booking.objects.create(
            approved=True,
            approval_date=None,
            code=new_code,
            observations=form.cleaned_data.get("observations", ""),
            date=selected_date,
            time_slot=time_slot,
            user=self.request.user
        )
        reserva.tables.set(mesas_seleccionadas)
        
        messages.success(self.request, f"Reserva solicitada con éxito. Código: {new_code}")
        return super().form_valid(form)
