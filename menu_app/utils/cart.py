from menu_app.models import Product, Combo
from decimal import Decimal

def get_cart_products_by_booking(session, booking_id):
    cart = session.get('cart', {})
    items = []
    total = Decimal("0.00")

    products_data = cart.get(str(booking_id), {})
    
    for item_key, data in products_data.items():
        quantity = data.get('quantity', 1)

        # Verificar si es un combo
        if item_key.startswith('combo_'):
            try:
                combo_id = int(item_key.replace('combo_', ''))
                combo = Combo.objects.get(id=combo_id)
                if combo.on_promotion:
                    subtotal = Decimal(combo.discounted_price) * Decimal(quantity)
                else:
                    subtotal = Decimal(combo.price) * Decimal(quantity)
                total += subtotal
                items.append({
                    'item': combo,
                    'type': 'combo',
                    'quantity': quantity,
                    'subtotal': subtotal
                })
            except (Combo.DoesNotExist, ValueError):
                continue

        else:
            # Procesar como producto
            try:
                product_id = int(item_key)
                product = Product.objects.get(id=product_id)
                if product.on_promotion:
                    subtotal = Decimal(product.discounted_price) * Decimal(quantity)
                else:
                    subtotal = Decimal(product.price) * Decimal(quantity)
                total += subtotal
                items.append({
                    'item': product,
                    'type': 'product',
                    'quantity': quantity,
                    'subtotal': subtotal
                })
            except (Product.DoesNotExist, ValueError):
                continue

    return items, total