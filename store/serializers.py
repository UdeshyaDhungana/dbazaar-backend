from decimal import Decimal
from rest_framework import serializers
from .models import Cart, CartItem, Collection, Product, Review


class CollectionSerializer(serializers.ModelSerializer):
    # id = serializers.IntegerField()
    # title = serializers.CharField(max_length=255)
    class Meta:
        model = Collection
        fields = ['id', 'title', 'products_count']

    # we have to define this because products_count is not a field of collection table
    products_count = serializers.IntegerField(read_only=True)


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = [
            'id', 'title', 'description', 'slug', 'inventory', 'unit_price',
            'price_with_tax', 'collection'
        ]

    price_with_tax = serializers.SerializerMethodField('calculate_tax')
    collection = serializers.PrimaryKeyRelatedField(
        queryset=Collection.objects.all())

    # collection = serializers.StringRelatedField()
    # collection = serializers.HyperlinkedRelatedField(
    #     queryset=Collection.objects.all(),
    #     view_name='collection-detail'
    # )
    # collection = CollectionSerializer()
    def calculate_tax(self, product: Product):
        return product.unit_price * Decimal(1.1)


class SimpleProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'title', 'unit_price']


class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ['id', 'date', 'name', 'description', 'product']

    def create(self, validated_data):
        product_id = self.context['product_id']
        return Review.objects.create(product_id=product_id, **validated_data)


class CartItemSerializer(serializers.ModelSerializer):
    product = SimpleProductSerializer()
    total_price = serializers.SerializerMethodField()
    class Meta:
        model = CartItem
        fields = ['id', 'product', 'quantity', 'total_price']

    def get_total_price(self, cartItem: CartItem):
        return (cartItem.quantity * cartItem.product.unit_price)


class AddCartItemSerializer(serializers.ModelSerializer):
    product_id = serializers.IntegerField()
    class Meta:
        model = CartItem
        fields = ['id', 'product_id', 'quantity']

    def validate_product_id(self, value):
        if not Product.objects.filter(pk=value).exists():
            raise serializers.ValidationError("No product with given id was found")
        return value

    def save(self, **kwargs):
        product_id = self.validated_data['product_id']
        quantity = self.validated_data['quantity']
        cart_id = self.context['cart_id']
        try:
            cart_item = CartItem.objects.get(cart_id=cart_id, product_id=product_id)
            cart_item.quantity += quantity
            cart_item.save()
            self.instance = cart_item
        except:
            self.instance = CartItem.objects.create(cart_id=cart_id, **self.validated_data)
        return self.instance


class EditCartItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartItem
        fields = ['quantity']


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
        return sum([item.quantity * item.product.unit_price for item in cart.items.all()])