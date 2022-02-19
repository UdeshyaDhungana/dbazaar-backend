from urllib import request

from django.db.models import Count
from django.db.models.query import QuerySet
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.mixins import (CreateModelMixin, DestroyModelMixin,
                                   RetrieveModelMixin, UpdateModelMixin)
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet, ModelViewSet
from rest_framework import permissions

from store.filters import ProductFilter
from store.pagination import DefaultPagination
from store.permissions import IsAdminOrReadOnly, IsCommentor, IsProductOwner

from .models import Collection, Customer, Product, Comment
from .serializers import (CollectionSerializer, CommentSerializer, CreateCommentSerializer, CreateProductSerializer,
                          CustomerSerializer, ProductSerializer,)


class CollectionViewSet(ModelViewSet):
    queryset = Collection.objects.annotate(
        products_count=Count('products')).all()
    serializer_class = CollectionSerializer
    permission_classes = [IsAdminOrReadOnly]

    def delete(self, request, pk):
        collection = get_object_or_404(Collection, pk=pk)
        if collection.products.count() > 0:
            return Response(
                {
                    'error': 'Collection cannot be deleted because it includes products'
                },
                status=status.HTTP_405_METHOD_NOT_ALLOWED)
        collection.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProductsViewSet(ModelViewSet):
    serializer_class = ProductSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = ProductFilter
    search_fields = ['title', 'description']
    pagination_class = DefaultPagination

    def get_serializer_class(self):
        if self.request.method in permissions.SAFE_METHODS:
            return ProductSerializer
        return CreateProductSerializer

    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            return [AllowAny()]
        elif self.request.method == 'POST':
            return [IsAuthenticated()]
        else:
            return [IsProductOwner()]

    def get_queryset(self):
        queryset = Product.objects.filter(visible=True)
        collection_id = self.request.query_params.get('collection_id')
        if collection_id is not None:
            queryset = queryset.filter(
                collection_id=collection_id, visible=True)
        return queryset

    def get_serializer_context(self):
        return {'user': self.request.user}



class CustomerViewSet(CreateModelMixin, RetrieveModelMixin, UpdateModelMixin, GenericViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer

    @action(detail=False, methods=['GET', 'PUT'])
    def me(self, request):
        customer = Customer.objects.get(user_id=request.user.id)
        if request.method == 'GET':
            serializer = CustomerSerializer(customer)
            return Response(serializer.data)
        elif request.method == 'PUT':
            serializer = CustomerSerializer(customer, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)


class CommentViewSet(ModelViewSet):
    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            return [AllowAny()]
        elif self.request.method == 'POST':
            return [IsAuthenticated()]
        else:
            return [IsCommentor()]

    def get_serializer_class(self):
        if self.request.method in permissions.SAFE_METHODS:
            return CommentSerializer
        return CreateCommentSerializer

    def get_queryset(self):
        return Comment.objects.filter(product_id=self.kwargs['product_pk'])

    def get_serializer_context(self):
        return {
            'product_id': self.kwargs['product_pk'],
            'user': self.request.user,
        }

# class CartViewSet(CreateModelMixin, RetrieveModelMixin, DestroyModelMixin,
#                   GenericViewSet):
#     queryset = Cart.objects.prefetch_related('items__product').all()
#     serializer_class = CartSerializer


# class CartItemViewSet(ModelViewSet):
#     # have to be in lowercase
#     http_method_names = ['get', 'post', 'delete']

#     def get_serializer_class(self):
#         if (self.request.method == "POST"):
#             return AddCartItemSerializer
#         return CartItemSerializer

#     def get_serializer_context(self):
#         return {
#             'cart_id': self.kwargs['cart_pk']
#         }

#     def get_queryset(self):
#         return CartItem.objects\
#             .select_related('product')\
#             .filter(cart_id=self.kwargs['cart_pk'])
