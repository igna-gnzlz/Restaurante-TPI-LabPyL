from django.views.generic import FormView, ListView, DetailView, TemplateView
from django.views.generic.edit import UpdateView, DeleteView
from django.views import View
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import LoginView
from django.contrib.auth.models import User
from accounts_app.forms import UserRegisterForm, UserLoginForm, EditUsernameForm
from accounts_app.models import Notification, UserNotification
from django.urls import reverse_lazy
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404, redirect


user = get_user_model()


class UserNotificationDeleteAllView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        UserNotification.objects.filter(user=request.user).delete()
        return redirect('accounts_app:user_notifications_list')

class UserNotificationDeleteView(DeleteView):
    model = UserNotification
    success_url = reverse_lazy('accounts_app:user_notifications_list')
    template_name = 'accounts_app/user_notification_confirm_delete.html'


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

# Si querés conservar la función profile, podés comentarla o eliminarla
# @login_required
# def profile(request):
#     user = request.user
#     return render(request, 'accounts_app/profile.html', {'user': user})


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


class NotificationRecipientsView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = UserNotification
    template_name = 'accounts_app/notification_recipients.html'
    context_object_name = 'user_notifications'

    def test_func(self):
        # Solo staff/admin puede acceder
        return self.request.user.is_staff

    def handle_no_permission(self):
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(self.request.get_full_path())

    def get_queryset(self):
        notification_id = self.kwargs.get('pk')  # Asumiendo que recibís pk en url
        notification = get_object_or_404(Notification, pk=notification_id)
        return UserNotification.objects.filter(notification=notification).select_related('user')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['notification'] = get_object_or_404(Notification, pk=self.kwargs.get('pk'))
        return context


class UserNotificationsListView(LoginRequiredMixin, ListView):
    model = UserNotification
    template_name = 'accounts_app/user_notifications_list.html'
    context_object_name = 'user_notifications'

    def get_queryset(self):
        # Solo las notificaciones del usuario autenticado
        return UserNotification.objects.filter(user=self.request.user)


class UserNotificationDetailView(LoginRequiredMixin, DetailView):
    model = UserNotification
    template_name = 'accounts_app/user_notification_detail.html'
    context_object_name = 'user_notification'

    def get_object(self, queryset=None):
        obj = get_object_or_404(UserNotification, pk=self.kwargs['pk'], user=self.request.user)
        if not obj.is_read:
            obj.is_read = True
            obj.save()
        return obj
