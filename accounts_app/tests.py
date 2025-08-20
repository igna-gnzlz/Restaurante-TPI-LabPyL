from django.test import TestCase
from accounts_app.models import User, Notification, UserNotification
from django.db.utils import IntegrityError
from django.utils import timezone

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
