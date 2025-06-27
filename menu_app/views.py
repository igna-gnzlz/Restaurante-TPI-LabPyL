from django.urls import reverse_lazy
from django.views.generic import TemplateView, ListView, DetailView, FormView
from .models import Product, Order, OrderContainsProduct
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.timezone import now
import uuid

from .forms import AddOneForm, RemoveOneForm, DeleteItemForm, CancelOrderForm

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
    model = Product
    template_name = "menu_app/menu.html"
    context_object_name = "menu_items"

    def get_queryset(self):
        return Product.objects.all().order_by("name")

class ProductDetailView(DetailView):
    model = Product
    template_name = "menu_app/product_detail.html"
    context_object_name = "product"
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

class AddToOrderView(LoginRequiredMixin, View):
    def post(self, request, slug):
        product = get_object_or_404(Product, slug=slug)
        order, created = Order.objects.get_or_create(
            user=request.user,
            state='P',
            defaults={
                'buyDate': now().date(),
                'code': uuid.uuid4().hex[:15],
                'amount': 0.0,
            }
        )
        ocp, created_ocp = OrderContainsProduct.objects.get_or_create(
            order=order,
            product=product,
            defaults={
                'subtotal': product.price,
                'quantity': 1
            }
        )
        if not created_ocp:
            ocp.quantity += 1
            ocp.subtotal = ocp.quantity * product.price
            ocp.save()
        order.amount = sum(item.subtotal for item in order.ordercontainsproduct_set.all())
        order.save()
        return redirect("menu_app:order_detail")

class OrderDetailView(LoginRequiredMixin, TemplateView):
    template_name = 'menu_app/my_order.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order = Order.objects.filter(
            user=self.request.user,
            state='P'
        ).prefetch_related('ordercontainsproduct_set__product').first()
        context['order'] = order
        return context

class MyOrdersListView(LoginRequiredMixin, ListView):
    model = Order
    template_name = 'menu_app/my_orders.html'
    context_object_name = 'orders'

    def get_queryset(self):
        # Solo pedidos completados (ajusta el estado si usas otro)
        return Order.objects.filter(user=self.request.user, state='C').order_by('-buyDate')

class ClearOrdersHistoryView(LoginRequiredMixin, View):
    def post(self, request):
        Order.objects.filter(user=request.user, state='C').delete()
        return redirect('menu_app:my_orders')