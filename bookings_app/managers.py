from django.db import models
from django.utils import timezone
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
        local_now = timezone.localtime()
        hoy = local_now.date()
        ahora = local_now.time()
        return self.filter(approval_date__isnull=True).filter(
            Q(date__lt=hoy) | Q(date=hoy, time_slot__start_time__lt=ahora)
        )

    def futuras(self):
        local_now = timezone.localtime()
        hoy = local_now.date()
        ahora = local_now.time()
        return self.aprobadas().filter(
            Q(date__gt=hoy) | Q(date=hoy, time_slot__start_time__gt=ahora)
        )

    def proxima(self):
        local_now = timezone.localtime()
        hoy = local_now.date()
        ahora = local_now.time()
        return self.aprobadas().filter(
            Q(date__gt=hoy) |
            Q(date=hoy, time_slot__end_time__gte=ahora)
        ).order_by('date', 'time_slot__start_time').first()

    def historial_aprobadas(self):
        local_now = timezone.localtime()
        hoy = local_now.date()
        ahora = local_now.time()
        return self.aprobadas().filter(
            Q(date__lt=hoy) |
            Q(date=hoy, time_slot__end_time__lt=ahora)
        ).order_by('-date', '-time_slot__start_time')

    def con_cantidad_pedidos(self):
        return self.annotate(cantidad_pedidos=Count('orders'))


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
        local_now = timezone.localtime()
        hoy = local_now.date()
        ahora = local_now.time()

        qs = base_qs if base_qs is not None else self.get_queryset()

        return qs.aprobadas().filter(
            Q(date__gt=hoy) |
            Q(date=hoy, time_slot__end_time__gte=ahora)
        ).order_by('date', 'time_slot__start_time').first()

    def historial_aprobadas(self):
        return self.get_queryset().historial_aprobadas()

    def con_cantidad_pedidos(self):
        return self.get_queryset().con_cantidad_pedidos()
