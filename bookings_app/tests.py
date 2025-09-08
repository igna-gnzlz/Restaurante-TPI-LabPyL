from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta, time
from bookings_app.models import Booking, TimeSlot, Table
from bookings_app.utils import DateTimeUtils
from bookings_app.helpers import BookingHelpers
from bookings_app.forms import TableAdminForm, TimeSlotAdminForm, MakeReservationForm
from django.urls import reverse
from unittest.mock import patch, MagicMock
from django.http import HttpRequest
from datetime import date, datetime
from django.utils.crypto import get_random_string
from django.contrib.auth.models import Group
from django.contrib.messages import get_messages


User = get_user_model()




# Testeos para los Managers

class BookingManagerTest(TestCase):

    def setUp(self):
        # Crear usuario de prueba
        self.user1 = User.objects.create_user(username="user1", password="pass")
        self.user2 = User.objects.create_user(username="user2", password="pass")

        # Crear TimeSlots para hoy y fechas relativas
        now = timezone.localtime()
        self.timeslot1 = TimeSlot.objects.create(
            name="Morning",
            start_time=(now - timedelta(hours=2)).time(),
            end_time=(now - timedelta(hours=1)).time()
        )
        self.timeslot2 = TimeSlot.objects.create(
            name="Afternoon",
            start_time=(now + timedelta(hours=1)).time(),
            end_time=(now + timedelta(hours=2)).time()
        )

        # Crear reservas con distintos estados y fechas
        today = DateTimeUtils.get_local_date()
        yesterday = today - timedelta(days=1)
        tomorrow = today + timedelta(days=1)

        # Reserva aprobada con approval_date (aprobadas)
        Booking.objects.create(
            user=self.user1, code="B1", approved=True, approval_date=today,
            date=today, time_slot=self.timeslot1, issue_date=today
        )
        # Reserva aprobada sin approval_date (pendientes)
        Booking.objects.create(
            user=self.user1, code="B2", approved=True, approval_date=None,
            date=yesterday, time_slot=self.timeslot1, issue_date=yesterday
        )
        # Reserva rechazada
        Booking.objects.create(
            user=self.user2, code="B3", approved=False, approval_date=None,
            date=tomorrow, time_slot=self.timeslot2, issue_date=today
        )

    def test_del_usuario(self):
        qs = Booking.objects.del_usuario(self.user1)
        self.assertTrue(all(b.user == self.user1 for b in qs))

    def test_aprobadas(self):
        qs = Booking.objects.aprobadas()
        self.assertTrue(all(b.approved and b.approval_date for b in qs))
        self.assertEqual(qs.count(), 1)  # Solo B1

    def test_pendientes(self):
        qs = Booking.objects.pendientes()
        self.assertTrue(all(b.approved and b.approval_date is None for b in qs))
        self.assertEqual(qs.count(), 1)  # Solo B2

    def test_rechazadas(self):
        qs = Booking.objects.rechazadas()
        self.assertTrue(all(not b.approved for b in qs))
        self.assertEqual(qs.count(), 1)  # Solo B3

    def test_sin_confirmar(self):
        qs = Booking.objects.sin_confirmar()
        for booking in qs:
            self.assertIsNone(booking.approval_date)
            self.assertTrue(
                booking.date < DateTimeUtils.get_local_date() or
                (booking.date == DateTimeUtils.get_local_date() and
                 booking.time_slot.start_time < DateTimeUtils.get_local_time())
            )

    def test_futuras(self):
        qs = Booking.objects.futuras()
        for booking in qs:
            self.assertTrue(booking.approved and booking.approval_date is not None)
            self.assertTrue(
                booking.date > DateTimeUtils.get_local_date() or
                (booking.date == DateTimeUtils.get_local_date() and
                 booking.time_slot.start_time > DateTimeUtils.get_local_time())
            )

    def test_proxima(self):
        proxima = Booking.objects.proxima()
        if proxima:
            self.assertTrue(proxima.approved and proxima.approval_date is not None)
            self.assertTrue(
                proxima.date > DateTimeUtils.get_local_date() or
                (proxima.date == DateTimeUtils.get_local_date() and
                 proxima.time_slot.end_time >= DateTimeUtils.get_local_time())
            )
        else:
            self.assertIsNone(proxima)

    def test_historial_aprobadas(self):
        qs = Booking.objects.historial_aprobadas()
        for booking in qs:
            self.assertTrue(booking.approved and booking.approval_date is not None)
            self.assertTrue(
                booking.date < DateTimeUtils.get_local_date() or
                (booking.date == DateTimeUtils.get_local_date() and
                 booking.time_slot.end_time < DateTimeUtils.get_local_time())
            )

    def test_con_cantidad_pedidos(self):
        qs = Booking.objects.con_cantidad_pedidos()
        for booking in qs:
            self.assertTrue(hasattr(booking, 'cantidad_pedidos'))

    def test_pendientes_por_usuario(self):
        qs = Booking.objects.pendientes_por_usuario(self.user1)
        self.assertTrue(all(b.user == self.user1 and b.approved and b.approval_date is None for b in qs))


class TimeSlotManagerTest(TestCase):

    def setUp(self):
        now = timezone.localtime()
        self.today = DateTimeUtils.get_local_date()
        self.yesterday = self.today - timedelta(days=1)
        self.tomorrow = self.today + timedelta(days=1)

        # Timeslots de prueba con distintos horarios
        self.timeslot_past = TimeSlot.objects.create(
            name="Past Slot",
            start_time=(now - timedelta(hours=3)).time(),
            end_time=(now - timedelta(hours=2)).time()
        )
        self.timeslot_future = TimeSlot.objects.create(
            name="Future Slot",
            start_time=(now + timedelta(hours=1)).time(),
            end_time=(now + timedelta(hours=2)).time()
        )
        self.timeslot_now = TimeSlot.objects.create(
            name="Now Slot",
            start_time=(now - timedelta(minutes=30)).time(),
            end_time=(now + timedelta(minutes=30)).time()
        )
        
    def test_disponibles_para_fecha_hoy_filtra_start_time(self):
        # Para fecha hoy, debe filtrar start_time > ahora
        resultado = TimeSlot.objects.disponibles_para_fecha(self.today)
        for ts in resultado:
            self.assertTrue(ts.start_time > DateTimeUtils.get_local_time())

    def test_disponibles_para_fecha_otra_fecha_retorna_todos(self):
        # Para fecha distinta a hoy, retorna todos los timeslots sin filtrar
        resultado = TimeSlot.objects.disponibles_para_fecha(self.tomorrow)
        timeslot_ids = set(ts.id for ts in resultado)
        esperado_ids = set([self.timeslot_past.id, self.timeslot_future.id, self.timeslot_now.id])
        self.assertSetEqual(timeslot_ids, esperado_ids)

    def test_manager_disponibles_para_fecha(self):
        # El método del manager debe llamar al queryset y funcionar igual
        resultado_manager = TimeSlot.objects.disponibles_para_fecha(self.today)
        resultado_qs = TimeSlot.objects.all().disponibles_para_fecha(self.today)
        self.assertQuerySetEqual(
            resultado_manager.order_by('id'),
            resultado_qs.order_by('id'),
            transform=lambda x: x
        )


class TableManagerTest(TestCase):

    def setUp(self):
        self.today = DateTimeUtils.get_local_date()
        now = timezone.localtime()
        
        # Crear un usuario para asignar a las reservas
        self.user = User.objects.create_user(username='testuser', password='pass')

        # Crear un timeslot
        self.timeslot = TimeSlot.objects.create(
            name="Test Slot",
            start_time=now.time(),
            end_time=(now + timedelta(hours=1)).time()
        )

        # Crear mesas
        self.table1 = Table.objects.create(capacity=4, number=1, description="Mesa para 4")
        self.table2 = Table.objects.create(capacity=6, number=2, description="Mesa para 6")
        self.table3 = Table.objects.create(capacity=2, number=3, description="Mesa para 2")

        # Crear una reserva que ocupe la mesa 1
        self.booking = Booking.objects.create(
            user=self.user,
            approved=True,
            approval_date=self.today,
            date=self.today,
            time_slot=self.timeslot,
            issue_date=self.today,
            code='RES1'
        )
        self.booking.tables.add(self.table1)

    def test_disponibles_para_fecha_y_timeslot_no_timeslot(self):
        qs = Table.objects.disponibles_para_fecha_y_timeslot(self.today, None)
        self.assertEqual(qs.count(), 0)

    def test_disponibles_para_fecha_y_timeslot_con_timeslot(self):
        qs = Table.objects.disponibles_para_fecha_y_timeslot(self.today, self.timeslot.id)
        self.assertIn(self.table2, qs)
        self.assertIn(self.table3, qs)
        self.assertNotIn(self.table1, qs)  # Mesa reservada no debe aparecer




# Testoes para los Modelos

class BookingModelTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        # Crear usuario para asignar a Booking
        cls.user = User.objects.create_user(username='testuser', password='pass')
        now = timezone.localtime()
        cls.timeslot = TimeSlot.objects.create(
            name="Test Slot",
            start_time=now.time(),
            end_time=(now + timedelta(hours=1)).time()
        )
        cls.table1 = Table.objects.create(capacity=4, number=1, description="Mesa 1")
        cls.table2 = Table.objects.create(capacity=6, number=2, description="Mesa 2")

        # Crear instancia Booking válida
        cls.booking = Booking.objects.create(
            approved=True,
            approval_date=DateTimeUtils.get_local_date(),
            code="RES123",
            observations="Test booking",
            date=DateTimeUtils.get_local_date(),
            time_slot=cls.timeslot,
            user=cls.user,
            issue_date=DateTimeUtils.get_local_date()
        )
        cls.booking.tables.add(cls.table1, cls.table2)

    def test_creacion_y_guardado(self):
        booking = Booking.objects.create(
            approved=False,
            code="UNQ001",
            date=DateTimeUtils.get_local_date(),
            time_slot=self.timeslot,
            user=self.user
        )
        booking.tables.add(self.table1)
        self.assertEqual(booking.code, "UNQ001")
        self.assertFalse(booking.approved)

    def test_validacion_unicidad_code(self):
        with self.assertRaises(Exception):
            Booking.objects.create(
                approved=False,
                code="RES123",  # código duplicado
                date=DateTimeUtils.get_local_date(),
                time_slot=self.timeslot,
                user=self.user
            )

    def test_str_representacion(self):
        self.assertEqual(str(self.booking), f'Codigo de Reserva: {self.booking.code}')

    def test_get_cantidad_pedidos(self):
        # Suponiendo que pueda tener atributo cantidad_pedidos
        self.booking.cantidad_pedidos = 5
        self.assertEqual(self.booking.get_cantidad_pedidos(), 5)

    def test_es_reserva_actual(self):
        hoy = DateTimeUtils.get_local_date()
        ahora = timezone.localtime().time()
        # Asegurar que para tu fecha y hour actuales devuelva True o False según corresponda
        self.booking.date = hoy
        self.booking.time_slot.start_time = (timezone.localtime() - timedelta(minutes=30)).time()
        self.booking.time_slot.end_time = (timezone.localtime() + timedelta(minutes=30)).time()
        self.assertTrue(self.booking.es_reserva_actual)
        # Y para otra fecha falso
        self.booking.date = hoy - timedelta(days=1)
        self.assertFalse(self.booking.es_reserva_actual)

    def test_get_card_title(self):
        fecha_actual = DateTimeUtils.get_local_date()
        hora_actual = timezone.localtime().time()
        self.booking.date = fecha_actual
        self.booking.time_slot.start_time = (timezone.localtime() - timedelta(minutes=30)).time()
        self.booking.time_slot.end_time = (timezone.localtime() + timedelta(minutes=30)).time()
        self.assertEqual(self.booking.get_card_title(fecha_actual, hora_actual), "Reserva Actual")

    def test_is_past_due(self):
        hoy = DateTimeUtils.get_local_date()
        ahora = timezone.localtime().time()
        self.booking.date = hoy - timedelta(days=1)
        self.assertTrue(self.booking.is_past_due())
        self.booking.date = hoy
        self.booking.time_slot.end_time = (timezone.localtime() - timedelta(minutes=30)).time()
        self.assertTrue(self.booking.is_past_due())
        self.booking.date = hoy
        self.booking.time_slot.end_time = (timezone.localtime() + timedelta(minutes=30)).time()
        self.assertFalse(self.booking.is_past_due())

    def test_relacion_tables_m2m(self):
        self.assertIn(self.table1, self.booking.tables.all())
        self.assertIn(self.table2, self.booking.tables.all())

    def test_integridad_on_delete(self):
        # Borrar usuario debería borrar reserva por on_delete=models.CASCADE
        self.user.delete()
        with self.assertRaises(Booking.DoesNotExist):
            Booking.objects.get(pk=self.booking.pk)


class TableModelTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.table = Table.objects.create(capacity=4, number=1, description="Mesa de prueba")

    def test_creacion_y_guardado(self):
        table = Table.objects.create(capacity=6, number=2)
        self.assertEqual(table.capacity, 6)
        self.assertEqual(table.number, 2)

    def test_str_representacion(self):
        self.assertEqual(str(self.table), f"Table {self.table.number}")

    def test_get_label(self):
        label = self.table.get_label()
        self.assertIn(f"Mesa {self.table.number}", label)
        self.assertIn(str(self.table.capacity), label)

    def test_save_autoincrement_number(self):
        # Guardar tabla sin número asignado activa autoincremento
        table = Table(capacity=2)
        table.save()
        self.assertIsNotNone(table.number)
        self.assertTrue(table.number > 0)

    def test_is_available(self):
        user = User.objects.create_user(username='tester')
        now = timezone.localtime()
        timeslot = TimeSlot.objects.create(
            name='Slot Test',
            start_time=now.time(),
            end_time=(now + timedelta(hours=1)).time()
        )
        booking = Booking.objects.create(
            approved=True,
            approval_date=DateTimeUtils.get_local_date(),
            code='CODE2',
            date=DateTimeUtils.get_local_date(),
            time_slot=timeslot,
            user=user,
            issue_date=DateTimeUtils.get_local_date()
        )
        booking.tables.add(self.table)

        # La mesa está reservada, no disponible
        self.assertFalse(self.table.is_available(timeslot, DateTimeUtils.get_local_date()))

        # Para otro timeslot o fecha estará disponible
        otro_slot = TimeSlot.objects.create(
            name='Otro Slot',
            start_time=(now + timedelta(hours=2)).time(),
            end_time=(now + timedelta(hours=3)).time()
        )
        self.assertTrue(self.table.is_available(otro_slot, DateTimeUtils.get_local_date()))

        otra_fecha = DateTimeUtils.get_local_date() + timedelta(days=1)
        self.assertTrue(self.table.is_available(timeslot, otra_fecha))


class TimeSlotModelTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.start_time = time(9, 0)
        cls.end_time = time(11, 0)
        cls.timeslot = TimeSlot.objects.create(
            name="Mañana",
            start_time=cls.start_time,
            end_time=cls.end_time,
        )
        cls.table1 = Table.objects.create(capacity=4, number=1, description="Mesa 1")
        cls.table2 = Table.objects.create(capacity=6, number=2, description="Mesa 2")
        cls.timeslot.tables.add(cls.table1, cls.table2)

    def test_creacion_y_guardado(self):
        self.assertEqual(self.timeslot.name, "Mañana")
        self.assertEqual(self.timeslot.start_time, self.start_time)
        self.assertEqual(self.timeslot.end_time, self.end_time)

    def test_str_representacion(self):
        self.assertEqual(str(self.timeslot), "Mañana")

    def test_get_label_horas(self):
        label = self.timeslot.get_label_horas()
        self.assertEqual(label, "09:00 hs. - 11:00 hs.")

    def test_is_future_true_false(self):
        ahora = DateTimeUtils.get_local_time()
        # Preparar timeslot con start_time en el futuro
        future_time = (timezone.localtime() + timedelta(hours=1)).time()
        past_time = (timezone.localtime() - timedelta(hours=1)).time()

        self.timeslot.start_time = future_time
        self.timeslot.save()
        self.assertTrue(self.timeslot.is_future())

        self.timeslot.start_time = past_time
        self.timeslot.save()
        self.assertFalse(self.timeslot.is_future())

    def test_m2m_tables_asociacion(self):
        tables = self.timeslot.tables.all()
        self.assertIn(self.table1, tables)
        self.assertIn(self.table2, tables)

    def test_m2m_tables_agregar_eliminar(self):
        table3 = Table.objects.create(capacity=2, number=3)
        self.timeslot.tables.add(table3)
        self.assertIn(table3, self.timeslot.tables.all())

        self.timeslot.tables.remove(table3)
        self.assertNotIn(table3, self.timeslot.tables.all())




# Testeos para el Helper
class TestBookingHelpers(TestCase):
    @patch('bookings_app.helpers.DateTimeUtils.get_local_datetime')
    def test_get_selected_date_from_request_defaults(self, mock_local_datetime):
        mock_local_datetime.return_value = datetime(2025, 9, 8)
        request = HttpRequest()
        request.GET = {}
        result = BookingHelpers.get_selected_date_from_request(request)
        self.assertEqual(result, date(2025, 9, 8))

    @patch('bookings_app.helpers.DateTimeUtils.get_local_datetime')
    def test_get_selected_date_from_request_with_params(self, mock_local_datetime):
        mock_local_datetime.return_value = datetime(2025, 9, 8)
        request = HttpRequest()
        request.GET = {'month': '10', 'day': '15'}
        result = BookingHelpers.get_selected_date_from_request(request)
        self.assertEqual(result, date(2025, 10, 15))

    @patch('bookings_app.helpers.DateTimeUtils.get_local_datetime')
    def test_get_selected_date_from_request_day_exceeds_max(self, mock_local_datetime):
        mock_local_datetime.return_value = datetime(2025, 2, 1)
        request = HttpRequest()
        request.GET = {'month': '2', 'day': '31'}  # Feb max 28/29
        result = BookingHelpers.get_selected_date_from_request(request)
        self.assertEqual(result, date(2025, 2, 28))

    def test_get_selected_timeslot_from_request(self):
        class DummyTimeslot:
            def __init__(self, id):
                self.id = id
        

        timeslot1 = DummyTimeslot(1)
        timeslot2 = DummyTimeslot(2)

        filtered_mock = MagicMock()
        filtered_mock.exists.return_value = True

        available_timeslots = MagicMock()
        available_timeslots.filter.return_value = filtered_mock
        available_timeslots.get.return_value = timeslot1
        available_timeslots.first.return_value = timeslot2

        request = HttpRequest()

        # Caso parámetro inválido - debería devolver first()
        request.GET = {'time_slot': 'abc'}
        result = BookingHelpers.get_selected_timeslot_from_request(request, available_timeslots)
        self.assertEqual(result.id, 2)

        # Caso parámetro válido - debería devolver get()
        request.GET = {'time_slot': '1'}
        result = BookingHelpers.get_selected_timeslot_from_request(request, available_timeslots)
        self.assertEqual(result.id, 1)
    
    def test_get_available_months(self):
        today = date(2025, 9, 15)
        months = BookingHelpers.get_available_months(today)
        expected_names = ["Septiembre", "Octubre", "Noviembre", "Diciembre"]
        self.assertEqual([m['nombre'] for m in months], expected_names)
        self.assertEqual([m['numero'] for m in months], [9, 10, 11, 12])

    def test_get_weekdays(self):
        weekdays = BookingHelpers.get_weekdays()
        self.assertEqual(weekdays, ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"])

    def test_get_month_calendar(self):
        cal = BookingHelpers.get_month_calendar(2025, 9)
        self.assertIsInstance(cal, list)
        for week in cal:
            self.assertIsInstance(week, list)

    @patch('bookings_app.helpers.DateTimeUtils.get_local_date')
    def test_get_availability_status(self, mock_get_local_date):
        mock_get_local_date.return_value = date(2025, 9, 8)

        time_slots = MagicMock()
        time_slots.exists.return_value = False
        available_tables = MagicMock()
        available_tables.exists.return_value = False

        msg = BookingHelpers.get_availability_status(date(2025, 9, 8), time_slots, available_tables)
        self.assertFalse(msg[2])
        self.assertIn("NO SE PUEDEN HACER MAS RESERVAS", msg[0])

        available_tables.exists.return_value = True
        msg = BookingHelpers.get_availability_status(date(2025, 9, 7), time_slots, available_tables)
        self.assertTrue(msg[2])
        self.assertEqual(msg[0], "Mesas Disponibles")

        available_tables.exists.return_value = False
        time_slots.exists.return_value = True
        msg = BookingHelpers.get_availability_status(date(2025, 9, 7), time_slots, available_tables)
        self.assertFalse(msg[2])
        self.assertIn("FRANJA HORARIA COMPLETA", msg[0])

    @patch('bookings_app.helpers.get_random_string')
    def test_generar_codigo_reserva_unique(self, mock_get_random_string):
        mock_get_random_string.side_effect = ['ABC123XYZ', 'UNIQUE123']

        with patch('bookings_app.helpers.Booking.objects.filter') as mock_filter:
            mock_filter.side_effect = [
                MagicMock(exists=lambda: True),
                MagicMock(exists=lambda: False)
            ]
            codigo = BookingHelpers.generar_codigo_reserva()
        self.assertEqual(codigo, 'UNIQUE123')
        self.assertEqual(len(codigo), 9)


class TableAdminFormTest(TestCase):
    def test_number_field_disabled_and_hidden(self):
        table = Table.objects.create(number=1, capacity=4)
        form = TableAdminForm(instance=table)
        self.assertTrue(form.fields['number'].disabled)
        html_output = form.as_p()
        self.assertIn(f'<input type="hidden" name="number" value="{table.number}">', html_output)





# Testeos para Formularios

class TimeSlotAdminFormTest(TestCase):
    def setUp(self):
        # Crear datos iniciales necesarios para las pruebas
        self.tables = [Table.objects.create(number=i, capacity=4) for i in range(1, 4)]
        self.time_slot = TimeSlot.objects.create(name="Mañana", start_time="09:00", end_time="12:00")
        self.time_slot.tables.set(self.tables)
    
    def test_clean_validate_time_overlap(self):
        form_data = {
            'name': 'Tarde',
            'start_time': '11:00',
            'end_time': '14:00',
            'tables': [self.tables[0].id]
        }
        form = TimeSlotAdminForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('El horario se superpone con las siguientes franjas:', form.errors['__all__'][0])

    def test_clean_requires_at_least_one_table(self):
        form_data = {
            'name': 'Noche',
            'start_time': '18:00',
            'end_time': '21:00',
            'tables': []
        }
        form = TimeSlotAdminForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('Debe asignar al menos una mesa a la franja horaria.', form.errors['__all__'][0])


class MakeReservationFormTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.table1 = Table.objects.create(number=1, capacity=4, description="Mesa VIP")
        cls.table2 = Table.objects.create(number=2, capacity=6, description="Mesa Patio")

    def test_queryset_assignment_and_labels(self):
        tables_queryset = Table.objects.all()
        form = MakeReservationForm(available_tables=tables_queryset)

        self.assertEqual(list(form.fields['tables'].queryset), list(tables_queryset))
        
        table = tables_queryset.first()
        label = form.get_table_label(table)
        self.assertIn(f"Mesa {table.number}", label)
        self.assertIn(f"Capacidad: {table.capacity}", label)
        self.assertIn(f"Descripción: {table.description}", label)




# Testeos para las Vistas

class BookingListViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='cliente', password='testpass123')
        
        # Crear o cargar grupo esperado
        grupo_cliente, created = Group.objects.get_or_create(name='Cliente')
        
        # Asignar grupo al usuario
        cls.user.groups.add(grupo_cliente)
        cls.user.save()
        
        cls.time_slot = TimeSlot.objects.create(name='Mañana', start_time='09:00', end_time='12:00')
        cls.booking1 = Booking.objects.create(
            user=cls.user,
            time_slot=cls.time_slot,
            approved=True,
            code=get_random_string(10)
        )
        cls.booking2 = Booking.objects.create(
            user=cls.user,
            time_slot=cls.time_slot,
            approved=False,
            code=get_random_string(10)
        )

    def test_redirect_if_not_logged_in(self):
        url = reverse('bookings_app:my_reservation')  # Cambiar por el name real de la url
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_logged_in_user_access(self):
        self.client.login(username='cliente', password='testpass123')
        url = reverse('bookings_app:my_reservation')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'bookings_app/my_reservation.html')

        context = response.context
        self.assertIn('proxima_reserva', context)
        self.assertIn('card_title', context)
        self.assertIn('reservas_futuras', context)
        self.assertIn('reservas_pendientes', context)
        self.assertIn('reservas_historial_aprobadas', context)
        self.assertIn('reservas_historial_rechazadas', context)
        self.assertIn('reservas_sin_confirmar', context)
        self.assertIn('cantidad_pedidos_proxima_reserva', context)

        # Confirmar que el queryset solo trae reservas del usuario
        bookings = context['bookings']
        self.assertTrue(all(b.user == self.user for b in bookings))


class GetNextReservationViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='cliente', password='testpass123')

        # Asegurar que usuario tiene el grupo requerido para ClienteRequiredMixin
        grupo_cliente, _ = Group.objects.get_or_create(name='Cliente')
        cls.user.groups.add(grupo_cliente)
        cls.user.save()

        cls.time_slot = TimeSlot.objects.create(name='Mañana', start_time='09:00', end_time='12:00')
        cls.booking = Booking.objects.create(
            user=cls.user,
            time_slot=cls.time_slot,
            approved=True,
            code=get_random_string(10)
        )

    def test_get_next_reservation_ajax(self):
        self.client.login(username='cliente', password='testpass123')
        url = reverse('bookings_app:get_next_reservation')

        response = self.client.get(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')

        json_data = response.json()
        self.assertIn('card_html', json_data)
        self.assertTrue(len(json_data['card_html']) > 0)  # Confirmar que envío algo en HTML


class GetFutureReservationsViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='cliente', password='testpass123')

        # Asignar usuario al grupo requerido
        grupo_cliente, _ = Group.objects.get_or_create(name='Cliente')
        cls.user.groups.add(grupo_cliente)
        cls.user.save()

        cls.time_slot = TimeSlot.objects.create(name='Mañana', start_time='09:00', end_time='12:00')
        # Crear reservas aprobadas y futuras
        cls.booking1 = Booking.objects.create(
            user=cls.user,
            time_slot=cls.time_slot,
            approved=True,
            code=get_random_string(10)
        )
        cls.booking2 = Booking.objects.create(
            user=cls.user,
            time_slot=cls.time_slot,
            approved=True,
            code=get_random_string(10)
        )

    def test_get_future_reservations_ajax(self):
        self.client.login(username='cliente', password='testpass123')
        url = reverse('bookings_app:get_future_reservations')

        response = self.client.get(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')

        json_data = response.json()
        self.assertIn('card_html', json_data)
        self.assertTrue(len(json_data['card_html']) > 0)  # Confirmar que html no está vacío


class GetPendingReservationsViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='cliente', password='testpass123')

        # Asignar usuario al grupo para pasar ClienteRequiredMixin
        grupo_cliente, _ = Group.objects.get_or_create(name='Cliente')
        cls.user.groups.add(grupo_cliente)
        cls.user.save()

        cls.time_slot = TimeSlot.objects.create(name='Tarde', start_time='15:00', end_time='18:00')
        cls.booking1 = Booking.objects.create(
            user=cls.user,
            time_slot=cls.time_slot,
            approved=False,  # Pendiente
            code=get_random_string(10)
        )
        cls.booking2 = Booking.objects.create(
            user=cls.user,
            time_slot=cls.time_slot,
            approved=False,  # Pendiente
            code=get_random_string(10)
        )

    def test_get_pending_reservations_ajax(self):
        self.client.login(username='cliente', password='testpass123')
        url = reverse('bookings_app:get_pending_reservations')

        response = self.client.get(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')

        json_data = response.json()
        self.assertIn('card_html', json_data)
        self.assertTrue(len(json_data['card_html']) > 0)  # Validar html renderizado


class GetHistoryAprobadasViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='cliente', password='testpass123')

        # Asignar usuario al grupo requerido para pasar ClienteRequiredMixin
        grupo_cliente, _ = Group.objects.get_or_create(name='Cliente')
        cls.user.groups.add(grupo_cliente)
        cls.user.save()

        cls.time_slot = TimeSlot.objects.create(name='Noche', start_time='20:00', end_time='23:00')
        # Crear reservas aprobadas para historial
        cls.booking1 = Booking.objects.create(
            user=cls.user,
            time_slot=cls.time_slot,
            approved=True,
            code=get_random_string(10)
        )
        cls.booking2 = Booking.objects.create(
            user=cls.user,
            time_slot=cls.time_slot,
            approved=True,
            code=get_random_string(10)
        )

    def test_get_history_aprobadas_ajax(self):
        self.client.login(username='cliente', password='testpass123')
        url = reverse('bookings_app:get_history_aprobadas')

        response = self.client.get(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')

        json_data = response.json()
        self.assertIn('card_html', json_data)
        self.assertTrue(len(json_data['card_html']) > 0)  # Validar HTML no vacío


class GetHistoryRechazadasViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='cliente', password='testpass123')

        # Asignar grupo Cliente para pasar ClienteRequiredMixin
        grupo_cliente, _ = Group.objects.get_or_create(name='Cliente')
        cls.user.groups.add(grupo_cliente)
        cls.user.save()

        cls.time_slot = TimeSlot.objects.create(name='Mañana', start_time='09:00', end_time='12:00')
        # Crear reservas rechazadas
        cls.booking1 = Booking.objects.create(
            user=cls.user,
            time_slot=cls.time_slot,
            approved=False,
            code=get_random_string(10)
        )
        cls.booking2 = Booking.objects.create(
            user=cls.user,
            time_slot=cls.time_slot,
            approved=False,
            code=get_random_string(10)
        )

    def test_get_history_rechazadas_ajax(self):
        self.client.login(username='cliente', password='testpass123')
        url = reverse('bookings_app:get_history_rechazadas')

        response = self.client.get(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')

        json_data = response.json()
        self.assertIn('card_html', json_data)
        self.assertTrue(len(json_data['card_html']) > 0)


class DeleteBookingViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='cliente', password='testpass123')
        grupo_cliente, _ = Group.objects.get_or_create(name='Cliente')
        cls.user.groups.add(grupo_cliente)
        cls.user.save()

        cls.time_slot = TimeSlot.objects.create(name='Tarde', start_time='15:00', end_time='18:00')
        cls.booking = Booking.objects.create(
            user=cls.user,
            time_slot=cls.time_slot,
            approved=True,
            code=get_random_string(10)
        )

    def test_delete_booking(self):
        self.client.login(username='cliente', password='testpass123')
        url = reverse('bookings_app:delete_booking', kwargs={'pk': self.booking.pk})

        response = self.client.post(url)

        # Test que la respuesta es JSON y success True
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        self.assertJSONEqual(response.content, {'success': True})

        # Test que el objeto Booking fue eliminado
        self.assertFalse(Booking.objects.filter(pk=self.booking.pk).exists())

    def test_delete_booking_not_owner(self):
        # Otro usuario intenta borrar reserva que no es suya
        otro_usuario = User.objects.create_user(username='otro', password='testpass123')
        self.client.login(username='otro', password='testpass123')
        url = reverse('bookings_app:delete_booking', kwargs={'pk': self.booking.pk})

        response = self.client.post(url)
        
        # Debe obtener 404 porque no pertenece al usuario logueado
        self.assertEqual(response.status_code, 403)


class MakeReservationViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='cliente', password='testpass123')
        grupo_cliente, _ = Group.objects.get_or_create(name='Cliente')
        cls.user.groups.add(grupo_cliente)
        cls.user.save()

        # Crear tablas y franjas horarias para usar en los tests
        cls.table1 = Table.objects.create(number=1, capacity=4, description='Mesa 1')
        cls.table2 = Table.objects.create(number=2, capacity=4, description='Mesa 2')
        cls.time_slot = TimeSlot.objects.create(name='Mañana', start_time='10:00', end_time='12:00')

    def setUp(self):
        self.client.login(username='cliente', password='testpass123')
        session = self.client.session
        session.save()

    def test_get_view_authenticated(self):
        self.client.login(username='cliente', password='testpass123')
        url = reverse('bookings_app:make_reservation')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'bookings_app/make_reservation.html')

    def test_get_view_redirect_if_not_logged_in(self):
        self.client.logout()
        url = reverse('bookings_app:make_reservation')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    @patch('bookings_app.helpers.BookingHelpers.get_selected_date_from_request')
    @patch('bookings_app.helpers.BookingHelpers.get_selected_timeslot_from_request')
    @patch('bookings_app.helpers.BookingHelpers.generar_codigo_reserva')
    @patch('bookings_app.models.Booking.objects.del_usuario')
    def test_post_form_valid_creates_booking(self, mock_del_usuario, mock_generar_codigo, mock_get_selected_timeslot, mock_get_selected_date):
        self.client.login(username='cliente', password='testpass123')
        mock_del_usuario.return_value.pendientes.return_value.exists.return_value = False
        mock_generar_codigo.return_value = 'ABC1234567'
        mock_get_selected_date.return_value = date(2025, 9, 20)

        mock_time_slot = MagicMock()
        mock_time_slot.id = self.time_slot.id  # Usar id real
        mock_get_selected_timeslot.return_value = mock_time_slot

        url = reverse('bookings_app:make_reservation')

        post_data = {
            'time_slot': self.time_slot.id,
            'tables': [self.table1.id, self.table2.id],
            'observations': 'Test reservation'
        }

        response = self.client.post(url, post_data, follow=True)

        self.assertRedirects(response, reverse('bookings_app:my_reservation'))
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('Reserva solicitada con éxito' in str(message) for message in messages))
