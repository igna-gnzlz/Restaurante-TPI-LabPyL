from django.views.generic import FormView, ListView, TemplateView
from django.views.generic.edit import UpdateView
from django.views import View
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import LoginView
from django.contrib.auth.models import User
from accounts_app.forms import UserRegisterForm, UserLoginForm, EditUsernameForm
from accounts_app.models import Notification, UserNotification
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404

from django.http import JsonResponse


class EditUsernameView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = EditUsernameForm
    template_name = 'accounts_app/edit_username.html'
    success_url = reverse_lazy('accounts_app:profile')

    def get_object(self, queryset=None):
        return self.request.user

class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'accounts_app/profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user'] = self.request.user
        return context


class UserRegisterView(FormView):
    template_name = 'accounts_app/register.html'
    form_class = UserRegisterForm
    success_url = reverse_lazy('accounts_app:login')  # o la url name que tengas para login

    def form_valid(self, form):
        form.save()  # Guarda el usuario usando tu método save()
        messages.success(self.request, "Usuario registrado correctamente. Ahora podés iniciar sesión.")
        return super().form_valid(form)


class UserLoginView(LoginView):
    template_name = 'accounts_app/login.html'
    authentication_form = UserLoginForm

    def form_valid(self, form):
        user = form.get_user()
        # Bloquea el login si el usuario está en grupos prohibidos
        if user.groups.filter(name__in=["Administrador", "Cajero"]).exists():
            form.add_error(None, "Credenciales inválidas. Verifica usuario y contraseña.")
            return self.form_invalid(form)  # Mostrar formulario con error
        return super().form_valid(form)


class UserNotificationsListView(LoginRequiredMixin, ListView):
    model = UserNotification
    template_name = 'accounts_app/user_notifications_list.html'
    context_object_name = 'user_notifications'

    def get_queryset(self):
        # Solo las notificaciones del usuario autenticado
        return UserNotification.objects.filter(user=self.request.user)

class DeleteNotificationView(LoginRequiredMixin, View):

    def post(self, request, pk, *args, **kwargs):
        notif = get_object_or_404(UserNotification, pk=pk, user=request.user)
        notif.delete()
        return JsonResponse({'status': 'success'})

class DeleteAllNotificationsView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        request.user.usernotification_set.all().delete()
        return JsonResponse({'status': 'success'})

class UserNotificationDetailView(LoginRequiredMixin, View):
    def get(self, request, pk, *args, **kwargs):
        notif = get_object_or_404(UserNotification, pk=pk, user=request.user)
        return JsonResponse({
            'title': notif.notification.title,
            'message': notif.notification.message,
        })


class MarkNotificationReadView(LoginRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        notif = get_object_or_404(UserNotification, pk=pk, user=request.user)
        notif.is_read = True
        notif.save(update_fields=['is_read'])
        return JsonResponse({'status': 'ok'})