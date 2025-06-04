from django.views.generic import TemplateView, ListView, DetailView
from .models import Product
from bookings_app.models import Booking


class HomeView(TemplateView):
    template_name = "home.html"


class MenuListView(ListView):
    model = Product
    template_name = "menu_app/menu.html"
    context_object_name = "menu_items"

    def get_queryset(self):
        return Product.objects.all().order_by("name")

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