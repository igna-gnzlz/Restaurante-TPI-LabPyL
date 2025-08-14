from django.db import models

class Product(models.Model):
    name = models.CharField(max_length=20,default="")
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.IntegerField() # stock
    image = models.ImageField(upload_to="products/", null=True, blank=True)
    # El diagrama solo permite una category (pero queda a elección nuestra permitir varias)
    category = models.ForeignKey('Category', on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return self.name
    
    @classmethod
    def validate(cls, name, description, price):
        errors = {}

        if name == "":
            errors["name"] = "Por favor ingrese un nombre"

        if description == "":
            errors["description"] = "Por favor ingrese una descripción"

        if price <= 0:
            errors["price"] = "Por favor ingrese un precio mayor a 0"

        return errors

    @classmethod
    def new(cls, name, description, price, quantity, image):
        errors = Product.validate(name, description, price)

        if len(errors.keys()) > 0:
            return False, errors

        Product.objects.create(
            name=name,
            description=description,
            price=price,
            quantity=quantity,
            image=image 
        )

        return True, None

    def update(self, name, description, price, quantity):
        self.name = name or self.name
        self.description = description or self.description
        self.price = price or self.price
        self.quantity = quantity or self.quantity

        self.save()

class Category(models.Model):
    name = models.CharField(max_length=20)
    description = models.TextField()
    isActive = models.BooleanField(default=True)

    def __str__(self):
        return self.name
    
    @classmethod
    def validate(cls, name, description):
        errors = {}

        if name == "":
            errors["name"] = "Por favor ingrese un nombre"

        if description == "":
            errors["description"] = "Por favor ingrese una descripción"

        return errors
    
    @classmethod
    def new(cls, name, description):
        errors = Category.validate(name, description)

        if len(errors.keys()) > 0:
            return False, errors

        Category.objects.create(
            name=name,
            description=description,
        )

        return True, None
    
    def update(self, name, description, isActive=None):
        if isActive is not None:
            self.isActive = isActive
        self.name = name or self.name
        self.description = description or self.description

        self.save()

class Order(models.Model):
    STATE_CHOICES = [
        ('S','Solicitado por cliente'),
        ('P','Preparación'),
        ('E','Enviado'),
        ('R','Recibido'),
        ('C','Cancelado')
    ]
    buyDate = models.DateField()
    code = models.CharField(max_length=15, unique=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    state = models.CharField(max_length=15, choices=STATE_CHOICES, default='S')
    user = models.ForeignKey('accounts_app.User', on_delete=models.CASCADE, related_name='menu_orders')
    booking = models.ForeignKey('bookings_app.Booking', on_delete=models.CASCADE, null=True, blank=True, related_name='orders')

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = self._generate_unique_code()
        super().save(*args, **kwargs)
    
    def _generate_unique_code(self):
        """Genera un código único con reintentos para evitar colisiones"""
        max_attempts = 10
        for _ in range(max_attempts):
            code = self.generate_order_code()
            if not Order.objects.filter(code=code).exists():
                return code
        raise ValueError("No se pudo generar un código único después de 10 intentos")
    
    def generate_order_code(self):
        import uuid
        """Genera un código corto y único basado en UUID"""
        short_uuid = str(uuid.uuid4()).replace('-', '')[:8].upper()
        return f'PDD-{short_uuid}'

    def __str__(self):
        return f"Pedido {self.code} - {self.user.username}"

class OrderContainsProduct(models.Model):
    order = models.ForeignKey('Order', on_delete=models.CASCADE)
    product = models.ForeignKey('Product', on_delete=models.CASCADE, null=True)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    quantity = models.PositiveIntegerField(default=1)

    def save(self, *args, **kwargs):
        self.subtotal = self.product.price * self.quantity
        super().save(*args, **kwargs)

class Rating(models.Model):
    title = models.CharField(max_length=15)
    text = models.TextField()
    rating = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    product = models.ForeignKey('menu_app.Product', on_delete=models.CASCADE)
    user = models.ForeignKey('accounts_app.User', on_delete=models.CASCADE)

    def __str__(self):
        return self.title
    
    @classmethod
    def validate(cls, title, text, rating):
        errors = {}

        if title == "":
            errors["title"] = "Por favor ingrese un título"

        if text == "":
            errors["text"] = "Por favor ingrese un comentario"

        if rating < 1 or rating > 5:
            errors["rating"] = "Por favor ingrese una calificación entre 1 y 5"

        return errors
    
    @classmethod
    def new(cls, title, text, rating, product, user):
        errors = Rating.validate(title, text, rating)

        if len(errors.keys()) > 0:
            return False, errors

        Rating.objects.create(
            title=title,
            text=text,
            rating=rating,
            product=product,
            user=user
        )

        return True, None
    
    def update(self, title, text, rating):
        self.title = title or self.title
        self.text = text or self.text
        if rating is not None:
            self.rating = rating

        self.save()