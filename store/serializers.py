from decimal import Decimal

from django.db import transaction
from rest_framework import serializers

from .models import (Cart, CartItem, Collection, Customer, Bid,
                     Product, Speak)

from .signals import order_created


class CollectionSerializer(serializers.ModelSerializer):
    products_count = serializers.IntegerField(read_only=True)
    class Meta:
        model = Collection
        fields = ['id', 'title', 'products_count']


class ProductSerializer(serializers.ModelSerializer):
    collection = serializers.PrimaryKeyRelatedField(
        queryset=Collection.objects.all())

    class Meta:
        model = Product
        fields = [
            'id', 'title', 'description', 'unit_price', 'collection'
        ]


class SimpleProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'title', 'unit_price']


class Speak(serializers.ModelSerializer):
    class Meta:
        model = Speak
        fields = ['id', 'date', 'description', 'product', 'posted_by']

    def create(self, validated_data):
        product_id = self.context['product_id']
        posted_by_id = self.context
        print(posted_by_id)
        return Speak.objects.create(product_id=product_id, **validated_data)


class CartItemSerializer(serializers.ModelSerializer):
    product = SimpleProductSerializer()
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = ['id', 'product', 'total_price']

    def get_total_price(self, cartItem: CartItem):
        return (cartItem.product.unit_price)


class AddCartItemSerializer(serializers.ModelSerializer):
    product_id = serializers.IntegerField()

    class Meta:
        model = CartItem
        fields = ['id', 'product_id']

    # validate_field
    def validate_product_id(self, value):
        if not Product.objects.filter(pk=value).exists():
            raise serializers.ValidationError(
                "No product with given id was found")
        return value

    def save(self, **kwargs):
        cart_id = self.context['cart_id']
        self.instance = CartItem.objects.create(
                cart_id=cart_id, **self.validated_data)
        return self.instance


class CartSerializer(serializers.ModelSerializer):
    # read only because empty object while cart creation
    id = serializers.UUIDField(read_only=True)
    items = CartItemSerializer(many=True, read_only=True)
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        # in cartitem model, related_name=items is set, i.e items is a valid field of cart class
        fields = ['id', 'items', 'total_price']

    def get_total_price(self, cart):
        return sum([item.product.unit_price for item in cart.items.all()])


class CustomerSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = Customer
        fields = [
            'id',
            'user_id',
            'phone',
            'birthday',
            'membership'
        ]


class SpeakSerializer(serializers.ModelSerializer):
    class Meta:
        model = Speak
        fields = [
            'id',
            'product',
            'description'
            'posted_by',
            'date',
        ]
        
class BidSerializer(serializers.ModelSerializer):
    customer_id=serializers.IntegerField(read_only=True)

 
    class Meta:
        model= Bid
        fields=[
          'id',
          'customer_id',
          'placed_at','description',
          'price'
        ]

    def create(self,validated_data):
        customer_id=self.context['customer_id']
        return Bid.objects.create(customer_id=customer_id,**validated_data)
         
