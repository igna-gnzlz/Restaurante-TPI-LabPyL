from django.views.generic import TemplateView, ListView, DetailView
from django.shortcuts import get_object_or_404
from .models import Product, Booking, Notification, UserRecievesNotification


class HomeView(TemplateView):
    template_name = "home.html"


class MenuListView(ListView):
    model = Product
    template_name = "menu_app/menu.html"
    context_object_name = "menu_items"

    def get_queryset(self):
        return Product.objects.all().order_by("title")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class ProductDetailView(DetailView):
    model = Product
    template_name = "menu_app/product_detail.html"
    context_object_name = "product"

class BookingListView(ListView):
    model = Booking
    template_name = "menu_app/booking_list.html"
    context_object_name = "bookings"

    def get_queryset(self):
        return Booking.objects.order_by("approval_date","date")
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['booking'] = Booking.objects.order_by("approval_date","date")
        return context
    
class NotificationListView(ListView):
    model = Notification
    template_name = "menu_app/notification_list.html"
    context_object_name = "notifications"

    def get_queryset(self):
        return Notification.objects.order_by("-created_at")

class NotificationReceiversView(DetailView):
    model = Notification
    template_name = "menu_app/notification_receivers.html"
    context_object_name = "notification"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Obtener la notificación actual (ya está en context['notification'], pero OK)
        notification = context['notification']

        # Obtener los UserRecievesNotification para esta notificación con usuarios no nulos
        receivers = UserRecievesNotification.objects.filter(notification=notification, user__isnull=False)
        
        # Pasar la lista de usuarios al contexto (puedes pasar solo los usuarios si quieres)
        context['receivers'] = [ur.user for ur in receivers]

        return context