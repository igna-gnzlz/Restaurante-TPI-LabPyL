from django.contrib import admin
from .models import Product, Category, Order,Combo,Rating
#Librerias para el cálculo de precio de combo
from django.shortcuts import get_object_or_404, redirect
from django.urls import path
from django.contrib import messages
from django.urls import reverse
from django.utils.html import format_html
from django.contrib.admin.views.decorators import staff_member_required


#Vista personalizada
@staff_member_required
def calculate_combo_price_view(request, pk):
    combo = get_object_or_404(Combo, pk=pk)
    try:
        new_price = combo.CalculateComboPrice()
        combo.price = new_price
        combo.save()
        messages.success(request, f'Price calculated successfully: {new_price:.2f}')
    except ValueError as e:
        messages.warning(request, str(e))
    return redirect(f'/admin/menu_app/combo/{pk}/change/')

class MenuAdmin(admin.ModelAdmin):
    ##########Se agrego los campos on_promotion y dicount_percentage
    list_display = ("name", "description", "price", "quantity","on_promotion", "dicount_percentage")
   ############ #se agrego los campos on_promotion y dicount_percentage
    search_fields = ("name", "price")
    list_filter = ("price", "quantity")

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'isActive']
    list_filter = ['isActive']
    search_fields = ['name', 'description']

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    pass

@admin.register(Combo)
class ComboAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'price', 'list_products', 'on_promotion', 'dicount_percentage', 'is_active']
    list_editable = ['on_promotion', 'dicount_percentage', 'is_active']
    search_fields = ['name', 'description']
    filter_horizontal = ['products']
    list_filter = ['on_promotion', 'is_active']

    actions = ['activate_combos', 'deactivate_combos', 'apply_promotion', 'remove_promotion']

    def list_products(self, obj):
        return ", ".join([p.name for p in obj.products.all()])
    list_products.short_description = 'Productos'

    @admin.action(description='Habilitar combos seleccionados')
    def activate_combos(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, 'Combos habilitados correctamente.')

    @admin.action(description='Deshabilitar combos seleccionados')
    def deactivate_combos(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, 'Combos deshabilitados correctamente.')

    @admin.action(description='Aplicar promoción 20% a combos seleccionados')
    def apply_promotion(self, request, queryset):
        for combo in queryset:
            combo.setDiscount(20)  # Aplicar descuento del 20%
        self.message_user(request, 'Promoción del 20% aplicada a combos seleccionados.')

    @admin.action(description='Quitar promoción de combos seleccionados')
    def remove_promotion(self, request, queryset):
        for combo in queryset:
            combo.setPromotion(False)
        self.message_user(request, 'Promociones removidas de combos seleccionados.')

    #Actualizar precio en base a los productos
    @admin.site.admin_view
    def calculate_combo_price(self, request, pk):
        combo = get_object_or_404(Combo, pk=pk)
        try:
            new_price = combo.CalculateComboPrice()
            combo.price = new_price
            combo.save()
            self.message_user(request, f'Price calculated successfully: {new_price:.2f}', level=messages.SUCCESS)
        except ValueError as e:
            self.message_user(request, str(e), level=messages.WARNING)
        return redirect(f'../{pk}/change/')
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:pk>/calculate-price/',
                calculate_combo_price_view,
                name='combo-calculate-price',
            ),
        ]
        return custom_urls + urls
    
    readonly_fields = ['calculate_price_button']
    fields = (
        'name',
        'description',
        'products',
        'price',
        'on_promotion',
        'dicount_percentage',
        'is_active',
        'calculate_price_button',  # Aquí se muestra el botón, solo 1 vez
    )
    def calculate_price_button(self, obj):
        if not obj.pk:
            return ''
        products_list = ", ".join([p.name for p in obj.products.all()])
        url = reverse('admin:combo-calculate-price', args=[obj.pk])
        return format_html(
            '<a class="button" href="{}" onclick="return confirm(\'Are you sure you want to calculate price?\\nProducts in combo: {}\');">Calculate Average Price</a>',
            url,
            products_list
        )
    calculate_price_button.short_description = 'Calculate Price'
        

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'category', 'price', 'is_available', 'quantity', 'on_promotion', 'dicount_percentage']
    list_filter = ['category', 'is_available']
    search_fields = ['name', 'description']
    # Se agrego los campos on_promotion y dicount_percentage para ser editables en la lista
    list_editable = ['on_promotion', 'dicount_percentage']
    # Se agrego los campos on_promotion y dicount_percentage para ser editables en la lista
    # Campos adicionales para mejor organización
    fields = ['name', 'description', 'price', 'is_available','quantity', 'category', 'image']
    
    # Mostrar imagen en el admin
    readonly_fields = ['image_preview']
    
    def image_preview(self, obj):
        if obj.image:
            return f'<img src="{obj.image.url}" style="max-height: 100px; max-width: 100px;" />'
        return "No image"
    image_preview.allow_tags = True
    image_preview.short_description = 'Preview'

    ##########Se agrego el metodo save_model para validar y aplicar el descuento
    def save_model(self, request, obj, form, change):
        # Validar y aplicar descuento si on_promotion está activo
        if obj.on_promotion:
            try:
                obj.setDiscount(obj.dicount_percentage)
            except ValueError as e:
                # Si hay error, puedes manejarlo como quieras
                from django.contrib import messages
                messages.error(request, f"Error en descuento: {e}")
                return
        else:
            # Si no hay promoción, asegurarse de limpiar descuento
            obj.unSetPromotion()
        super().save_model(request, obj, form, change)

        #########Se agrego el metodo save_model para validar y aplicar el descuento

@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ('title', 'product', 'user', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('title', 'text', 'product__name', 'user__username')
