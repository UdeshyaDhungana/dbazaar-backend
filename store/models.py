from statistics import mode
from django.db import models
from django.core.validators import MaxLengthValidator, MinValueValidator
from django.db.models.fields import related
from django.conf import settings
from uuid import uuid4
from os import path

from playground.settings import MEDIA_ROOT


# Create your models here.
class Collection(models.Model):
    title = models.CharField(max_length=255)

    def __str__(self) -> str:
        return self.title


class Customer(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='customer')
    phone = models.CharField(max_length=15)

    def __str__(self):
        return self.user.first_name + ' ' + self.user.last_name

    def email(self):
        return self.user.email

    class Meta:
        ordering = ['user__first_name', 'user__last_name']


class Product(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    unit_price = models.DecimalField(max_digits=10,
                                     decimal_places=2,
                                     validators=[MinValueValidator(1)])
    last_update = models.DateTimeField(auto_now=True)
    collection = models.ForeignKey(Collection, on_delete=models.PROTECT, related_name='products')
    owner = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='products')
    visible = models.BooleanField(default=True)
    photo = models.ImageField(upload_to='products', default=None)
    product_hash = models.CharField(max_length=64, unique=True)

    def __str__(self) -> str:
        return self.title

    class Meta:
        ordering = ['title']


class Comment(models.Model):
    commentor = models.ForeignKey(Customer, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='comments')
    description = models.TextField()
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.description

# Later ==========================
class Bid(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='bids')
    price = models.DecimalField(max_digits=10,
                                     decimal_places=2,
                                     validators=[MinValueValidator(1)])
    description = models.TextField()
    placed_at = models.DateTimeField(auto_now_add=True)
    approved = models.BooleanField(default=False)

# Once a bid is approved, delete all other bids of that product

class Transfer(models.Model):
    completed = models.BooleanField(default=False)
    buyer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name='incoming_transfers')
    seller = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name='outgoing_transfers')
    product = models.OneToOneField(Product, on_delete=models.PROTECT, related_name='transfer')