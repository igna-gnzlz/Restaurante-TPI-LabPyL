from django import forms
from django.contrib.auth import authenticate
from accounts_app.models import User
import re

class LoginForm(forms.Form):
    username = forms.CharField(
        label="Usuario",
        max_length=100,
        required=True,
        error_messages={
            'required': 'Debes ingresar tu nombre de usuario.'
        },
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Ingresa tu usuario"
        })
    )

    password = forms.CharField(
        label="Contraseña",
        max_length=100,
        required=True,
        error_messages={
            'required': 'Debes ingresar tu contraseña.'
        },
        widget=forms.PasswordInput(attrs={
            "class": "form-control",
            "placeholder": "Ingresa tu contraseña"
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get("username")
        password = cleaned_data.get("password")

        # Solo si ambos están presentes y válidos, se intenta autenticar
        if username and password:
            user = authenticate(username=username, password=password)
            print("DEBUG: usuario autenticado:", user)
            if not user:
                raise forms.ValidationError("Credenciales inválidas. Verifica usuario y contraseña.")

        return cleaned_data


class RegisterForm(forms.Form):
    name = forms.CharField(
        label="Nombre",
        max_length=15,
        required=True,
        error_messages={
            'required': 'El nombre es obligatorio.'
        },
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Ingresa tu nombre"
        })
    )
    last_name = forms.CharField(
        label="Apellido",
        max_length=15,
        required=True,
        error_messages={
            'required': 'El apellido es obligatorio.'
        },
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Ingresa tu apellido"
        })
    )
    username = forms.CharField(
        label="Nombre de Usuario",
        max_length=15,
        required=True,
        error_messages={
            'required': 'El nombre de usuario es obligatorio.'
        },
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Ingresa un nombre de usuario"
        })
    )
    email = forms.EmailField(
        label="Correo Electrónico",
        required=True,
        error_messages={
            'required': 'El correo electrónico es obligatorio.'
        },
        widget=forms.EmailInput(attrs={
            "class": "form-control",
            "placeholder": "Ingresa tu email"
        })
    )
    password = forms.CharField(
        label="Contraseña",
        max_length=32,
        required=True,
        error_messages={
            'required': 'La contraseña es obligatoria.'
        },
        widget=forms.PasswordInput(attrs={
            "class": "form-control",
            "placeholder": "Ingresa una contraseña"
        })
    )
    confirm_password = forms.CharField(
        label="Confirmar Contraseña",
        max_length=32,
        required=True,
        error_messages={
            'required': 'La confirmación de contraseña es obligatoria.'
        },
        widget=forms.PasswordInput(attrs={
            "class": "form-control",
            "placeholder": "Confirma tu contraseña"
        })
    )

    def clean_name(self):
        name = self.cleaned_data.get("name", "").strip()
        # Ya no hace falta validar si está vacío, porque el required y error_messages ya lo hacen
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
    
    def clean_password(self):
        password = self.cleaned_data.get("password", "").strip()
    
        min_length = 8
        if len(password) < min_length:
            raise forms.ValidationError(f"La contraseña debe tener al menos {min_length} caracteres.")
        
        max_length = self.fields['password'].max_length
        if len(password) > max_length:
            raise forms.ValidationError(f"La contraseña no puede superar los {max_length} caracteres.")

        return password
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', "Las contraseñas no coinciden.")

        return cleaned_data

    
    def save(self):
        data = self.cleaned_data
        user = User.objects.create(
            username=data["username"],
            email=data["email"],
            name=data["name"],
            last_name=data["last_name"]
        )
        user.set_password(data["password"])
        user.save()

        return user
