from menu_app.models import Product, Combo

def get_cart_products_by_booking(session, booking_id):
    cart = session.get('cart', {})
    items = []

    products_data = cart.get(str(booking_id), {})
    
    for item_key, data in products_data.items():
        quantity = data.get('quantity', 1)

        # Verificar si es un combo
        if item_key.startswith('combo_'):
            try:
                combo_id = int(item_key.replace('combo_', ''))
                combo = Combo.objects.get(id=combo_id)
                subtotal = combo.price * quantity
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
                subtotal = product.price * quantity
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