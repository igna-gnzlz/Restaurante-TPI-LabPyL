from django.db import models

class Product(models.Model):
    title = models.CharField(max_length=20,default="")
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.IntegerField() # stock
    image = models.ImageField(upload_to="products/", null=True, blank=True)
    # En diagrama solo permite una category
    category = models.ForeignKey('Category', on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return self.title

    @classmethod
    def validate(cls, name, description, price):
        errors = {}

        if name == "":
            errors["name"] = "Por favor ingrese un nombre"

        if description == "":
            errors["description"] = "Por favor ingrese una descripcion"

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
            image=image,
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

class Rating(models.Model):
    title = models.CharField(max_length=15)
    text = models.TextField()
    rating = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    product = models.ForeignKey('Product', on_delete=models.CASCADE)
    user = models.ForeignKey('User', on_delete=models.CASCADE)
    def __str__(self):
        return self.title

class Booking(models.Model):
    approved = models.BooleanField(default=False)
    approval_date = models.DateField(null=True, blank=True)
    code = models.CharField(max_length=15, unique=True)
    observations = models.TextField(blank=True)
    date = models.DateField()
    user = models.ForeignKey('User', on_delete=models.CASCADE)
    def __str__(self):
        return 'Booking '+self.code

class Table(models.Model):
    capacity = models.IntegerField()
    # number = models.IntegerField() #
    description = models.TextField(blank=True)
    is_reserved = models.BooleanField(default=False)
    booking = models.ForeignKey('Booking', models.SET_NULL, null=True)

    #def __str__(self):
    #    return 'Table '+self.number

class TableHasTimeSlot(models.Model):
    table = models.ForeignKey('Table', on_delete=models.SET_NULL, null=True)
    time_slot = models.ForeignKey('TimeSlot', on_delete=models.CASCADE)

class TimeSlot(models.Model):
    start = models.DateTimeField() # Consultar uso de tiempo en lugar de fecha, usar datetime?
    end = models.DateTimeField()
    is_full = models.BooleanField(default=False) # Para consultar

    #def __str__(self):
    #    return ''
    
class User(models.Model):
    username = models.CharField(max_length=15)
    email = models.EmailField()

    def __str__(self):
        return self.username

class UserRecievesNotification(models.Model):
    user = models.ForeignKey('User', on_delete=models.SET_NULL, null=True)
    notification = models.ForeignKey('Notification', on_delete=models.CASCADE)

class Notification(models.Model):
    title = models.CharField(max_length=100)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True) # date o datetime?
    is_read = models.BooleanField(default=False)

class OrderContainsProduct(models.Model):
    order = models.ForeignKey('Order', on_delete=models.CASCADE)
    product = models.ForeignKey('Product', on_delete=models.SET_NULL, null=True)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

class Order(models.Model):
    STATE_CHOICES = [
        ('P','Preparación'),
        ('E','Enviado'),
        ('R','Recibido'),
        ('C','Cancelado')
    ]
    buyDate = models.DateField()
    code = models.CharField(max_length=15, unique=True)
    amount = models.FloatField()
    state = models.CharField(max_length=15, choices=STATE_CHOICES, default='P')
    user = models.ForeignKey('User', on_delete=models.CASCADE)