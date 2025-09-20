from django.http import JsonResponse
from django.views.generic import TemplateView, ListView, DetailView, FormView
from menu_app.models import Product, Order, OrderContainsProduct, Category, Rating, Combo, OrderContainsCombo
from menu_app.forms import RatingForm
from accounts_app.models import User
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.mixins import LoginRequiredMixin
from bookings_app.models import Booking
from django.contrib import messages
from django.urls import reverse, reverse_lazy
from django.views import View
from django.utils.timezone import now


class MakeRatingView(FormView):
    form_class = RatingForm
    template_name = 'menu_app/rating_form.html'
    success_url = reverse_lazy('menu_app:menu')

    def dispatch(self, request, *args, **kwargs):
        self.product = get_object_or_404(Product, pk=kwargs.get('product_id'))
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['product'] = self.product
        return context

    def form_valid(self, form):
        rating = form.save(commit=False)
        rating.user = self.request.user if self.request.user.is_authenticated else None
        rating.product = self.product
        rating.save()
        messages.success(self.request, "¡Comentario creado con éxito!")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Por favor corrija los errores en el formulario.")
        return super().form_invalid(form)


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
                for product in products:
                    product.rating_form = RatingForm()
                    product.comments = product.rating_set.select_related('user').order_by('-created_at')
                categorized_items[category] = products
                
        context['categorized_items'] = categorized_items
        context['rating_form'] = RatingForm()
        context['combos'] = Combo.objects.all()
        return context
        
class ComboDetailView(ListView):
    model = Combo
    template_name = 'menu_app/combo_detail.html'
    context_object_name= 'combo'


class HomeView(TemplateView):
    template_name = "home.html"

    
class ProductDetailView(DetailView):
    model = Product
    template_name = "menu_app/product_detail.html"
    context_object_name = "product"

class MakeOrderView(LoginRequiredMixin, View):
    template_name = 'menu_app/make_order.html'

    def get(self, request):
        from menu_app.utils.cart import get_cart_products_by_booking
        from django.db.models import Q
        from django.utils import timezone

        local_now = timezone.localtime()
        hoy = local_now.date()
        ahora = local_now.time()

        reservas_usuario = Booking.objects.filter(user=self.request.user).select_related('time_slot')
        reservas_proximas = Booking.objects.none()  # vacío por defecto

        # Todas las reservas futuras o actuales (aprobadas y con fecha de aprobación)
        reservas_proximas = reservas_usuario.filter(
            approved=True,
            approval_date__isnull=False
        ).filter(
            Q(date__gt=hoy) |
            Q(date=hoy, time_slot__end_time__gte=ahora)
        ).order_by('date', 'time_slot__start_time')

        reserva_seleccionada = None

        reserva_id = request.GET.get('booking')
        if reserva_id:
            reserva_seleccionada = get_object_or_404(reservas_proximas, id=reserva_id)
            request.session['booking_selected_id'] = reserva_seleccionada.id
        else:
            booking_selected_id_session = request.session.get('booking_selected_id')
            if booking_selected_id_session:
                try:
                    reserva_seleccionada = reservas_proximas.get(id=booking_selected_id_session)
                except Booking.DoesNotExist:
                    reserva_seleccionada = None
                    request.session.pop('booking_selected_id', None)  # limpia sesión si la reserva ya no existe


        carrito_reserva = []
        total_carrito = 0.00
        if reserva_seleccionada:
            carrito_reserva, total_carrito = get_cart_products_by_booking(request.session, reserva_seleccionada.id)

        context = {
            'reservas_proximas': reservas_proximas,
            'reserva_seleccionada': reserva_seleccionada,
            'carrito_reserva': carrito_reserva,
            'total_carrito': total_carrito
        }

        return render(request, self.template_name, context)


class AddToOrderView(LoginRequiredMixin, View):
    def post(self, request, pk):
        from menu_app.utils.cart import get_cart_products_by_booking
        product = get_object_or_404(Product, pk=pk)
        booking_selected_id = request.session.get('booking_selected_id')

        if not booking_selected_id:
            return JsonResponse({
                "success": False,
                "message": "Seleccione primero una reserva."
            }, status=400)

        cart = request.session.get('cart', {})
        booking_key = str(booking_selected_id)
        product_key = str(product.id)

        # Obtener cantidad actual del producto en el carrito (si existe)
        prod_quantity_cart = cart.get(booking_key, {}).get(product_key, {}).get('quantity', 0)

        # Verificar no pasarse del stock permitido por pedido
        if (prod_quantity_cart + 1) > product.quantity:
            return JsonResponse({
                "success": False,
                "message": f'No puedes agregar más de {product.quantity} unidades de "{product.name}" por pedido.'
            }, status=400)

        # Actualizar el carrito de la sesión
        cart.setdefault(booking_key, {}).setdefault(product_key, {"quantity": 0})
        cart[booking_key][product_key]["quantity"] += 1

        # Guardar cambios en la sesión
        request.session['cart'] = cart
        request.session.modified = True

        # Calculo el subtotal producto
        subtotal = product.price * cart[booking_key][product_key]["quantity"]

        # Calcular el total carrito
        items, total_cart = get_cart_products_by_booking(request.session, booking_selected_id)

        return JsonResponse({
            "success": True,
            "message": f'Se agregó "{product.name}" al pedido.',
            "product_id": product.id,
            "quantity": cart[booking_key][product_key]["quantity"],
            "subtotal": subtotal,
            "total_cart": total_cart
        })
        

class AddComboToOrderView(LoginRequiredMixin, View):
    def post(self, request, pk):
        combo = get_object_or_404(Combo, pk=pk)
        booking_selected_id = request.session.get('booking_selected_id')

        if not booking_selected_id:
            return redirect('make_order')

        cart = request.session.get('cart', {})
        booking_key = str(booking_selected_id)
        combo_key = f"combo_{combo.id}"  # prefijo para distinguir combos de productos

        if booking_key not in cart:
            cart[booking_key] = {}

        if combo_key in cart[booking_key]:
            cart[booking_key][combo_key]['quantity'] += 1
        else:
            cart[booking_key][combo_key] = {'quantity': 1}

        request.session['cart'] = cart
        request.session.modified = True

        return redirect(f"{reverse('menu_app:menu')}#combo-{combo.id}")

class RemoveComboFromCartView(LoginRequiredMixin, View):
    def post(self, request, pk):
        combo = get_object_or_404(Combo, pk=pk)
        booking_selected_id = request.session.get('booking_selected_id')

        if not booking_selected_id:
            return redirect('make_order')

        cart = request.session.get('cart', {})
        booking_key = str(booking_selected_id)
        combo_key = f"combo_{combo.id}"

        if booking_key in cart and combo_key in cart[booking_key]:
            cart[booking_key][combo_key]['quantity'] -= 1

            if cart[booking_key][combo_key]['quantity'] <= 0:
                del cart[booking_key][combo_key]

            if not cart[booking_key]:
                del cart[booking_key]

            request.session['cart'] = cart
            request.session.modified = True

            messages.success(request, f"Se quitó una unidad de '{combo.name}' del carrito.")

        return redirect('make_order')


class DecrementFromCartView(LoginRequiredMixin, View):
    def post(self, request, pk):
        from menu_app.utils.cart import get_cart_products_by_booking

        product = get_object_or_404(Product, pk=pk)
        booking_selected_id = request.session.get('booking_selected_id')

        cart = request.session.get('cart', {})
        booking_key = str(booking_selected_id)
        product_key = str(product.id)

        product_quantity = None
        product_removed = False
        product_subtotal = 0

        if booking_key in cart and product_key in cart[booking_key]:
            cart[booking_key][product_key]['quantity'] -= 1

            # Eliminar si la cantidad es 0 o menos
            if cart[booking_key][product_key]['quantity'] <= 0:
                del cart[booking_key][product_key]
                product_removed = True
            else:
                product_quantity = cart[booking_key][product_key]['quantity']
                product_subtotal = product_quantity * product.price

            # Si ya no hay productos en la reserva, quitar la reserva del carrito
            if not cart[booking_key]:
                del cart[booking_key]

            request.session['cart'] = cart
            request.session.modified = True

         # Recalcular el carrito actualizado
        carrito_reserva, total_cart = get_cart_products_by_booking(request.session, booking_selected_id)
        
        return JsonResponse({
            "success": True,
            "message": f'Se quitó una unidad de "{product.name}" del pedido.',
            "product_id": product.id,
            "quantity": product_quantity,            # None si fue eliminado
            "product_removed": product_removed,      # True si ya no está en el carrito
            "subtotal": product_subtotal,            # Subtotal del producto actualizado
            "total_cart": total_cart,                # Total recalculado
            "cart_empty": len(carrito_reserva) == 0  # True si ya no quedan productos
        })

class DeleteFromCartView(LoginRequiredMixin, View):
    def post(self, request, pk):
        from menu_app.utils.cart import get_cart_products_by_booking

        product = get_object_or_404(Product, pk=pk)
        booking_selected_id = request.session.get('booking_selected_id')

        cart = request.session.get('cart', {})
        booking_key = str(booking_selected_id)
        product_key = str(product.id)

        if booking_key in cart and product_key in cart[booking_key]:
            del cart[booking_key][product_key]

            # Si ya no hay productos en la reserva, la quito del carrito
            if not cart[booking_key]:
                del cart[booking_key]

            request.session['cart'] = cart
            request.session.modified = True

        # Recalcular el carrito actualizado
        carrito_reserva, total_cart = get_cart_products_by_booking(request.session, booking_selected_id)

        return JsonResponse({
            "success": True,
            "message": f'Se eliminó "{product.name}" del pedido.',
            "product_id": product.id,
            "total_cart": total_cart,
            "cart_empty": len(carrito_reserva) == 0  # True si ya no quedan productos
        })


class ConfirmOrderView(LoginRequiredMixin, View):
    def post(self, request):
        booking_selected_id = request.session.get('booking_selected_id')
        if not booking_selected_id:
            messages.warning(request, "Debe seleccionar una reserva para confirmar un pedido.")
            return redirect('make_order')

        cart = request.session.get('cart', {})
        booking_selected_cart = cart.get(str(booking_selected_id), {})

        if not booking_selected_cart:
            messages.warning(request, "El carrito está vacío.")
            return redirect('make_order')

        # Crear la orden
        booking_obj = get_object_or_404(Booking, id=booking_selected_id)
        order = Order.objects.create(
            user=request.user,
            booking=booking_obj,
            buyDate=now().date(),
            amount=0.00,  # se inicializa en 0, se calculará después
            state='S'
            # El código se generará automáticamente en el método save de Order
        )

        total = 0
        for item_key, data in booking_selected_cart.items():
            quantity = data.get('quantity', 1)

            if item_key.startswith('combo_'):
                # Es un combo
                try:
                    combo_id = int(item_key.replace('combo_', ''))
                    combo = get_object_or_404(Combo, id=combo_id)

                    order_combo = OrderContainsCombo.objects.create(
                        order=order,
                        combo=combo,
                        quantity=quantity,
                    )

                    order_combo.refresh_from_db()
                    total += order_combo.subtotal

                except (ValueError, Combo.DoesNotExist):
                    continue  # Ignora si hay algún problema

            else:
                # Es un producto
                try:
                    product_id = int(item_key)
                    product = get_object_or_404(Product, id=product_id)

                    product.save()

                    order_product = OrderContainsProduct.objects.create(
                        order=order,
                        product=product,
                        quantity=quantity,
                    )

                    order_product.refresh_from_db()
                    total += order_product.subtotal

                except (ValueError, Product.DoesNotExist):
                    continue

        order.amount = total
        order.save()

        # Limpiar el carrito para esa reserva
        cart.pop(str(booking_selected_id), None)
        request.session['cart'] = cart
        request.session.modified = True

        messages.success(request, f'Pedido confirmado. Código: {order.code}')
        return redirect('bookings_app:my_reservation')
    
#vistas para añadir producto y combo desde make_order
class AddToOrderFromMakeOrderView(LoginRequiredMixin, View):
    def post(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        booking_selected_id = request.session.get('booking_selected_id')

        if not booking_selected_id:
            return redirect('make_order')

        cart = request.session.get('cart', {})
        booking_key = str(booking_selected_id)
        product_key = str(product.id)

        prod_quantity_cart = cart.get(booking_key, {}).get(product_key, {}).get('quantity', 0)

        if product.quantity <= prod_quantity_cart:
            messages.warning(request, f"No hay stock suficiente para agregar más unidades de '{product.name}'.")
            return redirect('make_order')

        if booking_key not in cart:
            cart[booking_key] = {}

        if product_key in cart[booking_key]:
            cart[booking_key][product_key]['quantity'] += 1
        else:
            cart[booking_key][product_key] = {'quantity': 1}

        request.session['cart'] = cart
        request.session.modified = True

        return redirect('make_order')

class AddComboToOrderFromMakeOrderView(LoginRequiredMixin, View):
    def post(self, request, pk):
        combo = get_object_or_404(Combo, pk=pk)
        booking_selected_id = request.session.get('booking_selected_id')

        if not booking_selected_id:
            return redirect('make_order')

        cart = request.session.get('cart', {})
        booking_key = str(booking_selected_id)
        combo_key = f"combo_{combo.id}"

        if booking_key not in cart:
            cart[booking_key] = {}

        if combo_key in cart[booking_key]:
            cart[booking_key][combo_key]['quantity'] += 1
        else:
            cart[booking_key][combo_key] = {'quantity': 1}

        request.session['cart'] = cart
        request.session.modified = True

        return redirect('make_order')

#Vistas para eliminar todos los producto o combo del carrito
class RemoveProductFromCartView(LoginRequiredMixin, View):
    def post(self, request, pk):
        booking_selected_id = request.session.get('booking_selected_id')
        if not booking_selected_id:
            return redirect('make_order')

        cart = request.session.get('cart', {})
        booking_key = str(booking_selected_id)
        product_key = str(pk)

        if booking_key in cart and product_key in cart[booking_key]:
            del cart[booking_key][product_key]  # Eliminar todas las unidades del producto

            # Si no queda nada en la reserva, la quitamos
            if not cart[booking_key]:
                del cart[booking_key]

            request.session['cart'] = cart
            request.session.modified = True

            messages.success(request, "Producto eliminado completamente del carrito.")

        return redirect('make_order')

class RemoveComboAllFromCartView(LoginRequiredMixin, View):
    def post(self, request, pk):
        booking_selected_id = request.session.get('booking_selected_id')
        if not booking_selected_id:
            return redirect('make_order')

        cart = request.session.get('cart', {})
        booking_key = str(booking_selected_id)
        combo_key = f"combo_{pk}"

        if booking_key in cart and combo_key in cart[booking_key]:
            del cart[booking_key][combo_key]  # Eliminar todas las unidades del combo

            if not cart[booking_key]:
                del cart[booking_key]

            request.session['cart'] = cart
            request.session.modified = True

            messages.success(request, "Combo eliminado completamente del carrito.")

        return redirect('make_order')
