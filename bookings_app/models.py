from django.db import models
from accounts_app.models import User

class Booking(models.Model):
    approved = models.BooleanField(default=False)
    approval_date = models.DateField(null=True, blank=True)
    code = models.CharField(max_length=15, unique=True)
    observations = models.TextField(blank=True)
    date = models.DateField()
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return 'Booking code: '+self.code
    
    @classmethod
    def validate(cls, code, date):
        errors = {}

        if code == "":
            errors["code"] = "Por favor ingrese un código"

        if date is None:
            errors["date"] = "Por favor ingrese una fecha"

        return errors
    
    @classmethod
    def new(cls, code, date, user, observations=None):
        errors = Booking.validate(code, date)

        if len(errors.keys()) > 0:
            return False, errors

        Booking.objects.create(
            code=code,
            date=date,
            user=user,
            observations=observations
        )

        return True, None
    
    def update(self, code=None, date=None, observations=None):
        self.code = code or self.code
        self.date = date or self.date
        self.observations = observations or self.observations

        self.save()

class Table(models.Model):
    capacity = models.IntegerField()
    number = models.IntegerField(default=0)
    description = models.TextField(blank=True)
    is_reserved = models.BooleanField(default=False)
    booking = models.ForeignKey('Booking', models.SET_NULL, null=True)

    def __str__(self):
        return 'Table '+self.number

class TableHasTimeSlot(models.Model):
    table = models.ForeignKey('Table', on_delete=models.SET_NULL, null=True)
    time_slot = models.ForeignKey('TimeSlot', on_delete=models.CASCADE)

class TimeSlot(models.Model):
    start = models.DateTimeField() # Consultar uso de tiempo en lugar de fecha, usar datetime?
    end = models.DateTimeField()
    is_full = models.BooleanField(default=False) # Para consultar

    #def __str__(self):
    #    return ''