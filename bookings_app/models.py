from django.db import models
from django.conf import settings 


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

    def __str__(self):
        return 'Codigo de Reserva: '+self.code


class Table(models.Model):
    capacity = models.IntegerField()
    number = models.IntegerField(unique=True) # le agrego unique=True para evitar conflictos
    description = models.TextField(blank=True, max_length=200)

    def save(self, *args, **kwargs):
        if not self.number:
            last_number = Table.objects.aggregate(models.Max('number'))['number__max'] or 0
            self.number = last_number + 1
        super().save(*args, **kwargs)

    def __str__(self):
        return 'Table '+str(self.number)  # <--- str(self.number) para evitar error si number es int


class TimeSlot(models.Model):
    name = models.CharField(max_length=20)
    start_time = models.TimeField()
    end_time = models.TimeField()
    tables = models.ManyToManyField(Table)

    def __str__(self):
        return self.name