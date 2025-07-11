from django.db import models
from django.conf import settings
from django.utils import timezone

from bookings_app.managers import BookingManager, TimeSlotManager, TableManager
from bookings_app.utils import DateTimeUtils


class Booking(models.Model):
    approved = models.BooleanField(default=False)
    approval_date = models.DateField(null=True, blank=True)
    code = models.CharField(max_length=15, unique=True)
    observations = models.TextField(blank=True)
    date = models.DateField(null=True, blank=True)
    time_slot = models.ForeignKey('TimeSlot', on_delete=models.CASCADE)
    tables = models.ManyToManyField('Table')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE) # Usa el User definido en settings.py
    issue_date = models.DateField(auto_now_add=True)

    objects = BookingManager()

    def __str__(self):
        return 'Codigo de Reserva: '+self.code
    
    def get_cantidad_pedidos(self):
        # Si ya está anotado no hace consulta extra, sino consulta.
        if hasattr(self, 'cantidad_pedidos'):
            return self.cantidad_pedidos
        return self.orders.count()
    
    @property
    def es_reserva_actual(self):
        hoy = DateTimeUtils.get_local_date()
        ahora = DateTimeUtils.get_local_time()
        return self.date == hoy and self.time_slot.start_time <= ahora <= self.time_slot.end_time
    
    def get_card_title(self, fecha_actual, hora_actual):
        if self.date == fecha_actual and self.time_slot.start_time <= hora_actual <= self.time_slot.end_time:
            return "Reserva Actual"
        return "Próxima Reserva"
    
    def get_cantidad_pedidos(self):
        if hasattr(self, 'cantidad_pedidos'):
            return self.cantidad_pedidos
        return self.orders.count()

    def is_past_due(self):
        hoy = DateTimeUtils.get_local_date()
        ahora = DateTimeUtils.get_local_time()
        if self.date < hoy:
            return True
        if self.date == hoy and self.time_slot.end_time < ahora:
            return True
        return False


class Table(models.Model):
    capacity = models.IntegerField()
    number = models.IntegerField(unique=True) # le agrego unique=True para evitar conflictos
    description = models.TextField(blank=True, max_length=200)

    objects = TableManager()

    def __str__(self):
        return 'Table '+str(self.number)  # <--- str(self.number) para evitar error si number es int
    
    def save(self, *args, **kwargs):
        if not self.number:
            last_number = Table.objects.aggregate(models.Max('number'))['number__max'] or 0
            self.number = last_number + 1
        super().save(*args, **kwargs)
    
    def get_label(self):
        return f"Mesa {self.number} | Capacidad: {self.capacity} | Descripción: {self.description}"

    def is_available(self, time_slot, date):
        # Asumiendo que BookingManager tiene método para filtrar reservas aprobadas
        from bookings_app.models import Booking
        reservas = Booking.objects.filter(
            date=date,
            time_slot=time_slot,
            approved=True
        ).filter(tables=self)
        return not reservas.exists()


class TimeSlot(models.Model):
    name = models.CharField(max_length=20)
    start_time = models.TimeField()
    end_time = models.TimeField()
    tables = models.ManyToManyField(Table)

    objects = TimeSlotManager()

    def __str__(self):
        return self.name
    
    def is_future(self):
        ahora = timezone.localtime().time()
        return self.start_time > ahora

    def get_label(self):
        return f"{self.start_time.strftime('%H:%M')} - {self.end_time.strftime('%H:%M')}"