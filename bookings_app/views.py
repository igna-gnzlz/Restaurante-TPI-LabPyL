from django.contrib.auth.mixins import LoginRequiredMixin
from bookings_app.mixins import ClienteRequiredMixin
from django.views.generic import ListView, FormView
from bookings_app.models import Booking, TimeSlot, Table
from django.utils import timezone
from django.contrib import messages
from bookings_app.forms import MakeReservationForm
import calendar
from datetime import date
from django.db.models import Q
from django.urls import reverse_lazy
from django.utils.crypto import get_random_string
from django.shortcuts import redirect

from django.views import View
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string


class BookingListView(LoginRequiredMixin, ClienteRequiredMixin, ListView):
    model = Booking
    template_name = 'bookings_app/my_reservation.html'
    context_object_name = 'bookings'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        local_now = timezone.localtime()
        hoy = local_now.date()
        ahora = local_now.time()

        reservas_usuario = Booking.objects.filter(user=self.request.user).select_related('time_slot')

        # Próxima Reserva
        proxima_reserva = reservas_usuario.filter(
            approved=True,
            approval_date__isnull=False
        ).filter(
            Q(date__gt=hoy) |
            Q(date=hoy, time_slot__end_time__gte=ahora)
        ).order_by('date', 'time_slot__start_time').first()

        card_title = "Próxima Reserva"
        
        reservas_futuras = Booking.objects.none()  # vacío por defecto

        if proxima_reserva:
            if proxima_reserva.date == hoy and proxima_reserva.time_slot.start_time <= ahora <= proxima_reserva.time_slot.end_time:
                card_title = "Reserva Actual"
            # Reservas Futuras
            reservas_futuras = reservas_usuario.filter(
                approved=True,
                approval_date__isnull=False
            ).filter(
                Q(date__gt=hoy) |
                Q(date=hoy, time_slot__start_time__gt=ahora)
            )
            if proxima_reserva:
                reservas_futuras = reservas_futuras.exclude(id=proxima_reserva.id)
            reservas_futuras = reservas_futuras.order_by('date', 'time_slot__start_time')

        # Reservas Pendientes (aprobadas pero sin fecha de aprobación, y para hoy o futuro)
        reservas_pendientes = reservas_usuario.filter(
            approved=True,
            approval_date__isnull=True
        ).filter(
            Q(date__gt=hoy) |
            Q(date=hoy, time_slot__start_time__gte=ahora)
        ).order_by('date', 'time_slot__start_time')

        # Historial de Reservas Aprobadas
        reservas_historial_aprobadas = reservas_usuario.filter(
            approved=True,
            approval_date__isnull=False
        ).filter(
            Q(date__lt=hoy) |
            Q(date=hoy, time_slot__start_time__gt=ahora)
        ).order_by('-date', '-time_slot__start_time')

        # Historial de Reservas Rechazadas (approved=False)
        reservas_historial_rechazadas = reservas_usuario.filter(
            approved=False
        ).order_by('-date', '-time_slot__start_time')

        # Reservas Sin Confirmar (con approval_date NULL y para fechas PASADAS)
        reservas_sin_confirmar = reservas_usuario.filter(
            approval_date__isnull=True
        ).filter(
            Q(date__lt=hoy) |
            Q(date=hoy, time_slot__start_time__lt=ahora)
        ).order_by('-date', '-time_slot__start_time')

        context.update({
            'proxima_reserva': proxima_reserva,
            'card_title': card_title,
            'reservas_futuras': reservas_futuras,
            'reservas_pendientes': reservas_pendientes,
            'reservas_historial_aprobadas': reservas_historial_aprobadas,
            'reservas_historial_rechazadas': reservas_historial_rechazadas,
            'reservas_sin_confirmar': reservas_sin_confirmar
        })

        return context

    def get_queryset(self):
        # Reservas del usuario logueado (por compatibilidad con ListView, aunque no lo usamos ahora)
        return Booking.objects.filter(user=self.request.user)


class DeleteBookingView(ClienteRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        booking_id = kwargs.get('pk')
        booking = get_object_or_404(Booking, id=booking_id, user=request.user)
        booking.delete()
        return JsonResponse({'success': True})










class MakeReservationView(ClienteRequiredMixin, FormView):
    template_name = "bookings_app/make_reservation.html"
    form_class = MakeReservationForm
    success_url = reverse_lazy("bookings_app:my_reservation")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()

        # obtengo los el dia, mes, y año de bs.as que tienen los parametros GET
        selected_year = timezone.localtime().year
        selected_month = int(self.request.GET.get("month", timezone.localtime().month))
        selected_day = int(self.request.GET.get("day", timezone.localtime().day))
        
        # Por si estoy en un dia en un mes y cambio el mes, evaluo si este
        # "nuevo" mes tiene ese dia, sino lo tiene voy a su dia maximo
        max_day = calendar.monthrange(selected_year, selected_month)[1]
        if selected_day > max_day:
            selected_day = max_day
        
        # Creo mi objeto fecha
        selected_date = date(selected_year, selected_month, selected_day)

        # Obtengo todos los TimeSlots
        time_slots = TimeSlot.objects.all()

        # Si la reserva es para hoy, descarto las franjas horarias pasadas
        if selected_date == timezone.localtime().date():
            ahora = timezone.localtime().time()
            time_slots = time_slots.filter(start_time__gt=ahora)
        
        # Obtiene el time_slot desde GET
        raw_time_slot_id = self.request.GET.get("time_slot")
        try:
            time_slot_id = int(raw_time_slot_id)
        except (TypeError, ValueError):
            time_slot_id = None

        # Validar que time_slot_id exista y sea válido en time_slots
        if time_slot_id is None or not time_slots.filter(id=time_slot_id).exists():
            # Si no se eligió uno o no existe en los disponibles,
            # toma el primer horario disponible o None si no hay.
            first_slot = time_slots.first()
            time_slot_id = first_slot.id if first_slot else None
        
        # Obtiene las mesas disponibles
        available_tables = Table.objects.none()

        if time_slot_id is not None:
            # Si hay time_slot_id, busco las mesas
            # ya reservadas para esa fecha y horario.
            reserved_table_ids = Booking.objects.filter(
                date=selected_date,
                time_slot_id=time_slot_id,
                approved=True
            ).values_list('tables__id', flat=True)
            # Luego busco todas las mesas asociadas a ese horario
            # y las excluyo, y uso distinct por si una mesa esta
            # vinculada a varios TimeSlot
            available_tables = Table.objects.filter(
                timeslot__id=time_slot_id
            ).exclude(
                id__in=reserved_table_ids
            ).distinct()
        
        # Carga de variables extra en kwargs
        kwargs['available_tables'] = available_tables
        kwargs['time_slot_queryset'] = time_slots
        # Setea valor inicial para time_slot
        initial = kwargs.get('initial', {})
        initial['time_slot'] = time_slot_id
        kwargs['initial'] = initial

        return kwargs
    
    def get_context_data(self, **kwargs):
        # Obtengo el contexto actual
        context = super().get_context_data(**kwargs)
        # Obtengo la fecha y hora actual local
        today = timezone.localtime()
        # Obtengo el año y mes desde GET o usa valores actuales
        selected_year = today.year
        selected_month = int(self.request.GET.get("month", today.month))

        # Obtegno el  día desde GET o uso today.day (solo si es el mes actual)
        if "day" in self.request.GET:
            try:
                selected_day = int(self.request.GET.get("day"))
            except (TypeError, ValueError):
                selected_day = today.day
        else:
            selected_day = today.day if selected_month == today.month else 1

        # Validar que el día exista en el mes seleccionado
        max_day = calendar.monthrange(selected_year, selected_month)[1]
        if selected_day > max_day:
            selected_day = max_day
        
        # Creo el objeto date
        selected_date = date(selected_year, selected_month, selected_day)
        
        #  Obtengo todas las franjas horarias disponibles
        time_slots = TimeSlot.objects.all()
        
        # Si es hoy, descarto los horarios pasados
        if selected_date == today.date():
            ahora = today.time()
            time_slots = time_slots.filter(start_time__gt=ahora)
        
        # Obtengo el time_slot seleccionado desde GET
        selected_time_slot_id_raw = self.request.GET.get("time_slot")
        try:
            selected_time_slot_id = int(selected_time_slot_id_raw)
        except (TypeError, ValueError):
            selected_time_slot_id = None
        
        # Valido si el TimeSlot existe en los time_slots disponibles
        if selected_time_slot_id is None or not time_slots.filter(id=selected_time_slot_id).exists():
            first_slot = time_slots.first()
            selected_time_slot_id = first_slot.id if first_slot else None
        
        # Obtengo el objeto TimeSlot correspondiente
        selected_time_slot = (
            time_slots.filter(id=selected_time_slot_id).first()
            if selected_time_slot_id
            else None
        )

        # Creo el listado de meses desde el actual a diciembre
        all_months = [
            "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
            "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
        ]
        months = [
            {"numero": i, "nombre": all_months[i - 1]}
            for i in range(today.month, 13)
        ]

        # Defino los nombres de días de la semana
        weekdays = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]

        # Genera calendario del mes seleccionado (matriz de semanas y días)
        cal = calendar.Calendar(firstweekday=0)
        month_days = cal.monthdayscalendar(today.year, selected_month)

        # Obtengo mesas disponibles desde el formulario actual
        available_tables = self.get_form().fields['tables'].queryset

        # Detecto si hoy ya no hay más franjas horarias disponibles
        if selected_date == today.date() and not time_slots.exists():
            availability_title = "¡¡¡ NO SE PUEDEN HACER MAS RESERVAS POR HOY !!!"
            availability_subtitle = "La hora actual supera la última franja horaria disponible."
            show_tables = False
            
        elif available_tables.exists():
            availability_title = "Mesas Disponibles"
            availability_subtitle = ""
            show_tables = True
        else:
            availability_title = "FRANJA HORARIA COMPLETA."
            availability_subtitle = "Todas las mesas están reservadas."
            show_tables = False
        
        # Busco próxima reserva aprobada del usuario actual
        reservas_usuario = Booking.objects.filter(
            user=self.request.user,
            approved=True,
            approval_date__isnull=False
        )

        hoy = today.date()
        ahora = today.time()

        # Filtro la próxima reserva futura o a partir de ahora
        proxima_reserva = reservas_usuario.filter(
            Q(date__gt=hoy) | Q(date=hoy, time_slot__start_time__gte=ahora)
        ).order_by('date', 'time_slot__start_time').first()

        # Determina si está en curso ahora mismo
        es_reserva_actual = False
        if proxima_reserva:
            if proxima_reserva.date == hoy and proxima_reserva.time_slot.start_time <= ahora <= proxima_reserva.time_slot.end_time:
                es_reserva_actual = True
        
        # Actualizo el contexto con todas las variables
        context.update({
            "months": months,
            "weekdays": weekdays,
            "month_days": month_days,
            "time_slots": time_slots,
            "selected_time_slot": selected_time_slot,
            "current_month": selected_month,
            "current_day": selected_day,
            "today": today,
            "availability_title": availability_title,
            "availability_subtitle": availability_subtitle,
            "show_tables": show_tables,
            "proxima_reserva": proxima_reserva,
            "es_reserva_actual": es_reserva_actual,
        })

        return context

    def form_valid(self, form):
        try:
            reservas_pendientes = Booking.objects.filter(
                user=self.request.user,
                approved=True,
                approval_date__isnull=True
            )

            # No se puede hacer la reserva si hay una pediente
            if reservas_pendientes.exists():
                messages.error(
                    self.request,
                    "Operación Denegada: Tiene una reserva pendiente."
                )
                return redirect("bookings_app:my_reservation")

            now_local = timezone.localtime()
            selected_month = int(self.request.GET.get("month", now_local.month))
            selected_day = int(self.request.GET.get("day", now_local.day))
            
            max_day = calendar.monthrange(now_local.year, selected_month)[1]
            if selected_day > max_day:
                selected_day = max_day

            selected_date = date(
                year=now_local.year,
                month=selected_month,
                day=selected_day
            )

            time_slot = form.cleaned_data['time_slot']
            mesas_seleccionadas = form.cleaned_data["tables"]

            new_code = get_random_string(8).upper()

            booking = Booking.objects.create(
                approved=True,
                approval_date=None,
                code=new_code,
                observations=form.cleaned_data.get("observations", ""),
                date=selected_date,
                time_slot=time_slot,
                user=self.request.user
            )

            booking.tables.set(mesas_seleccionadas)

            messages.success(self.request, f"Reserva realizada con éxito. Código: {new_code}")
            return super().form_valid(form)

        except Exception as e:
            messages.error(self.request, f"Error al procesar la reserva: {str(e)}")
            return redirect("bookings_app:make_reservation")









class GetNextReservationView(LoginRequiredMixin, ClienteRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        local_now = timezone.localtime()
        hoy = local_now.date()
        ahora = local_now.time()

        reservas_usuario = Booking.objects.filter(
            user=request.user,
            approved=True,
            approval_date__isnull=False
        )

        proxima_reserva = reservas_usuario.filter(
            Q(date__gt=hoy) |
            Q(date=hoy, time_slot__end_time__gte=ahora)
        ).order_by('date', 'time_slot__start_time').first()

        es_reserva_actual = False
        if proxima_reserva:
            if proxima_reserva.date == hoy and proxima_reserva.time_slot.start_time <= ahora <= proxima_reserva.time_slot.end_time:
                es_reserva_actual = True
        
        card_html = render_to_string('bookings_app/includes/get_next_reservation_card.html', {
            'proxima_reserva': proxima_reserva,
            'es_reserva_actual': es_reserva_actual
        }, request=request)
        
        return JsonResponse({'card_html': card_html})


class GetFutureReservationsView(LoginRequiredMixin, ClienteRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        local_now = timezone.localtime()
        hoy = local_now.date()
        ahora = local_now.time()

        reservas_usuario = Booking.objects.filter(
            user=request.user,
            approved=True,
            approval_date__isnull=False
        )

        proxima_reserva = reservas_usuario.filter(
            Q(date__gt=hoy) | Q(date=hoy, time_slot__start_time__gte=ahora)
        ).order_by('date', 'time_slot__start_time').first()

        reservas_futuras = reservas_usuario.filter(
            Q(date__gt=hoy) | Q(date=hoy, time_slot__start_time__gte=ahora)
        )

        if proxima_reserva:
            reservas_futuras = reservas_futuras.exclude(id=proxima_reserva.id)

        reservas_futuras = reservas_futuras.order_by('date', 'time_slot__start_time')

        card_html = render_to_string('bookings_app/includes/get_future_reservations_card.html', {
            'reservas_futuras': reservas_futuras
        }, request=request)

        return JsonResponse({'card_html': card_html})


class GetPendingReservationsView(LoginRequiredMixin, ClienteRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        reservas_pendientes = Booking.objects.filter(
            user=request.user,
            approved=True,
            approval_date__isnull=True
        ).order_by('date', 'time_slot__start_time')

        card_html = render_to_string('bookings_app/includes/get_pending_reservations_card.html', {
            'reservas_pendientes': reservas_pendientes
        }, request=request)

        return JsonResponse({'card_html': card_html})


class GetHistoryAprobadasView(LoginRequiredMixin, ClienteRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        local_now = timezone.localtime()
        hoy = local_now.date()
        ahora = local_now.time()

        reservas_aprobadas = Booking.objects.filter(
            user=request.user,
            approved=True,
            approval_date__isnull=False
        ).filter(
            Q(date__lt=hoy) | Q(date=hoy, time_slot__end_time__lte=ahora)
        ).order_by('-date', '-time_slot__start_time')

        card_html = render_to_string('bookings_app/includes/get_history_reservations_aprobadas_card.html', {
            'reservas_historial_aprobadas': reservas_aprobadas
        }, request=request)

        return JsonResponse({'card_html': card_html})


class GetHistoryRechazadasView(LoginRequiredMixin, ClienteRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        reservas_rechazadas = Booking.objects.filter(
            user=request.user,
            approved=False
        ).order_by('-date', '-time_slot__start_time')

        card_html = render_to_string('bookings_app/includes/get_history_reservations_rechazadas_card.html', {
            'reservas_historial_rechazadas': reservas_rechazadas
        }, request=request)

        return JsonResponse({'card_html': card_html})
