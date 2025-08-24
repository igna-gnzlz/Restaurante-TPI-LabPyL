from menu_app.models import Product

def get_cart_products_by_booking(session, booking_id):
    cart = session.get('cart', {})
    items = []

    products_data = cart.get(str(booking_id), {})
    for product_id, data in products_data.items():
        try:
            product = Product.objects.get(id=product_id)
            quantity = data['quantity']
            subtotal = product.price * quantity
            items.append({
                'product': product,
                'quantity': quantity,
                'subtotal': subtotal
            })
        except Product.DoesNotExist:
            continue
    return items

def get_cart_total(cart_items):
    return sum(item['subtotal'] for item in cart_items)

def clear_cart(session, booking_id):
    cart = session.get('cart', {})
    if str(booking_id) in cart:
        del cart[str(booking_id)]
        session['cart'] = cart
        session.modified = True
    return session