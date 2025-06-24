from django.contrib import admin, messages
from bookings_app.models import Table, TimeSlot, Booking
from bookings_app.forms import TableAdminForm, TimeSlotAdminForm, BookingAdminForm
from django.utils import timezone
from django.http import HttpResponseRedirect
from django.db.models import Q
from django.urls import reverse
from django.utils.html import format_html
from django.shortcuts import redirect


# --- TableAdmin: numerado automático ---

class TableAdmin(admin.ModelAdmin):
    form = TableAdminForm
    actions = ['eliminar_mesas_controladas']

    def get_actions(self, request):
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions
    
    def eliminar_mesas_controladas(self, request, queryset):
        local_now = timezone.localtime()
        hoy = local_now.date()
        hora_actual = local_now.time()
        bloqueadas = []
        permitidas_ids = []

        for mesa in queryset:
            reservas_activas = Booking.objects.filter(
                approved=True,
                tables=mesa,
            ).filter(
                Q(date__gt=hoy) | Q(date=hoy, time_slot__start_time__gt=hora_actual)
            )

            if reservas_activas.exists():
                bloqueadas.append(mesa.number)
            else:
                permitidas_ids.append(mesa.id)

        if bloqueadas:
            messages.error(
                request,
                f"No se pudieron eliminar las mesas: {', '.join(str(n) for n in bloqueadas)} porque están asignadas a reservas activas."
            )

        if permitidas_ids:
            count = Table.objects.filter(id__in=permitidas_ids).delete()[0]
            messages.success(
                request,
                f"Se eliminaron correctamente {count} mesa(s) sin reservas activas."
            )

    eliminar_mesas_controladas.short_description = "Eliminar mesas seleccionadas (con control de reservas)"


    def get_changeform_initial_data(self, request):
        existing_numbers = set(Table.objects.values_list('number', flat=True))
        max_number = max(existing_numbers) if existing_numbers else 0

        for num in range(1, max_number + 1):
            if num not in existing_numbers:
                next_number = num
                break
        else:
            next_number = max_number + 1

        return {'number': next_number}
    
    def change_view(self, request, object_id, form_url='', extra_context=None):
        obj = self.get_object(request, object_id)
        local_now = timezone.localtime()
        hoy = local_now.date()
        hora_actual = local_now.time()

        reservas_activas = Booking.objects.filter(
            approved=True,
            tables=obj,
        ).filter(
            Q(date__gt=hoy) | Q(date=hoy, time_slot__start_time__gt=hora_actual)
        )

        if reservas_activas.exists():
            messages.error(
                request,
                f"No se puede eliminar la mesa {obj.number}. Está asignada a reservas activas (códigos: {', '.join(r.code for r in reservas_activas)})."
            )
            # Guardar esa info en extra_context para deshabilitar el botón Delete
            if extra_context is None:
                extra_context = {}
            extra_context['show_delete'] = False  # esto lo usa el template admin/change_form.html

        return super().change_view(request, object_id, form_url, extra_context)

    def save_model(self, request, obj, form, change):
        if not change:
            existing_numbers = set(Table.objects.values_list('number', flat=True))
            max_number = max(existing_numbers) if existing_numbers else 0

            for num in range(1, max_number + 1):
                if num not in existing_numbers:
                    obj.number = num
                    break
            else:
                obj.number = max_number + 1

        local_now = timezone.localtime()
        hoy = local_now.date()
        hora_actual = local_now.time()

        if change:
            reservas_activas = Booking.objects.filter(
                approved=True,
                tables=obj,
            ).filter(
                Q(date__gt=hoy) | Q(date=hoy, time_slot__start_time__gt=hora_actual)
            )

            if reservas_activas.exists():
                capacidad_vieja = Table.objects.get(pk=obj.pk).capacity
                capacidad_nueva = form.cleaned_data['capacity']

                if capacidad_vieja != int(capacidad_nueva):
                    form.add_error(
                        'capacity',
                        f'No se puede cambiar la capacidad de una mesa asignada a reservas activas (códigos: {", ".join(r.code for r in reservas_activas)}).'
                    )
                    return  # no guardamos

        super().save_model(request, obj, form, change)

    def has_delete_permission(self, request, obj=None):
        if not request.user.groups.filter(name='Administrador').exists():
            return False

        return super().has_delete_permission(request, obj)

    def delete_model(self, request, obj):
        local_now = timezone.localtime()
        hoy = local_now.date()
        hora_actual = local_now.time()
        reservas_activas = Booking.objects.filter(
            approved=True,
            tables=obj,
        ).filter(
            Q(date__gt=hoy) | Q(date=hoy, time_slot__start_time__gt=hora_actual)
        )

        if reservas_activas.exists():
            messages.error(
                request,
                f"No se puede eliminar la mesa {obj.number}. Está asignada a reservas activas (códigos: {', '.join(r.code for r in reservas_activas)})."
            )
            return HttpResponseRedirect(
                reverse(f'admin:bookings_app_table_change', args=[obj.pk])
            )

        super().delete_model(request, obj)
    
    def delete_queryset(self, request, queryset):
        hoy = timezone.localtime().date()
        bloqueadas = []
        permitidas_ids = []

        for mesa in queryset:
            reservas_activas = Booking.objects.filter(
                approved=True,
                tables=mesa,
                date__gte=hoy
            )

            if reservas_activas.exists():
                bloqueadas.append(mesa.number)
            else:
                permitidas_ids.append(mesa.id)

        if bloqueadas:
            messages.error(
                request,
                f"No se pudieron eliminar las mesas: {', '.join(str(n) for n in bloqueadas)} porque están asignadas a reservas activas."
            )

        if permitidas_ids:
            count = Table.objects.filter(id__in=permitidas_ids).delete()[0]
            messages.success(
                request,
                f"Se eliminaron correctamente {count} mesa(s) sin reservas activas."
            )

admin.site.register(Table, TableAdmin)










# --- TimeSlotAdmin con formulario custom ---
class TimeSlotAdmin(admin.ModelAdmin):
    form = TimeSlotAdminForm
    actions = None

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = []
        campos_controlados = ['name', 'start_time', 'end_time']

        if request.user.groups.filter(name='Cajero').exists():
            return campos_controlados

        if request.user.groups.filter(name='Administrador').exists() and obj is not None:
            local_now = timezone.localtime()
            hoy = local_now.date()
            hora_actual = local_now.time()

            reservas_futuras = obj.tables.filter(
                booking__approved=True,
                booking__time_slot=obj
            ).filter(
                Q(booking__date__gt=hoy) |
                Q(booking__date=hoy, booking__time_slot__start_time__gt=hora_actual)
            ).exists()

            if reservas_futuras:
                return campos_controlados

        return readonly_fields

    def change_view(self, request, object_id, form_url='', extra_context=None):
        obj = self.get_object(request, object_id)

        if obj is not None:
            local_now = timezone.localtime()
            hoy = local_now.date()
            hora_actual = local_now.time()

            # Filtrar mesas con reservas futuras
            mesas_con_reservas = obj.tables.filter(
                booking__approved=True,
                booking__time_slot=obj  # Esto filtra solo reservas en la franja actual
            ).filter(
                Q(booking__date__gt=hoy) |
                Q(booking__date=hoy, booking__time_slot__start_time__gt=hora_actual)
            ).distinct()

            if mesas_con_reservas.exists():
                nombres_mesas = ", ".join(f"Mesa {mesa.number}" for mesa in mesas_con_reservas)

                # Mensaje por bloqueo de name/start_time/end_time
                # Solo Administrador ve este mensaje
                if request.user.groups.filter(name='Administrador').exists():
                    self.message_user(
                        request,
                        f"Los campos 'name', 'start_time' y 'end_time' están bloqueados porque las siguientes mesas tienen reservas futuras: {nombres_mesas}.",
                        level=messages.WARNING
                    )

                # Mensaje por bloqueo de desasignación de mesas
                # Cajero y Administrador ven este mensaje
                if request.user.groups.filter(name__in=['Administrador', 'Cajero']).exists():
                    self.message_user(
                        request,
                        f"No se pueden desasignar las siguientes mesas porque tienen reservas futuras: {nombres_mesas}.",
                        level=messages.WARNING
                    )

                # Mensaje explicativo de por qué no podrá eliminarse
                # Solo Administrador ve este mensaje extra si querés dejarlo
                if request.user.groups.filter(name='Administrador').exists():
                    self.message_user(
                        request,
                        f"No se podrá eliminar esta franja horaria porque tiene reservas futuras para las mesas: {nombres_mesas}.",
                        level=messages.WARNING
                    )

        return super().change_view(request, object_id, form_url, extra_context)
    
    def delete_model(self, request, obj):
        local_now = timezone.localtime()
        hoy = local_now.date()
        hora_actual = local_now.time()

        reservas_futuras = obj.tables.filter(
            booking__approved=True,
            booking__time_slot=obj
        ).filter(
            Q(booking__date__gt=hoy) |
            Q(booking__date=hoy, booking__time_slot__start_time__gt=hora_actual)
        ).exists()

        if reservas_futuras:
            self.message_user(
                request,
                "No se puede eliminar esta franja horaria porque tiene reservas futuras.",
                level=messages.ERROR
            )
            return

        super().delete_model(request, obj)

    def has_delete_permission(self, request, obj=None):
        if not obj:
            return super().has_delete_permission(request, obj)

        # Solo Administrador puede eliminar
        if not request.user.groups.filter(name='Administrador').exists():
            return False

        local_now = timezone.localtime()
        hoy = local_now.date()
        hora_actual = local_now.time()

        # Verificar si hay reservas futuras en esta franja horaria
        reservas_futuras = obj.tables.filter(
            booking__approved=True,
            booking__time_slot=obj
        ).filter(
            Q(booking__date__gt=hoy) |
            Q(booking__date=hoy, booking__time_slot__start_time__gt=hora_actual)
        ).exists()

        # Solo permitir eliminar si NO hay reservas futuras
        return not reservas_futuras
    
admin.site.register(TimeSlot, TimeSlotAdmin)










class PendientesFilter(admin.SimpleListFilter):
    title = 'Reservas Pendientes'
    parameter_name = 'pendientes'

    def lookups(self, request, model_admin):
        return (('1', 'Mostrar'),)

    def queryset(self, request, queryset):
        if self.value() == '1':
            # Si hay cualquier otro filtro activo, no permite combinar
            if request.GET.get('aceptadas') == '1' or request.GET.get('rechazadas') == '1' or request.GET.get('pasadas') == '1':
                return queryset.none()
            return queryset.filter(approved=True, approval_date__isnull=True).order_by('date')
        return queryset


class AceptadasFilter(admin.SimpleListFilter):
    title = 'Reservas Aceptadas'
    parameter_name = 'aceptadas'

    def lookups(self, request, model_admin):
        return (('1', 'Mostrar'),)

    def queryset(self, request, queryset):
        if self.value() == '1':
            if request.GET.get('pendientes') == '1' or request.GET.get('rechazadas') == '1':
                return queryset.none()
            qs = queryset.filter(approved=True, approval_date__isnull=False)
            if request.GET.get('pasadas') == '1':
                local_now = timezone.localtime()
                qs = qs.filter(
                    Q(date__lt=local_now.date()) | Q(date=local_now.date(), time_slot__start_time__lt=local_now.time())
                )
            return qs.order_by('-date')
        return queryset


class RechazadasFilter(admin.SimpleListFilter):
    title = 'Reservas Rechazadas'
    parameter_name = 'rechazadas'

    def lookups(self, request, model_admin):
        return (('1', 'Mostrar'),)

    def queryset(self, request, queryset):
        if self.value() == '1':
            if request.GET.get('pendientes') == '1' or request.GET.get('aceptadas') == '1':
                return queryset.none()
            qs = queryset.filter(approved=False, approval_date__isnull=False)
            if request.GET.get('pasadas') == '1':
                local_now = timezone.localtime()
                qs = qs.filter(
                    Q(date__lt=local_now.date()) | Q(date=local_now.date(), time_slot__start_time__lt=local_now.time())
                )
            return qs.order_by('-date')
        return queryset


class PasadasFilter(admin.SimpleListFilter):
    title = 'Reservas Pasadas'
    parameter_name = 'pasadas'

    def lookups(self, request, model_admin):
        return (('1', 'Mostrar'),)

    def queryset(self, request, queryset):
        if self.value() == '1':
            if request.GET.get('pendientes') == '1':
                return queryset.none()
            local_now = timezone.localtime()
            # Solo aplico Pasadas sobre lo que ya esté filtrado por aceptadas o rechazadas, si corresponde
            if request.GET.get('aceptadas') == '1':
                return queryset.filter(
                    approved=True, approval_date__isnull=False
                ).filter(
                    Q(date__lt=local_now.date()) | Q(date=local_now.date(), time_slot__start_time__lt=local_now.time())
                ).order_by('-date')
            elif request.GET.get('rechazadas') == '1':
                return queryset.filter(
                    approved=False, approval_date__isnull=False
                ).filter(
                    Q(date__lt=local_now.date()) | Q(date=local_now.date(), time_slot__start_time__lt=local_now.time())
                ).order_by('-date')
            else:
                return queryset.filter(
                    Q(date__lt=local_now.date()) | Q(date=local_now.date(), time_slot__start_time__lt=local_now.time())
                ).order_by('-date')
        return queryset


class BookingAdmin(admin.ModelAdmin):
    form = BookingAdminForm
    list_filter = [PendientesFilter, AceptadasFilter, RechazadasFilter, PasadasFilter]
    actions = None
    ordering = ['-issue_date']
    change_form_template = 'admin/bookings_app/booking/change_form.html'
    readonly_fields = [
        'code', 'observations', 'date', 'issue_date',
        'time_slot_info', 'tables_info', 'user_info'
    ]
    
    class Media:
        css = {
            'all': ('bookings_app/css/admin_custom.css',)
        }
    
    def response_change(self, request, obj):
        if "_accept" in request.POST:
            obj.approval_date = timezone.now()
            obj.save()
            self.message_user(request, f"Reserva {obj.code} aceptada.")

            # Buscar siguiente reserva pendiente
            next_booking = Booking.objects.filter(
                approved=True,
                approval_date__isnull=True
            ).order_by('date').exclude(pk=obj.pk).first()

            if next_booking:
                return redirect(
                    reverse('admin:bookings_app_booking_change', args=[next_booking.pk])
                )

            return redirect("admin:bookings_app_booking_changelist")

        if "_reject" in request.POST:
            obj.approval_date = timezone.now()
            obj.approved = False
            obj.save()
            self.message_user(request, f"Reserva {obj.code} rechazada.", level="error")

            next_booking = Booking.objects.filter(
                approved=True,
                approval_date__isnull=True
            ).order_by('date').exclude(pk=obj.pk).first()

            if next_booking:
                return redirect(
                    reverse('admin:bookings_app_booking_change', args=[next_booking.pk])
                )

            return redirect("admin:bookings_app_booking_changelist")

        return super().response_change(request, obj)
    
    def change_view(self, request, object_id, form_url='', extra_context=None):
        if extra_context is None:
            extra_context = {}

        obj = self.get_object(request, object_id)
        mostrar_acciones = False
        if obj and obj.approved and obj.approval_date is None:
            mostrar_acciones = True

        extra_context['mostrar_acciones'] = mostrar_acciones

        # Construir URL changelist con los filtros activos
        changelist_base = reverse('admin:bookings_app_booking_changelist')
        filtros = request.GET.urlencode()
        if filtros:
            changelist_url = f"{changelist_base}?{filtros}"
        else:
            changelist_url = changelist_base

        extra_context['changelist_url'] = changelist_url

        # Contexto para el boton de eliminar
        extra_context['delete_url'] = reverse(
            'admin:bookings_app_booking_delete', args=[object_id]
        )

        return super().change_view(request, object_id, form_url, extra_context)
    
    def user_info(self, obj):
        return format_html(
            "<strong>Usuario:</strong> {}<br>"
            "<strong>Nombre:</strong> {}<br>"
            "<strong>Apellido:</strong> {}<br>"
            "<strong>Email:</strong> {}",
            obj.user.username,
            obj.user.name,
            obj.user.last_name,
            obj.user.email
        )
    
    user_info.short_description = "Información del Cliente"

    def time_slot_info(self, obj):
        return f"{obj.time_slot.name} ({obj.time_slot.start_time} - {obj.time_slot.end_time})"
    time_slot_info.short_description = "Franja Horaria"

    def tables_info(self, obj):
        return "\n".join(
            f"Mesa {t.number} — Capacidad: {t.capacity} — {t.description}"
            for t in obj.tables.all()
        )
    tables_info.short_description = "Mesas Reservadas"

    def has_delete_permission(self, request, obj=None):
        if request.user.groups.filter(name='Administrador').exists():
            return True
        if request.user.groups.filter(name='Cajero').exists():
            return False
        return False

admin.site.register(Booking, BookingAdmin)