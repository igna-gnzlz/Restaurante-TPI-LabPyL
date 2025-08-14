from bookings_app.utils import DateTimeUtils
from bookings_app.models import Booking

import calendar
from datetime import date
from django.utils.crypto import get_random_string


class BookingHelpers:

    @staticmethod
    def get_selected_date_from_request(request):
        today = DateTimeUtils.get_local_datetime()
        year = today.year
        month = int(request.GET.get("month", today.month))
        day = int(request.GET.get("day", today.day))

        max_day = calendar.monthrange(year, month)[1]
        if day > max_day:
            day = max_day

        return date(year, month, day)

    @staticmethod
    def get_selected_timeslot_from_request(request, available_timeslots):
        try:
            time_slot_id = int(request.GET.get("time_slot"))
        except (TypeError, ValueError):
            time_slot_id = None

        if time_slot_id and available_timeslots.filter(id=time_slot_id).exists():
            return available_timeslots.get(id=time_slot_id)
        return available_timeslots.first()

    @staticmethod
    def get_available_months(today):
        nombres = [
            "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
            "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
        ]
        return [{"numero": i, "nombre": nombres[i - 1]} for i in range(today.month, 13)]

    @staticmethod
    def get_weekdays():
        return ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]

    @staticmethod
    def get_month_calendar(year, month):
        cal = calendar.Calendar(firstweekday=0)
        return cal.monthdayscalendar(year, month)

    @staticmethod
    def get_availability_status(selected_date, time_slots, available_tables):
        today = DateTimeUtils.get_local_date()

        if selected_date == today and not time_slots.exists():
            return (
                "¡¡¡ NO SE PUEDEN HACER MAS RESERVAS POR HOY !!!",
                "La hora actual supera la última franja horaria disponible.",
                False
            )

        if available_tables.exists():
            return ("Mesas Disponibles", "", True)

        return (
            "FRANJA HORARIA COMPLETA.",
            "Todas las mesas están reservadas.",
            False
        )

    @staticmethod
    def generar_codigo_reserva():
        while True:
            codigo = get_random_string(length=9, allowed_chars='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
            if not Booking.objects.filter(code=codigo).exists():
                return codigo