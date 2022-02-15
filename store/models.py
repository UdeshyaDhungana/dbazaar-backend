from django.db import models
from django.core.validators import MaxLengthValidator, MinValueValidator
from django.db.models.fields import related
from django.conf import settings
from uuid import uuid4


# Create your models here.
class Collection(models.Model):
    title = models.CharField(max_length=255)

    def __str__(self) -> str:
        return self.title


class Product(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    unit_price = models.DecimalField(max_digits=10,
                                     decimal_places=2,
                                     validators=[MinValueValidator(1)])
    last_update = models.DateTimeField(auto_now=True)
    collection = models.ForeignKey(Collection, on_delete=models.PROTECT, related_name='products')

    def __str__(self) -> str:
        return self.title

    class Meta:
        ordering = ['title']


class Customer(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    phone = models.CharField(max_length=15)
    birthday = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.user.first_name + ' ' + self.user.last_name

    def email(self):
        return self.user.email

    class Meta:
        ordering = ['user__first_name', 'user__last_name']


class Bid(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    placed_at = models.DateTimeField(auto_now_add=True)
    price = models.DecimalField(max_digits=10,
                                     decimal_places=2,
                                     validators=[MinValueValidator(1)])
    description = models.TextField()


class Cart(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)


class Speak(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    description = models.TextField()
    date = models.DateField(auto_now_add=True)
    posted_by = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)


class Reply(models.Model):
    speak = models.ForeignKey(Speak, on_delete=models.CASCADE)
    posted_by = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)