from menu_app.models import Product

def get_cart_items_and_total(session, booking_id):
    cart = session.get('cart', {})
    items = []
    total = 0

    products_data = cart.get(str(booking_id), {})
    for product_id, data in products_data.items():
        try:
            product = Product.objects.get(id=product_id)
            quantity = data['quantity']
            subtotal = product.price * quantity
            total += subtotal
            items.append({
                'product': product,
                'quantity': quantity,
                'subtotal': subtotal
            })
        except Product.DoesNotExist:
            continue

    return items, total
