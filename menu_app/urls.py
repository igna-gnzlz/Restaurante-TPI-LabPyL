from django.urls import path
from .views import HomeView, MenuListView, ProductDetailView, BookingListView
from . import views

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("menu/", MenuListView.as_view(), name="menu"),
    path("menu/<int:pk>/", ProductDetailView.as_view(), name="product_detail"),
    path("bookings/", BookingListView.as_view(), name="bookings"),
    path('realizar/', views.realizar_reserva, name='realizar_reserva'),
    path('realizar-pedido/', views.realizar_pedido, name='realizar_pedido'),
]