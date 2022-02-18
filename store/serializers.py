from decimal import Decimal
import queue
from django.conf import settings

from django.db import transaction
from rest_framework import serializers
from django.contrib.auth import get_user_model

from .models import  Collection, Customer, Product
from .signals import order_created


class CustomerSerializer(serializers.ModelSerializer):
    firstname = serializers.SerializerMethodField('get_firstname')
    lastname = serializers.SerializerMethodField('get_lastname')
    
    class Meta:
        model = Customer
        fields = [
            'id',
            'user',
            'phone',
            'firstname',
            'lastname',
        ]

    def get_firstname(self, obj):
        return obj.user.first_name
    
    def get_lastname(self, obj):
        return obj.user.last_name


class CollectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Collection
        fields = ['id', 'title']


class CreateProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'title', 'description', 'unit_price', 'collection']

    def create(self, validated_data):
        user = self.context['user']
        customer = Customer.objects.get(user=user)
        return Product.objects.create(owner=customer, **validated_data)


class ProductSerializer(serializers.ModelSerializer):
    collection = CollectionSerializer()
    owner = CustomerSerializer()
    class Meta:
        model = Product
        fields = [
            'id', 'title', 'description', 'unit_price', 'collection', 'owner'
        ]


class SimpleProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'title', 'unit_price']


# class Speak(serializers.ModelSerializer):
#     class Meta:
#         model = Speak
#         fields = ['id', 'date', 'description', 'product', 'posted_by']

#     def create(self, validated_data):
#         product_id = self.context['product_id']
#         posted_by_id = self.context
#         print(posted_by_id)
#         return Speak.objects.create(product_id=product_id, **validated_data)


# class CartItemSerializer(serializers.ModelSerializer):
#     product = SimpleProductSerializer()
#     total_price = serializers.SerializerMethodField()

#     class Meta:
#         model = CartItem
#         fields = ['id', 'product', 'total_price']

#     def get_total_price(self, cartItem: CartItem):
#         return (cartItem.product.unit_price)


# class AddCartItemSerializer(serializers.ModelSerializer):
#     product_id = serializers.IntegerField()

#     class Meta:
#         model = CartItem
#         fields = ['id', 'product_id']

#     # validate_field
#     def validate_product_id(self, value):
#         if not Product.objects.filter(pk=value).exists():
#             raise serializers.ValidationError(
#                 "No product with given id was found")
#         return value

#     def save(self, **kwargs):
#         cart_id = self.context['cart_id']
#         self.instance = CartItem.objects.create(
#                 cart_id=cart_id, **self.validated_data)
#         return self.instance


# class CartSerializer(serializers.ModelSerializer):
#     # read only because empty object while cart creation
#     id = serializers.UUIDField(read_only=True)
#     items = CartItemSerializer(many=True, read_only=True)
#     total_price = serializers.SerializerMethodField()

#     class Meta:
#         model = Cart
#         # in cartitem model, related_name=items is set, i.e items is a valid field of cart class
#         fields = ['id', 'items', 'total_price']

#     def get_total_price(self, cart):
#         return sum([item.product.unit_price for item in cart.items.all()])





# class SpeakSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Speak
#         fields = [
#             'id',
#             'product',
#             'description'
#             'posted_by',
#             'date',
#         ]
