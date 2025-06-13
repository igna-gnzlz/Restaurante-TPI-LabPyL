from django.db import models
from django.contrib.auth.models import AbstractUser
class User(AbstractUser):
    name = models.CharField(max_length=15, verbose_name="Nombre") #nombre
    last_name = models.CharField(max_length=15, verbose_name="Apellido") #apellido
    
    username = models.CharField(max_length=15, unique=True, verbose_name="Nombre de usuario") # Sobreescribe el de AbstractUser de "username"
    email = models.EmailField(verbose_name="Correo Electrónico")
    password = models.CharField(max_length=128, verbose_name="Contraseña")

    def __str__(self):
        return self.username

class UserNotification(models.Model):
    user = models.ForeignKey('User', on_delete=models.SET_NULL, null=True)
    notification = models.ForeignKey('Notification', on_delete=models.CASCADE)
    is_read = models.BooleanField(default=False)

class Notification(models.Model):
    title = models.CharField(max_length=100, verbose_name="Título")
    message = models.TextField(verbose_name="Mensaje")
    created_at = models.DateTimeField(auto_now_add=True)