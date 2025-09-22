from django import template
from decimal import Decimal

register = template.Library()

@register.filter
def currency_ar(value):
    if value is None or value == "":
        return "$0,00"
    
    try:
        # Asegurar que value es Decimal
        if not isinstance(value, Decimal):
            value = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return str(value)  # si no se puede convertir, lo devuelve crudo
    
    # Formatear con miles y 2 decimales
    formatted = f"${value:,.2f}"
    return formatted.replace(",", "X").replace(".", ",").replace("X", ".")