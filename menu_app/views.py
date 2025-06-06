from django.views.generic import TemplateView, ListView, DetailView
from .models import Product, Booking
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import Order
from django.http import JsonResponse

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

def realizar_reserva(request):
    return render(request, 'realizar_reserva.html')

def realizar_pedido(request):
    return render(request, 'realizar_pedido.html')

def mis_pedidos(request):
    if request.user.is_authenticated:
        pedidos = Order.objects.filter(user=request.user).order_by('-fecha')
    else:
        pedidos = Order.objects.none()  # No mostrar nada si no está logueado
    return render(request, 'mis_pedidos.html', {'pedidos': pedidos})

# Vista para obtener la reserva pendiente del usuario autenticado
def obtener_reserva_usuario(request):
    # Verifica si el usuario está autenticado
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'No autenticado'}, status=401)

    # Busca la primera reserva pendiente del usuario
    reserva = Booking.objects.filter(user=request.user, status='pending').first()
    if reserva:
        # Si existe una reserva, prepara los datos a devolver
        data = {
            'fecha': reserva.date.strftime('%Y-%m-%d'),
            'hora': reserva.timeslot.name,
            'mesa': reserva.table.number,
            'estado': reserva.status,
            # agregá los campos que necesites mostrar
        }
        return JsonResponse({'reserva': data})
    else:
        # Si no hay reserva pendiente, devuelve None
        return JsonResponse({'reserva': None})



    
