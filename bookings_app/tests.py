from django.test import TestCase
from django.utils import timezone
from unittest.mock import patch
from bookings_app.models import Booking, Table, TimeSlot
from django.contrib.auth import get_user_model
import datetime

User = get_user_model()

class BookingModelTests(TestCase):
    def setUp(self):
        # Crear usuario para usar en Booking
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='pass')
        # Crear tabla y timeslot para relaciones
        self.table1 = Table.objects.create(capacity=4, number=1)
        self.time_slot = TimeSlot.objects.create(
            name='Mañana',
            start_time=datetime.time(9, 0),
            end_time=datetime.time(12, 0)
        )
        self.time_slot.tables.add(self.table1)

    def test_creacion_booking(self):
        booking = Booking.objects.create(
            approved=False,
            code='ABC123',
            date=timezone.localdate(),
            time_slot=self.time_slot,
            user=self.user
        )
        booking.tables.add(self.table1)
        self.assertEqual(booking.code, 'ABC123')
        self.assertFalse(booking.approved)
        self.assertIn(self.table1, booking.tables.all())
        self.assertEqual(booking.user, self.user)
        self.assertEqual(str(booking), 'Codigo de Reserva: ABC123')

    def test_actualizacion_booking(self):
        booking = Booking.objects.create(code='UPD123', user=self.user, time_slot=self.time_slot)
        booking.approved = True
        booking.save()
        self.assertTrue(Booking.objects.get(id=booking.id).approved)

    def test_eliminacion_booking(self):
        booking = Booking.objects.create(code='DEL123', user=self.user, time_slot=self.time_slot)
        booking_id = booking.id
        booking.delete()
        with self.assertRaises(Booking.DoesNotExist):
            Booking.objects.get(id=booking_id)

    def test_unicidad_codigo(self):
        Booking.objects.create(code='UNIQ123', user=self.user, time_slot=self.time_slot)
        with self.assertRaises(Exception):
            Booking.objects.create(code='UNIQ123', user=self.user, time_slot=self.time_slot)

    @patch('bookings_app.utils.DateTimeUtils.get_local_date')
    @patch('bookings_app.utils.DateTimeUtils.get_local_time')
    def test_es_reserva_actual_true(self, mock_time, mock_date):
        mock_date.return_value = datetime.date(2025, 8, 20)
        mock_time.return_value = datetime.time(10, 0)
        booking = Booking.objects.create(code='RESACT123', user=self.user, time_slot=self.time_slot, date=mock_date.return_value)
        booking.tables.add(self.table1)
        self.assertTrue(booking.es_reserva_actual)

    @patch('bookings_app.utils.DateTimeUtils.get_local_date')
    @patch('bookings_app.utils.DateTimeUtils.get_local_time')
    def test_es_reserva_actual_false(self, mock_time, mock_date):
        mock_date.return_value = datetime.date(2025, 8, 20)
        mock_time.return_value = datetime.time(8, 0)  # Antes del start_time
        booking = Booking.objects.create(code='RESACT124', user=self.user, time_slot=self.time_slot, date=mock_date.return_value)
        booking.tables.add(self.table1)
        self.assertFalse(booking.es_reserva_actual)

    def test_get_card_title(self):
        fecha_actual = datetime.date(2025, 8, 20)
        hora_actual = datetime.time(10, 0)
        booking = Booking.objects.create(code='CARD123', user=self.user, time_slot=self.time_slot, date=fecha_actual)
        booking.tables.add(self.table1)
        self.assertEqual(booking.get_card_title(fecha_actual, hora_actual), "Reserva Actual")

        fecha_futura = datetime.date(2025, 8, 21)
        self.assertEqual(booking.get_card_title(fecha_futura, hora_actual), "Próxima Reserva")

    @patch('bookings_app.utils.DateTimeUtils.get_local_date')
    @patch('bookings_app.utils.DateTimeUtils.get_local_time')
    def test_is_past_due(self, mock_time, mock_date):
        mock_date.return_value = datetime.date(2025, 8, 20)
        mock_time.return_value = datetime.time(11, 30)

        past_date = datetime.date(2025, 8, 19)
        booking_past = Booking.objects.create(code='PAST123', user=self.user, time_slot=self.time_slot, date=past_date)
        booking_past.tables.add(self.table1)
        self.assertTrue(booking_past.is_past_due())

        today_date = mock_date.return_value
        end_time_past = datetime.time(11, 0)
        # Modificar time_slot para que end_time sea anterior a hora actual
        booking_today = Booking.objects.create(code='PAST124', user=self.user, time_slot=self.time_slot, date=today_date)
        booking_today.tables.add(self.table1)
        self.time_slot.end_time = end_time_past
        self.time_slot.save()
        self.assertTrue(booking_today.is_past_due())

        # Con end_time posterior a hora actual
        self.time_slot.end_time = datetime.time(12, 0)
        self.time_slot.save()
        booking_future = Booking.objects.create(code='PAST125', user=self.user, time_slot=self.time_slot, date=today_date)
        booking_future.tables.add(self.table1)
        self.assertFalse(booking_future.is_past_due())


class TableModelTests(TestCase):

    def setUp(self):
        self.table = Table.objects.create(capacity=4, number=1, description='Mesa principal')

    def test_creacion_table(self):
        self.assertEqual(self.table.capacity, 4)
        self.assertEqual(self.table.number, 1)
        self.assertEqual(self.table.description, 'Mesa principal')
        self.assertEqual(str(self.table), 'Table 1')
        self.assertEqual(self.table.get_label(), 'Mesa 1 | Capacidad: 4 | Descripción: Mesa principal')

    def test_actualizacion_table(self):
        self.table.capacity = 6
        self.table.save()
        self.assertEqual(Table.objects.get(id=self.table.id).capacity, 6)

    def test_eliminacion_table(self):
        table_id = self.table.id
        self.table.delete()
        with self.assertRaises(Table.DoesNotExist):
            Table.objects.get(id=table_id)

    def test_autonumeracion_number(self):
        table2 = Table.objects.create(capacity=2)
        self.assertEqual(table2.number, 2)  # Debe asignar número siguiente automáticamente

    def test_numero_unico(self):
        with self.assertRaises(Exception):
            Table.objects.create(capacity=2, number=1)  # number debe ser único

    def test_is_available(self):
        # Crear usuario y booking para ocupar la mesa
        user = User.objects.create_user(username='u1', email='u1@example.com', password='pass')
        time_slot = TimeSlot.objects.create(name='Tarde', start_time=datetime.time(13, 0), end_time=datetime.time(15, 0))
        time_slot.tables.add(self.table)

        booking = Booking.objects.create(code='BK001', user=user, time_slot=time_slot, date=timezone.localdate(), approved=True)
        booking.tables.add(self.table)
        disponible = self.table.is_available(time_slot, timezone.localdate())
        self.assertFalse(disponible)  # Mesa ocupada en ese time_slot y fecha

        # Probar disponibilidad en otro time_slot sin reservas
        otro_time_slot = TimeSlot.objects.create(name='Noche', start_time=datetime.time(19, 0), end_time=datetime.time(22, 0))
        otro_time_slot.tables.add(self.table)
        disponible_otro = self.table.is_available(otro_time_slot, timezone.localdate())
        self.assertTrue(disponible_otro)

class TimeSlotModelTests(TestCase):

    def setUp(self):
        self.time_slot = TimeSlot.objects.create(
            name='Mañana',
            start_time=datetime.time(9, 0),
            end_time=datetime.time(12, 0)
        )

    def test_creacion_timeslot(self):
        self.assertEqual(self.time_slot.name, 'Mañana')
        self.assertEqual(str(self.time_slot), 'Mañana')
        self.assertEqual(self.time_slot.get_label_horas(), '09:00 hs. - 12:00 hs.')

    def test_actualizacion_timeslot(self):
        self.time_slot.name = 'Mañana Actualizada'
        self.time_slot.save()
        self.assertEqual(TimeSlot.objects.get(id=self.time_slot.id).name, 'Mañana Actualizada')

    def test_eliminacion_timeslot(self):
        ts_id = self.time_slot.id
        self.time_slot.delete()
        with self.assertRaises(TimeSlot.DoesNotExist):
            TimeSlot.objects.get(id=ts_id)

    def test_is_future(self):
        ahora = timezone.localtime().time()
        # Crear TimeSlot futuro
        futuro = (datetime.datetime.combine(datetime.date.today(), ahora) + datetime.timedelta(hours=1)).time()
        ts_futuro = TimeSlot.objects.create(name='Futuro', start_time=futuro, end_time=(datetime.datetime.combine(datetime.date.today(), futuro) + datetime.timedelta(hours=2)).time())
        self.assertTrue(ts_futuro.is_future())

        # Crear TimeSlot pasado o actual
        pasado = (datetime.datetime.combine(datetime.date.today(), ahora) - datetime.timedelta(hours=1)).time()
        ts_pasado = TimeSlot.objects.create(name='Pasado', start_time=pasado, end_time=ahora)
        self.assertFalse(ts_pasado.is_future())

