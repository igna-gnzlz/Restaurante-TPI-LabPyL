from django.urls import path
from .views import HomeView, MenuListView, ProductDetailView, BookingListView, NotificationListView, NotificationReceiversView

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("menu/", MenuListView.as_view(), name="menu"),
    path("menu/<int:pk>/", ProductDetailView.as_view(), name="product_detail"),
    path("bookings/", BookingListView.as_view(), name="bookings"),
    path('notifications/', NotificationListView.as_view(), name='notification_list'),
    path('notifications/<int:pk>/receivers/', NotificationReceiversView.as_view(), name='notification_receivers'),
]