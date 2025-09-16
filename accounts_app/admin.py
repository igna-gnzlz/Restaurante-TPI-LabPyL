from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from accounts_app.forms import UserAdminRegisterForm, NotificationForm
from accounts_app.models import User, Notification, UserNotification
from django.contrib.auth.models import Group
from django.urls import reverse
from django.utils.html import format_html
from django.urls import path
from django.shortcuts import get_object_or_404, render


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
        url = reverse('admin:notification_recipients', kwargs={'pk': obj.id})
        return format_html('<a class="button" href="{}">Ver destinatarios</a>', url)

    ver_destinatarios.short_description = 'Destinatarios'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:pk>/recipients/',
                self.admin_site.admin_view(self.recipients_view),
                name='notification_recipients',
            ),
        ]
        return custom_urls + urls

    def recipients_view(self, request, pk):
        notification = get_object_or_404(Notification, pk=pk)
        user_notifications = UserNotification.objects.filter(notification=notification).select_related('user')

        context = dict(
            self.admin_site.each_context(request),
            notification=notification,
            user_notifications=user_notifications,
            opts=self.model._meta,
            title=f"Destinatarios de: {notification.title}",
        )
        return render(request, "admin/notification/recipients.html", context)

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