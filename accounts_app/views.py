from django.views.generic import FormView
from django.urls import reverse_lazy
from django.contrib import messages
from accounts_app.forms import RegisterForm, LoginForm

from django.contrib.auth import authenticate, login


class RegisterView(FormView):
    template_name = 'accounts_app/register.html'
    form_class = RegisterForm
    success_url = reverse_lazy('accounts_app:login')  # va hacia el login

    def form_valid(self, form):
        form.save()  # Guarda el usuario usando tu método save()
        messages.success(self.request, "Usuario registrado correctamente. Ahora podés iniciar sesión.")
        return super().form_valid(form)

class LoginView(FormView):
    template_name = 'accounts_app/login.html'  # tu template login.html
    form_class = LoginForm
    success_url = reverse_lazy('home')  

    def form_valid(self, form):
        username = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password')

        user = authenticate(self.request, username=username, password=password)
        if user is not None:
            login(self.request, user)
            messages.success(self.request, f"Bienvenido, {username}!")
            return super().form_valid(form)
        else:
            # Esto no debería pasar si tu formulario valida bien, 
            # pero por si acaso devolvemos error.
            form.add_error(None, "Credenciales inválidas.")
            return self.form_invalid(form)