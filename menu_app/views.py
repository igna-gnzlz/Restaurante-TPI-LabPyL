from .forms import AddOneForm, RemoveOneForm, DeleteItemForm, CancelOrderForm
from django.views.generic import TemplateView, ListView, DetailView, FormView
from .models import Product, Order, OrderContainsProduct, Category
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.mixins import LoginRequiredMixin
from bookings_app.models import Booking
from django.urls import reverse_lazy
from django.contrib import messages
from django.views import View


class AddOneView(LoginRequiredMixin, View):
    def post(self, request):
        form = AddOneForm(request.POST)
        if form.is_valid():
            item_id = form.cleaned_data['item_id']
            item = get_object_or_404(
                OrderContainsProduct,
                id=item_id,
                order__user=request.user,
                order__state='P'
            )
            item.quantity += 1
            item.subtotal = item.quantity * item.product.price
            item.save()
            order = item.order
            order.amount = sum(i.subtotal for i in order.ordercontainsproduct_set.all())
            order.save()
        return redirect('menu_app:order_detail')

class RemoveOneView(LoginRequiredMixin, View):
    def post(self, request):
        form = RemoveOneForm(request.POST)
        if form.is_valid():
            item_id = form.cleaned_data['item_id']
            item = get_object_or_404(
                OrderContainsProduct,
                id=item_id,
                order__user=request.user,
                order__state='P'
            )
            order = item.order
            if item.quantity > 1:
                item.quantity -= 1
                item.subtotal = item.quantity * item.product.price
                item.save()
            else:
                item.delete()
            order.amount = sum(i.subtotal for i in order.ordercontainsproduct_set.all())
            order.save()
        return redirect('menu_app:order_detail')

class DeleteItemView(LoginRequiredMixin, FormView):
    form_class = DeleteItemForm
    success_url = reverse_lazy('menu_app:order_detail')
    action = 'delete_item'
    template_name = 'menu_app/delete_item.html'
    def form_valid(self, form):
        item_id = form.cleaned_data['item_id']
        item = get_object_or_404(
            OrderContainsProduct,
            id=item_id,
            order__user=self.request.user,
            order__state='P'
        )
        order = item.order
        item.delete()
        order.amount = sum(i.subtotal for i in order.ordercontainsproduct_set.all())
        order.save()
        return super().form_valid(form)

class CancelOrderView(LoginRequiredMixin, FormView):
    template_name = 'menu_app/cancel_order.html'
    form_class = CancelOrderForm  # <--- sin paréntesis ni argumentos

    def form_valid(self, form):
        order_id = form.cleaned_data['order_id']
        order = get_object_or_404(Order, id=order_id, user=self.request.user, state='P')
        order.delete()
        return redirect('menu_app:menu')

class HomeView(TemplateView):
    template_name = "home.html"

class MenuListView(ListView):
    model = Category
    template_name = 'menu_app/menu.html'
    context_object_name = 'categories'
    
    def get_queryset(self):
        return Category.objects.filter(isActive=True).order_by('id')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        categories = self.get_queryset()
        categorized_items = {}
        
        for category in categories:
            products = Product.objects.filter(category=category)
            if products.exists():
                categorized_items[category] = products
                
        context['categorized_items'] = categorized_items
        return context
    
class ProductDetailView(DetailView):
    model = Product
    template_name = "menu_app/product_detail.html"
    context_object_name = "product"

class MyOrdersView(LoginRequiredMixin, View):
    template_name = 'menu_app/my_orders.html'

    def get(self, request):
        from menu_app.utils.cart import get_cart_items_and_total
        from django.db.models import Q
        from django.utils import timezone

        local_now = timezone.localtime()
        hoy = local_now.date()
        ahora = local_now.time()

        reservas_usuario = Booking.objects.filter(user=self.request.user).select_related('time_slot')

        reservas_proximas = Booking.objects.none()  # vacío por defecto
        reservas_proximas = reservas_usuario.filter(
            approved=True,
            approval_date__isnull=False
        ).filter(
            Q(date__gt=hoy) |
            Q(date=hoy, time_slot__start_time__gt=ahora)
        ).order_by('date', 'time_slot__start_time')

        reserva_seleccionada = None
        pedidos_reserva = []

        reserva_id = request.GET.get('booking')
        if reserva_id:
            reserva_seleccionada = get_object_or_404(reservas_proximas, id=reserva_id)
            pedidos_reserva = Order.objects.filter(user=request.user, booking=reserva_seleccionada)
            request.session['booking_selected_id'] = reserva_seleccionada.id
        else:
            booking_selected_id_session = request.session.get('booking_selected_id')
            if booking_selected_id_session:
                reserva_seleccionada = get_object_or_404(reservas_proximas, id=booking_selected_id_session)
                pedidos_reserva = Order.objects.filter(user=request.user, booking=reserva_seleccionada)

        carrito_reserva = []
        total_carrito = 0.00
        if reserva_seleccionada:
            carrito_reserva, total_carrito = get_cart_items_and_total(request.session, reserva_seleccionada.id)

        context = {
            'reservas_proximas': reservas_proximas,
            'reserva_seleccionada': reserva_seleccionada,
            'pedidos_reserva': pedidos_reserva,
            'carrito_reserva': carrito_reserva,
            'total_carrito': total_carrito
        }

        return render(request, self.template_name, context)


class AddToOrderView(LoginRequiredMixin, View):
    def post(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        booking_id = request.session.get('booking_selected_id')

        if not booking_id:
            messages.warning(request, "Seleccione primero una reserva.")
            return redirect('my_orders')

        cart = request.session.get('cart', {})

        booking_key = str(booking_id)
        product_key = str(product.id)

        if booking_key not in cart:
            cart[booking_key] = {}

        if product_key in cart[booking_key]:
            cart[booking_key][product_key]['quantity'] += 1
        else:
            cart[booking_key][product_key] = {'quantity': 1}

        request.session['cart'] = cart  # Guardar cambios en la sesión
        request.session.modified = True

        messages.success(request, f'Se agregó "{product.name}" al pedido.')
        return redirect('my_orders')
