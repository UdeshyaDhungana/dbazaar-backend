from django.db import models
from django.core.validators import MinValueValidator

# Create your models here.
class Collection(models.Model):
    name = models.CharField(max_length=255)
    # WARNING: 'Product' is used as name in the class below; don't change the string
    featured_product = models.ForeignKey('Product', on_delete=models.SET_NULL, null=True, related_name='+')
    # + means that don't create reverse relationship 

    def __str__(self)->str:
        return self.name


class Product(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField()
    description = models.TextField(null=True, blank=True)
    unit_price = models.DecimalField(max_digits=6, decimal_places=2, validators=[
        MinValueValidator(1)
    ])
    inventory = models.IntegerField(validators=[
        MinValueValidator(0)
    ])
    last_update = models.DateTimeField(auto_now=True)
    collection = models.ForeignKey(Collection, on_delete=models.PROTECT)
    # related name is the attribute that appears in promotion table, instead of product_set, 
    # which is the default choice for django
    promotions = models.ManyToManyField('Promotion', related_name='products', blank=True)

    def __str__(self)->str:
        return self.title

    class Meta:
        ordering = ['title']

class Customer(models.Model):
    MEMBERSHIP_BRONZE = 'B'
    MEMBERSHIP_SILVER = 'S'
    MEMBERSHIP_GOLD = 'G'
    MEMBERSHIP_CHOICES = [
        (MEMBERSHIP_BRONZE, "Bronze"),
        (MEMBERSHIP_SILVER, "Silver"),
        (MEMBERSHIP_GOLD, "Gold"),
    ]
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15)
    birthday = models.DateField(null=True)
    membership = models.CharField(choices=MEMBERSHIP_CHOICES, max_length=2, default=MEMBERSHIP_BRONZE)
    
    def __str__(self):
        return self.first_name + ' ' + self.last_name


class Address(models.Model):
    street = models.CharField(max_length=255)
    city = models.CharField(max_length=255)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    zip_code = models.CharField(max_length=16, null=True)


class Order(models.Model):
    STATUS_PENDING = 'P'
    STATUS_COMPLETE = 'C'
    STATUS_FAILED = 'F'
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_COMPLETE, "Complete"),
        (STATUS_FAILED, "Failed"),
    ]
    placed_at = models.DateTimeField(auto_now_add=True)
    payment_status = models.CharField(choices=STATUS_CHOICES, max_length=2, default=STATUS_PENDING)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT)


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.PROTECT)
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveSmallIntegerField()
    unit_price = models.DecimalField(max_digits=6, decimal_places=2)


class Cart(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveSmallIntegerField()


class Promotion(models.Model):
    description = models.CharField(max_length=255)
    discount = models.FloatField()
    # since the actual object is important, we describe this many-to-many relationship
    # inside product class: See product class