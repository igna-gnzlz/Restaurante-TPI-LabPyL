from django import forms
from accounts_app.models import User, Notification
import re
from django.contrib.auth.models import Group
from django.contrib.auth.forms import AuthenticationForm


class UserLoginForm(AuthenticationForm):
    error_messages = {
        'invalid_login': "Credenciales inválidas. Verifica usuario y contraseña."
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Ingresa tu usuario'
        })
        self.fields['password'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Ingresa tu contraseña'
        })

        self.fields['username'].label = "Usuario"
        self.fields['password'].label = "Contraseña"


class UserValidationMixin:
    def clean_name(self):
        name = self.cleaned_data.get("name", "").strip()
        if " " in name:
            raise forms.ValidationError("Solo se permite un nombre, sin espacios.")
        if not re.fullmatch(r'^[A-Za-zÁÉÍÓÚáéíóúÑñ]+$', name):
            raise forms.ValidationError("El nombre solo puede contener letras.")
        max_length = self.fields['name'].max_length
        if len(name) > max_length:
            raise forms.ValidationError(f"El nombre no puede superar los {max_length} caracteres.")
        return name

    def clean_last_name(self):
        last_name = self.cleaned_data.get("last_name", "").strip()
        if " " in last_name:
            raise forms.ValidationError("Solo se permite un apellido, sin espacios.")
        if not re.fullmatch(r'^[A-Za-zÁÉÍÓÚáéíóúÑñ]+$', last_name):
            raise forms.ValidationError("El apellido solo puede contener letras.")
        max_length = self.fields['last_name'].max_length
        if len(last_name) > max_length:
            raise forms.ValidationError(f"El apellido no puede superar los {max_length} caracteres.")
        return last_name

    def clean_username(self):
        username = self.cleaned_data.get("username", "").strip()
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Este nombre de usuario ya está registrado.")
        if not re.fullmatch(r'[A-Za-z0-9.]+', username):
            raise forms.ValidationError("El nombre de usuario solo puede contener letras, números, y puntos.")
        max_length = self.fields['username'].max_length
        if len(username) > max_length:
            raise forms.ValidationError(f"El nombre de usuario no puede superar los {max_length} caracteres.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get("email", "").strip()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Este correo electrónico ya está registrado.")
        patron = r'^[a-zA-Z0-9.]+@(gmail|hotmail)\.com$'
        if not re.match(patron, email):
            raise forms.ValidationError([
                "El correo electrónico debe ser de la forma ejemplo@(gmail|hotmail).com",
                'La parte de "ejemplo" solo puede contener letras, números, y puntos.'
            ])
        return email

    def clean_password_value(self, field_name):
        password = self.cleaned_data.get(field_name, "").strip()
        min_length = 8
        max_length = self.fields[field_name].max_length
        if len(password) < min_length:
            raise forms.ValidationError(f"La contraseña debe tener al menos {min_length} caracteres.")
        if len(password) > max_length:
            raise forms.ValidationError(f"La contraseña no puede superar los {max_length} caracteres.")
        return password

class UserRegisterForm(forms.ModelForm, UserValidationMixin):
    confirm_password = forms.CharField(
        label="Confirmar Contraseña",
        max_length=32,
        required=True,
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = User
        fields = ['name', 'last_name', 'username', 'email', 'password']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'password': forms.PasswordInput(attrs={'class': 'form-control'}),
        }

    def clean_password(self):
        return self.clean_password_value("password")

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm = cleaned_data.get("confirm_password")
        if password and confirm and password != confirm:
            self.add_error("confirm_password", "Las contraseñas no coinciden.")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
            # Asignar grupo Cliente
            cliente_group = Group.objects.get(name="Cliente")
            user.groups.add(cliente_group)
        return user


class UserAdminRegisterForm(forms.ModelForm, UserValidationMixin):
    password1 = forms.CharField(label="Contraseña", widget=forms.PasswordInput, max_length=32)
    password2 = forms.CharField(label="Confirmar Contraseña", widget=forms.PasswordInput, max_length=32)
    
    role = forms.ModelChoiceField(
        queryset=Group.objects.all(),
        label="Rol de Usuario",
        required=True,
        empty_label=None  # Esto elimina lo opcion vacia "------"
    )

    class Meta:
        model = User
        fields = ['name', 'last_name', 'username', 'email']
    
    # El Administrador solo puede crear usuarios "Administrador" o "Cajero"
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        allowed_roles = Group.objects.filter(name__in=["Administrador", "Cajero"])
        self.fields['role'].queryset = allowed_roles
        self.fields['role'].empty_label = None
    
    # El Administrador puede crear usuarios "Administrador" o "Cajero" o "Cliente"
    '''
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        cliente_group = Group.objects.filter(name="Cliente").first()
        # Si no existe, no pasa nada, no asigna valor por defecto
        if cliente_group:
            self.fields['role'].initial = cliente_group.id
    '''

    def clean_password1(self):
        return self.clean_password_value("password1")

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("password1") != cleaned_data.get("password2"):
            self.add_error("password2", "Las contraseñas no coinciden.")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
            # Asignar grupo según el rol seleccionado
            group = self.cleaned_data["role"]
            user.groups.add(group)
        return user


class NotificationForm(forms.ModelForm):
    recipients = forms.ModelMultipleChoiceField(
        queryset=User.objects.none(),  # lo seteoh en __init__
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Usuarios destinatarios (Clientes)"
    )
    send_to_all = forms.BooleanField(
        required=False,
        initial=False,
        label="Enviar a todos los clientes"
    )

    class Meta:
        model = Notification
        fields = ['title', 'message']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            clientes_group = Group.objects.get(name='Cliente')
            self.fields['recipients'].queryset = clientes_group.user_set.all()
        except Group.DoesNotExist:
            self.fields['recipients'].queryset = User.objects.none()

    def clean(self):
        cleaned_data = super().clean()
        title = cleaned_data.get('title')
        message = cleaned_data.get('message')
        recipients = cleaned_data.get('recipients')
        send_to_all = cleaned_data.get('send_to_all')

        if not title or title.strip() == '':
            self.add_error('title', 'El título no puede estar vacío.')

        if not message or message.strip() == '':
            self.add_error('message', 'El mensaje no puede estar vacío.')

        if not send_to_all and (not recipients or len(recipients) == 0):
            raise forms.ValidationError('Debe seleccionar al menos un destinatario o marcar "Enviar a todos".')

        return cleaned_data


class EditUsernameForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username']

    def clean_username(self):
        username = self.cleaned_data.get('username', '').strip()
        # Validación de caracteres permitidos
        if not re.fullmatch(r'[A-Za-z0-9.]+', username):
            raise forms.ValidationError("El nombre de usuario solo puede contener letras, números y puntos.")
        
        max_length = self.fields['username'].max_length
        if len(username) > max_length:
            raise forms.ValidationError(f"El nombre de usuario no puede superar los {max_length} caracteres.")

        # Permitir que el usuario mantenga su mismo username sin error
        # self.instance es el usuario actual
        if User.objects.filter(username=username).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Este nombre de usuario ya está registrado.")
        
        return username