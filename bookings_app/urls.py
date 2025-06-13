from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView
from . import views
from .views import UserOrdersHistoryView

urlpatterns = [
    # Reservations urls
    path('mis-reservas/', views.BookingListView.as_view(), name='user_reservations_history'),
     path('historial/', UserOrdersHistoryView.as_view(), name='user_orders_history'),

]