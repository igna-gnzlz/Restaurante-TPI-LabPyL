from django.urls import path
from bookings_app.views import BookingListView, DeleteBookingView, MakeReservationView
from bookings_app.views import GetNextReservationView, GetFutureReservationsView, GetPendingReservationsView
from bookings_app.views import GetHistoryAprobadasView, GetHistoryRechazadasView

app_name = 'bookings_app'

urlpatterns = [
    path('my_reservation/', BookingListView.as_view(), name='my_reservation'),
    path('make_reservation', MakeReservationView.as_view(), name='make_reservation'),
    path('delete_booking/<int:pk>/', DeleteBookingView.as_view(), name='delete_booking'),
    path('get_next_reservation/', GetNextReservationView.as_view(), name='get_next_reservation'),
    path('get_future_reservations/', GetFutureReservationsView.as_view(), name='get_future_reservations'),
    path('get_pending_reservations/', GetPendingReservationsView.as_view(), name='get_pending_reservations'),
    path('get_history_aprobadas/', GetHistoryAprobadasView.as_view(), name='get_history_aprobadas'),
    path('get_history_rechazadas/', GetHistoryRechazadasView.as_view(), name='get_history_rechazadas')
]
