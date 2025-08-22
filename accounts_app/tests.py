from django.test import TestCase
from accounts_app.models import User, Notification, UserNotification
from django.db.utils import IntegrityError
from django.utils import timezone
from django.urls import reverse
from django.contrib.messages import get_messages
from django.utils.translation import activate
from django.contrib.auth.models import Group

activate('es')




#TESTEOS DE MODELOS


class UserModelTests(TestCase):

    def test_creacion_user(self):
        # Creación de instancia User
        user = User.objects.create_user(
            username='usuario1',
            email='usuario1@example.com',
            password='password123',
            name='Juan',
            last_name='Perez'
        )
        self.assertEqual(user.username, 'usuario1')
        self.assertEqual(user.email, 'usuario1@example.com')
        self.assertEqual(user.name, 'Juan')
        self.assertEqual(user.last_name, 'Perez')
        
    def test_lectura_user(self):
        # Guardar y recuperar usuario
        User.objects.create_user(username='usuario2', email='u2@example.com', password='pass', name='Ana', last_name='Lopez')
        user = User.objects.get(username='usuario2')
        self.assertEqual(user.email, 'u2@example.com')
    
    def test_actualizacion_user(self):
        # Cambiar datos y guardar
        user = User.objects.create_user(username='usuario3', email='u3@example.com', password='pass', name='Luis', last_name='Diaz')
        user.name = 'Luis Updated'
        user.save()
        user_refreshed = User.objects.get(username='usuario3')
        self.assertEqual(user_refreshed.name, 'Luis Updated')
    
    def test_eliminacion_user(self):
        # Borrar instancia
        user = User.objects.create_user(username='usuario4', email='u4@example.com', password='pass', name='Maria', last_name='Gomez')
        user.delete()
        with self.assertRaises(User.DoesNotExist):
            User.objects.get(username='usuario4')
    
    def test_str_method_user(self):
        # __str__ debe devolver username
        user = User.objects.create_user(username='usuario5', email='u5@example.com', password='pass', name='Pedro', last_name='Alvarez')
        self.assertEqual(str(user), 'usuario5')
    
    def test_relaciones_user(self):
        # Aquí tu modelo User no tiene relaciones directas, se puede dejar pendiente para modelos relacionados
        self.assertTrue(True)  # Placeholder para futuros tests de relaciones
    
    def test_validacion_unique_username(self):
        # El campo username debe ser único, se verifica que no permita duplicados
        User.objects.create_user(username='usuario6', email='u6@example.com', password='pass', name='Laura', last_name='Sanchez')
        with self.assertRaises(IntegrityError):
            User.objects.create_user(username='usuario6', email='otro@example.com', password='pass', name='Otro', last_name='User')
    
    def test_validacion_campos_obligatorios(self):
        # Intentar crear usuario sin username genera error
        with self.assertRaises(ValueError):
            User.objects.create_user(username='', email='sinuser@example.com', password='pass', name='Sin', last_name='Usuario')


class NotificationModelTests(TestCase):

    def test_creacion_notification(self):
        notif = Notification.objects.create(title='Nueva Notificación', message='Detalle del mensaje')
        self.assertEqual(notif.title, 'Nueva Notificación')
        self.assertEqual(notif.message, 'Detalle del mensaje')

    def test_lectura_notification(self):
        Notification.objects.create(title='Leer Notificación', message='Mensaje para leer')
        notif = Notification.objects.get(title='Leer Notificación')
        self.assertEqual(notif.message, 'Mensaje para leer')

    def test_actualizacion_notification(self):
        notif = Notification.objects.create(title='Actualizar', message='Mensaje antiguo')
        notif.message = 'Mensaje actualizado'
        notif.save()
        notif_refreshed = Notification.objects.get(id=notif.id)
        self.assertEqual(notif_refreshed.message, 'Mensaje actualizado')

    def test_eliminacion_notification(self):
        notif = Notification.objects.create(title='Eliminar', message='Mensaje a eliminar')
        notif_id = notif.id
        notif.delete()
        with self.assertRaises(Notification.DoesNotExist):
            Notification.objects.get(id=notif_id)

    def test_created_at_auto_now_add(self):
        notif = Notification.objects.create(title='Fecha', message='Test fecha')
        now = timezone.now()
        self.assertLessEqual(notif.created_at, now)
        self.assertIsNotNone(notif.created_at)



class UserNotificationModelTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='user_test',
            email='user@test.com',
            password='testpass',
            name='Test',
            last_name='User'
        )
        self.notification = Notification.objects.create(
            title='Test Notification',
            message='This is a test notification'
        )

    def test_creacion_usernotification(self):
        un = UserNotification.objects.create(user=self.user, notification=self.notification)
        self.assertEqual(un.user, self.user)
        self.assertEqual(un.notification, self.notification)
        self.assertFalse(un.is_read)  # Valor por defecto False

    def test_relaciones_usernotification(self):
        un = UserNotification.objects.create(user=self.user, notification=self.notification)
        self.assertEqual(un.user.username, 'user_test')
        self.assertEqual(un.notification.title, 'Test Notification')

    def test_actualizacion_is_read(self):
        un = UserNotification.objects.create(user=self.user, notification=self.notification)
        un.is_read = True
        un.save()
        updated_un = UserNotification.objects.get(id=un.id)
        self.assertTrue(updated_un.is_read)

    def test_eliminacion_usernotification(self):
        un = UserNotification.objects.create(user=self.user, notification=self.notification)
        un_id = un.id
        un.delete()
        with self.assertRaises(UserNotification.DoesNotExist):
            UserNotification.objects.get(id=un_id)

    def test_user_null(self):
        un = UserNotification.objects.create(user=None, notification=self.notification)
        self.assertIsNone(un.user)

    def test_borrado_notification_cascada(self):
        un = UserNotification.objects.create(user=self.user, notification=self.notification)
        self.notification.delete()
        with self.assertRaises(UserNotification.DoesNotExist):
            UserNotification.objects.get(id=un.id)

    def test_borrado_user_set_null(self):
        un = UserNotification.objects.create(user=self.user, notification=self.notification)
        self.user.delete()
        un_after_user_delete = UserNotification.objects.get(id=un.id)
        self.assertIsNone(un_after_user_delete.user)




#TESTEOS DE VISTAS


class UserRegisterViewTests(TestCase):
    def setUp(self):
        Group.objects.create(name="Cliente")

    def test_get_register_view(self):
        url = reverse('accounts_app:register')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts_app/register.html')
        self.assertIn('form', response.context)

    def test_post_register_valid(self):
        Group.objects.get_or_create(name="Cliente")  # asegura que existe
        url = reverse('accounts_app:register')
        data = {
            'username': 'usuario.1',  # Solo letras, números, puntos
            'email': 'usuario1@gmail.com',  # Formato válido y dominio aceptado
            'password': 'ClaveSegura123',  # Campo obligatorio
            'confirm_password': 'ClaveSegura123',  # Debe coincidir con password
            'name': 'Juan',
            'last_name': 'Perez',
        }
        response = self.client.post(url, data)
        if response.context is not None:
            print(response.context['form'].errors) # Se imprime solo si hay contexto
        # Debe redirigir tras registro exitoso
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('accounts_app:login'))
        # Verificar que el usuario fue creado
        user_exists = User.objects.filter(username='usuario.1').exists()
        self.assertTrue(user_exists)
        # Verificar mensaje de éxito
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("Usuario registrado correctamente" in str(m) for m in messages))


    def test_post_register_invalid(self):
        url = reverse('accounts_app:register')
        data = {
            'username': '',  # Campo username obligatorio vacío
            'email': 'correo@ejemplo.com',
            'password1': 'ClaveSegura123',
            'password2': 'ClaveSegura123',
            'name': 'Nombre',
            'last_name': 'Apellido'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertFormError(form, 'username', 'Este campo es obligatorio.')


class EditUsernameViewTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='usuario_set', password='pass')
        self.client.login(username='usuario_set', password='pass')

    def test_get_edit_username_view(self):
        url = reverse('accounts_app:edit_username')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts_app/edit_username.html')
        self.assertIn('form', response.context)

    def test_post_edit_username_valid(self):
        url = reverse('accounts_app:edit_username')
        data = {'username': 'nuevo.username'}  # Cambiado guion bajo por punto para pasar la validación
        response = self.client.post(url, data)
        if response.context is not None:
            print(response.context['form'].errors)
        self.assertRedirects(response, reverse('accounts_app:profile'))
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, 'nuevo.username')

    def test_post_edit_username_invalid(self):
        url = reverse('accounts_app:edit_username')
        data = {'username': ''}  # username obligatorio
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertFormError(form, 'username', ['Este campo es obligatorio.'])


class UserNotificationDeleteAllViewTests(TestCase):

    def setUp(self):
        # Crear usuarios
        self.user = User.objects.create_user(username='user1', password='pass')
        self.other_user = User.objects.create_user(username='other', password='pass')

        # Crear notificaciones
        notification1 = Notification.objects.create(title="Notificación 1", message="Mensaje 1")
        notification2 = Notification.objects.create(title="Notificación 2", message="Mensaje 2")
        notification3 = Notification.objects.create(title="Notificación 3", message="Mensaje 3")

        # Asociar notificaciones a usuarios
        UserNotification.objects.create(user=self.user, notification=notification1)
        UserNotification.objects.create(user=self.user, notification=notification2)
        UserNotification.objects.create(user=self.other_user, notification=notification3)

        # Loguear usuario para hacer requests autenticados
        self.client.login(username='user1', password='pass')

    def test_post_deletes_only_user_notifications_and_redirects(self):
        url = reverse('accounts_app:user_notification_delete_all')
        response = self.client.post(url)
        self.assertRedirects(response, reverse('accounts_app:user_notifications_list'))
        # Verificar que las notificaciones del usuario actual fueron eliminadas
        self.assertFalse(UserNotification.objects.filter(user=self.user).exists())
        # Las notificaciones de otros usuarios no deben eliminarse
        self.assertTrue(UserNotification.objects.filter(user=self.other_user).exists())

    def test_redirect_if_not_logged_in(self):
        self.client.logout()
        url = reverse('accounts_app:user_notification_delete_all')
        response = self.client.post(url)
        # Debe redirigir a login u otra URL (código distinto a 200)
        self.assertNotEqual(response.status_code, 200)


class UserNotificationDeleteViewTests(TestCase):

    def setUp(self):
        # Crear usuarios
        self.user = User.objects.create_user(username='user1', password='pass')
        self.other_user = User.objects.create_user(username='other', password='pass')

        # Crear notificaciones
        notification = Notification.objects.create(title="Notificación para borrar", message="Mensaje")

        # Crear UserNotification asociado al usuario
        self.user_notification = UserNotification.objects.create(user=self.user, notification=notification)

        # Loguear usuario para requests autenticados
        self.client.login(username='user1', password='pass')

    def test_get_confirmation_page(self):
        url = reverse('accounts_app:user_notification_delete', args=[self.user_notification.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts_app/user_notification_confirm_delete.html')
        # Opcional: verificar contenido relevante en la página
        self.assertContains(response, "Notificación para borrar")

    def test_post_deletes_notification_and_redirects(self):
        url = reverse('accounts_app:user_notification_delete', args=[self.user_notification.pk])
        response = self.client.post(url)
        self.assertRedirects(response, reverse('accounts_app:user_notifications_list'))
        self.assertFalse(UserNotification.objects.filter(pk=self.user_notification.pk).exists())

    def test_redirect_if_not_logged_in(self):
        self.client.logout()
        url = reverse('accounts_app:user_notification_delete', args=[self.user_notification.pk])
        response = self.client.get(url)
        self.assertNotEqual(response.status_code, 200)  # Debería redirigir a login u otra página

