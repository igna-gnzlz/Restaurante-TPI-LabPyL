from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from accounts_app.forms import UserAdminRegisterForm, NotificationForm
from accounts_app.models import User, Notification, UserNotification
from django.contrib.auth.models import Group
from django.urls import reverse
from django.utils.html import format_html


class UserAdmin(BaseUserAdmin):
    add_form = UserAdminRegisterForm
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('name', 'last_name', 'username', 'email', 'password1', 'password2', 'role')}
        ),
    )

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if not change:
            group = form.cleaned_data.get("role")
            if group:
                obj.groups.add(group)

admin.site.register(User, UserAdmin)


class NotificationAdmin(admin.ModelAdmin):
    form = NotificationForm
    list_display = ('title', 'ver_destinatarios')  # Agregamos la columna

    def ver_destinatarios(self, obj):
        url = reverse('accounts_app:notification_recipients', kwargs={'pk': obj.id})
        return format_html('<a class="button" href="{}">Ver destinatarios</a>', url)

    ver_destinatarios.short_description = 'Destinatarios'

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        if change:
            UserNotification.objects.filter(notification=obj).delete()

        if form.cleaned_data.get('send_to_all'):
            try:
                clientes_group = Group.objects.get(name='Cliente')
                clientes = clientes_group.user_set.all()
            except Group.DoesNotExist:
                clientes = User.objects.none()
        else:
            clientes = form.cleaned_data.get('recipients')

        for cliente in clientes:
            UserNotification.objects.create(user=cliente, notification=obj)

admin.site.register(Notification, NotificationAdmin)