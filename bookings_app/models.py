from django.db import models
from django.conf import settings  # <--- Importante

class Booking(models.Model):
    approved = models.BooleanField(default=False)
    approval_date = models.DateField(null=True, blank=True)
    code = models.CharField(max_length=15, unique=True)
    observations = models.TextField(blank=True)
    date = models.DateField()
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)  # <--- Cambiado aquí

    def __str__(self):
        return 'Booking code: '+self.code

    # ... (resto igual)

class Table(models.Model):
    capacity = models.IntegerField()
    number = models.IntegerField(default=0)
    description = models.TextField(blank=True)
    is_reserved = models.BooleanField(default=False)
    booking = models.ForeignKey('Booking', models.SET_NULL, null=True)

    def __str__(self):
        return 'Table '+str(self.number)  # <--- str(self.number) para evitar error si number es int

class TableHasTimeSlot(models.Model):
    table = models.ForeignKey('Table', on_delete=models.SET_NULL, null=True)
    time_slot = models.ForeignKey('TimeSlot', on_delete=models.CASCADE)

class TimeSlot(models.Model):
    start = models.DateTimeField()
    end = models.DateTimeField()
    is_full = models.BooleanField(default=False)

