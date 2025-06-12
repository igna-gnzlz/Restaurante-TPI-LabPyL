from django.views.generic import TemplateView, ListView, DetailView
from .models import Product, Order, OrderContainsProduct
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.timezone import now
import uuid


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
    slug_field = 'slug'
    slug_url_kwarg = 'slug'


class AddToOrderView(LoginRequiredMixin, View):
    # Vista para agregar productos al pedido del usuario (POST)
    def post(self, request, slug):
        # Obtener el producto por slug
        #   Si el slug no es válido, se lanzará un 404
        #   y no se ejecutará el resto del código
        product = get_object_or_404(Product, slug=slug)
        
        # Obtener o crear un pedido activo del usuario
        order, created = Order.objects.get_or_create(
            user=request.user,
            state='P',
            # Valores iniciales de creación, si el pedido no existe
            defaults={
                'buyDate': now().date(),
                'code': uuid.uuid4().hex[:15], # Generar código único de 15 caracteres
                'amount': 0.0,
            }
        )
        
        # Obtener o crear la relación del productos con el pedido
        # ocp se refiere a OrderContainsProduct, es decir, la relación entre el pedido y el producto
        ocp, created_ocp = OrderContainsProduct.objects.get_or_create(
            order=order,
            product=product,
            # Valores iniciales de creación, si el producto no estaba en la orden
            defaults={
                'subtotal': product.price,
                'quantity': 1
            }
        )
        
        # Si el producto ya existe en la orden, incrementar cantidad y subtotal
        if not created_ocp:
            ocp.quantity += 1
            ocp.subtotal = ocp.quantity * product.price
            ocp.save()
        
        # Actualizar el monto total del pedido
        order.amount = sum( item.subtotal for item in order.ordercontainsproduct_set.all() )
        order.save()
        
        
        # Redirección
        return redirect("order_detail")
    
class OrderDetailView(LoginRequiredMixin, DetailView):
    # Vista para mostrar el pedido del usuario
    template_name = 'menu_app/my_order.html'
    context_object_name = 'order'
    
    # Obtiene el pedido actuvo del usuario
    def get_object(self):
        return get_object_or_404(
            Order.objects.prefetch_related('ordercontainsproduct_set__product'),
            user=self.request.user,
            state='P'
        )