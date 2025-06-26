from django import forms
from bookings_app.models import Table, TimeSlot, Booking
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.utils import timezone
from django.utils.timezone import now


class TableAdminForm(forms.ModelForm):
    CAPACITY_CHOICES = [
        (1, '1'),
        (2, '2'),
        (4, '4'),
        (6, '6'),
        (8, '8'),
    ]
    capacity = forms.ChoiceField(choices=CAPACITY_CHOICES)

    class Meta:
        model = Table
        fields = ['number', 'capacity', 'description']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['number'].disabled = True  # Deshabilitado para que no se pueda modificar
        self.fields['number'].required = False  # Para evitar validación porque se enviará por hidden
    
    def clean_number(self):
        # Retornamos el valor inicial para que se use el que esté en el formulario oculto
        return self.initial.get('number', self.instance.number)
    
    def as_p(self):
        """Renderizamos el campo number disabled + un hidden con el mismo valor"""
        # Esta parte es un truco para que en el renderizado el hidden se incluya.
        # Si usás un template custom, podés manejarlo mejor.
        return super().as_p() + f'<input type="hidden" name="number" value="{self.initial.get("number", "")}">'










class TimeSlotAdminForm(forms.ModelForm):
    tables = forms.ModelMultipleChoiceField(
        queryset=Table.objects.all(),
        required=False,
        widget=FilteredSelectMultiple('Mesas', is_stacked=False)
    )

    class Meta:
        model = TimeSlot
        fields = ['name', 'start_time', 'end_time', 'tables']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance.pk:
            local_now = timezone.localtime()
            hoy = local_now.date()
            hora_actual = local_now.time()

            # Filtrar mesas con reservas futuras
            mesas_con_reservas = self.instance.tables.filter(
                booking__approved=True
            ).filter(
                Q(booking__date__gt=hoy) |
                Q(booking__date=hoy, booking__time_slot__start_time__gt=hora_actual)
            ).distinct()

            # Guardar IDs de mesas con reservas futuras
            self.disabled_tables = list(mesas_con_reservas.values_list('id', flat=True))

            # Pasárselos al widget
            self.fields['tables'].widget.disabled_choices = self.disabled_tables
    
    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        nombre = cleaned_data.get('name')
        mesas_seleccionadas = cleaned_data.get('tables')

        if nombre:
            qs = TimeSlot.objects.filter(name=nombre)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError(f"Ya existe una franja horaria con el nombre '{nombre}'.")
        
        if start_time and end_time:
            if start_time >= end_time:
                raise ValidationError("La hora de inicio debe ser anterior a la hora de fin y no pueden ser iguales.")

            # Validar solapamiento de franjas
            qs = TimeSlot.objects.filter(
                start_time__lt=end_time,
                end_time__gt=start_time,
            )

            # Excluir la instancia actual si está editando
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)

            if qs.exists():
                nombres = ", ".join([f"'{ts.name}'" for ts in qs])
                raise ValidationError(f"El horario se superpone con las siguientes franjas: {nombres}.")
        
        # Nueva validación: al menos una mesa asignada
        if mesas_seleccionadas is None or not mesas_seleccionadas.exists():
            raise ValidationError("Debe asignar al menos una mesa a la franja horaria.")
    
        # Validación de desasignación de mesas con reservas futuras  
        if self.instance.pk and mesas_seleccionadas is not None:
                local_now = timezone.localtime()
                hoy = local_now.date()
                hora_actual = local_now.time()

                mesas_con_reservas = self.instance.tables.filter(
                    booking__approved=True
                ).filter(
                    Q(booking__date__gt=hoy) |
                    Q(booking__date=hoy, booking__time_slot__start_time__gt=hora_actual)
                ).distinct()

                mesas_asignadas_original = set(self.instance.tables.values_list('id', flat=True))
                mesas_actuales = set(mesas_seleccionadas.values_list('id', flat=True))
                desasignadas = mesas_asignadas_original - mesas_actuales

                conflictivas = mesas_con_reservas.filter(id__in=desasignadas)

                if conflictivas.exists():
                    nombres = ", ".join(f"Mesa {m.number}" for m in conflictivas)
                    raise ValidationError(
                        f"No se pueden desasignar las siguientes mesas porque tienen reservas futuras: {nombres}."
                    )

        return cleaned_data










class BookingAdminForm(forms.ModelForm):
    class Meta:
        model = Booking
        exclude = ['approved', 'approval_date', 'approved_by', 'time_slot', 'tables', 'user']  # Campos que no quiero mostrar

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Desactivo todos los campos restantes para solo lectura
        for field in self.fields.values():
            field.disabled = True










class MakeReservationForm(forms.Form):
    tables = forms.ModelMultipleChoiceField(
        queryset=Table.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=True,
        label="Mesas Disponibles"
    )

    observations = forms.CharField(
        label="Observaciones",
        required=False,
        widget=forms.Textarea(attrs={
            'placeholder': 'Opcional...',
            'rows': 3,
            'class': 'form-control'
        })
    )

    time_slot = forms.ModelChoiceField(
        queryset=TimeSlot.objects.all(),
        widget=forms.HiddenInput(),
        required=True
    )

    def __init__(self, *args, **kwargs):
        available_tables = kwargs.pop('available_tables', Table.objects.none())
        time_slot_queryset = kwargs.pop('time_slot_queryset', TimeSlot.objects.all())
        super().__init__(*args, **kwargs)

        self.fields['tables'].queryset = available_tables
        self.fields['time_slot'].queryset = time_slot_queryset
        self.fields['tables'].label_from_instance = self.get_table_label

    def get_table_label(self, table):
        return f"Mesa {table.number} | Capacidad: {table.capacity} | Descripción: {table.description}"
