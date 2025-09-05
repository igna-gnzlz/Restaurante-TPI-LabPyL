from bookings_app.utils import DateTimeUtils

from django.db import models
from django.db.models import Q, Count

class BookingQuerySet(models.QuerySet):
    def del_usuario(self, user):
        return self.filter(user=user)

    def aprobadas(self):
        return self.filter(approved=True, approval_date__isnull=False)

    def pendientes(self):
        return self.filter(approved=True, approval_date__isnull=True)
    
    def rechazadas(self):
        return self.filter(approved=False)

    def sin_confirmar(self):
        hoy = DateTimeUtils.get_local_date()
        ahora = DateTimeUtils.get_local_time()
        return self.filter(approval_date__isnull=True).filter(
            Q(date__lt=hoy) | Q(date=hoy, time_slot__start_time__lt=ahora)
        )

    def futuras(self):
        hoy = DateTimeUtils.get_local_date()
        ahora = DateTimeUtils.get_local_time()
        return self.aprobadas().filter(
            Q(date__gt=hoy) | Q(date=hoy, time_slot__start_time__gt=ahora)
        )

    def proxima(self):
        hoy = DateTimeUtils.get_local_date()
        ahora = DateTimeUtils.get_local_time()
        return self.aprobadas().filter(
            Q(date__gt=hoy) |
            Q(date=hoy, time_slot__end_time__gte=ahora)
        ).order_by('date', 'time_slot__start_time')

    def historial_aprobadas(self):
        hoy = DateTimeUtils.get_local_date()
        ahora = DateTimeUtils.get_local_time()
        return self.aprobadas().filter(
            Q(date__lt=hoy) |
            Q(date=hoy, time_slot__end_time__lt=ahora)
        ).order_by('-date', '-time_slot__start_time')

    def con_cantidad_pedidos(self):
        return self.annotate(cantidad_pedidos=Count('orders'))
    
    # Para la vista MakeReservationView

    def pendientes_por_usuario(self, user):
        return self.del_usuario(user).pendientes()


class BookingManager(models.Manager):
    def get_queryset(self):
        return BookingQuerySet(self.model, using=self._db)

    def del_usuario(self, user):
        return self.get_queryset().del_usuario(user)

    def aprobadas(self):
        return self.get_queryset().aprobadas()

    def pendientes(self):
        return self.get_queryset().pendientes()

    def rechazadas(self):
        return self.get_queryset().rechazadas()

    def sin_confirmar(self):
        return self.get_queryset().sin_confirmar()

    def futuras(self):
        return self.get_queryset().futuras()

    def proxima(self, base_qs=None):
        qs = base_qs if base_qs is not None else self.get_queryset()
        return qs.proxima().first()

    def historial_aprobadas(self):
        return self.get_queryset().historial_aprobadas()

    def con_cantidad_pedidos(self):
        return self.get_queryset().con_cantidad_pedidos()
    
    def pendientes_por_usuario(self, user):
        return self.get_queryset().pendientes_por_usuario(user)


class TimeSlotQuerySet(models.QuerySet):
    def disponibles_para_fecha(self, fecha):
        qs = self.all()
        if fecha == DateTimeUtils.get_local_date():
            ahora = DateTimeUtils.get_local_time()
            qs = qs.filter(start_time__gt=ahora)
        return qs


class TimeSlotManager(models.Manager):
    def get_queryset(self):
        return TimeSlotQuerySet(self.model, using=self._db)

    def disponibles_para_fecha(self, fecha):
        return self.get_queryset().disponibles_para_fecha(fecha)


class TableQuerySet(models.QuerySet):
    def disponibles_para_fecha_y_timeslot(self, fecha, time_slot_id):
        if time_slot_id is None:
            return self.none()
        else:
            from bookings_app.models import Booking  # import adentro para evitar circularidad
            
            mesas_reservadas_ids = Booking.objects.filter(
                date=fecha,
                time_slot_id=time_slot_id,
                approved=True
            ).values_list('tables__id', flat=True)

            return self.filter(
                timeslot__id=time_slot_id
            ).exclude(
                id__in=mesas_reservadas_ids
            ).distinct()
        


class TableManager(models.Manager):
    def get_queryset(self):
        return TableQuerySet(self.model, using=self._db)

    def disponibles_para_fecha_y_timeslot(self, fecha, time_slot_id):
        if time_slot_id is None:
            return self.none()
        else:
            from bookings_app.models import Booking
            mesas_reservadas_ids = Booking.objects.filter(
                date=fecha,
                time_slot_id=time_slot_id,
                approved=True
            ).values_list('tables__id', flat=True)

            return self.exclude(id__in=mesas_reservadas_ids).distinct()
