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
        # Sin confirmar: approval_date null, y para fechas PASADAS (menores o igual que hoy y con hora menor)
        return self.filter(approval_date__isnull=True).filter(
            Q(date__lt=hoy) | Q(date=hoy, time_slot__start_time__lt=ahora)
        )

    def futuras(self):
        local_now = timezone.localtime()
        hoy = local_now.date()
        ahora = local_now.time()
        # Futuras: aprobadas y confirmadas para hoy o futuro con start_time > ahora
        return self.aprobadas().filter(
            Q(date__gt=hoy) | Q(date=hoy, time_slot__start_time__gt=ahora)
        )

    def proxima(self):
        local_now = timezone.localtime()
        hoy = local_now.date()
        ahora = local_now.time()

        # Próxima reserva: aprobada y confirmada para hoy o futuro, con end_time >= ahora si es hoy
        return self.aprobadas().filter(
            Q(date__gt=hoy) |
            Q(date=hoy, time_slot__end_time__gte=ahora)
        ).order_by('date', 'time_slot__start_time').first()

    def actual(self):
        local_now = timezone.localtime()
        hoy = local_now.date()
        ahora = local_now.time()

        # Reserva actual: fecha es hoy y ahora entre start y end
        return self.aprobadas().filter(
            date=hoy,
            time_slot__start_time__lte=ahora,
            time_slot__end_time__gte=ahora
        ).first()

    def historial_aprobadas(self):
        local_now = timezone.localtime()
        hoy = local_now.date()
        ahora = local_now.time()
        # Historial aprobadas: fecha pasada o hoy con end_time < ahora
        return self.aprobadas().filter(
            Q(date__lt=hoy) |
            Q(date=hoy, time_slot__end_time__lt=ahora)
        ).order_by('-date', '-time_slot__start_time')

    def con_cantidad_pedidos(self):
        # Anotar queryset con cantidad de pedidos para evitar consultas N+1
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

    def proxima(self):
        return self.get_queryset().proxima()

    def actual(self):
        return self.get_queryset().actual()

    def historial_aprobadas(self):
        return self.get_queryset().historial_aprobadas()

    def con_cantidad_pedidos(self):
        return self.get_queryset().con_cantidad_pedidos()
