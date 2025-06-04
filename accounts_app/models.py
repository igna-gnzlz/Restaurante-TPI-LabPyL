from django.db import models

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

class Rating(models.Model):
    title = models.CharField(max_length=15)
    text = models.TextField()
    rating = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    product = models.ForeignKey('menu_app.Product', on_delete=models.CASCADE)
    user = models.ForeignKey('User', on_delete=models.CASCADE)

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
        self.rating = rating or self.rating

        self.save()