from django.contrib import admin
from .models import Product, Category, Order,Combo,Rating


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
    search_fields = ['name']

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

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'category', 'price', 'quantity', 'on_promotion', 'dicount_percentage']
    list_filter = ['category']
    search_fields = ['name', 'description']
    ############ Se agrego los campos on_promotion y dicount_percentage para ser editables en la lista
    list_editable = ['on_promotion', 'dicount_percentage']
     ############ Se agrego los campos on_promotion y dicount_percentage para ser editables en la lista
    # Campos adicionales para mejor organización
    fields = ['name', 'description', 'price', 'quantity', 'category', 'image']
    
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
