from bookings_app.views import (
    GetNextReservationView,
    GetFutureReservationsView,
    GetPendingReservationsView,
    BookingListView,
    DeleteBookingView,
    MakeReservationView,
    GetHistoryAprobadasView,
    GetHistoryRechazadasView,
    ReservationOrdersView,
    CancelOrderView,
    DeleteOrderView
)
from django.urls import path


app_name = 'bookings_app'

urlpatterns = [
    path('my_reservation/', BookingListView.as_view(), name='my_reservation'),
    path('make_reservation', MakeReservationView.as_view(), name='make_reservation'),
    path('delete_booking/<int:pk>/', DeleteBookingView.as_view(), name='delete_booking'),
    path('get_next_reservation/', GetNextReservationView.as_view(), name='get_next_reservation'),
    path('get_future_reservations/', GetFutureReservationsView.as_view(), name='get_future_reservations'),
    path('get_pending_reservations/', GetPendingReservationsView.as_view(), name='get_pending_reservations'),
    path('get_history_aprobadas/', GetHistoryAprobadasView.as_view(), name='get_history_aprobadas'),
    path('get_history_rechazadas/', GetHistoryRechazadasView.as_view(), name='get_history_rechazadas'),
    path('my_reservation/<int:pk>/orders/', ReservationOrdersView.as_view(), name='reservation_orders'),
    path('order/<int:pk>/cancel/', CancelOrderView.as_view(), name='cancel_order'),
    path('order/<int:pk>/delete/', DeleteOrderView.as_view(), name='delete_order')
]
