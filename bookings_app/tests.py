from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from bookings_app.models import Booking, TimeSlot, Table
from bookings_app.utils import DateTimeUtils


User = get_user_model()

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
