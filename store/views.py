from django.db.models import Count
from django.db.models.query import QuerySet
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.filters import SearchFilter
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from store.filters import ProductFilter
from store.pagination import DefaultPagination

from .models import Collection, OrderItem, Product, Review
from .serializers import (CollectionSerializer, ProductSerializer,
                          ReviewSerializer)


class ProductsViewSet(ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    queryset = Product.objects.all()
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = ProductFilter
    search_fields = ['title', 'description']
    pagination_class = DefaultPagination

    # def get_queryset(self):
    #     queryset = Product.objects.all()
    #     collection_id = self.request.query_params.get('collection_id')
    #     if collection_id is not None:
    #         queryset = queryset.filter(collection_id=collection_id)
    #     return queryset

    def get_serializer_context(self):
       return {'request': self.request}

    def destroy(self, request, *args, **kwargs):
        if (OrderItem.objects.filter(product_id=kwargs['pk']).count() > 0):
            return Response(
                {
                    'error':
                    "Product cannot be deleted because order item exists"
                },
                status=status.HTTP_405_METHOD_NOT_ALLOWED)
        return super().destroy(request, *args, **kwargs)


class CollectionViewSet(ModelViewSet):
    queryset = Collection.objects.annotate(products_count=Count('products')).all()
    serializer_class = CollectionSerializer

    def delete(self, request, pk):
        collection = get_object_or_404(Collection, pk=pk)
        if collection.products.count() > 0:
            return Response(
                {
                    'error':
                    'Collection cannot be deleted because it includes products'
                },
                status=status.HTTP_405_METHOD_NOT_ALLOWED)
        collection.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ReviewViewSet(ModelViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer

    def get_queryset(self):
        return Review.objects.filter(product_id=self.kwargs['product_pk'])

    def get_serializer_context(self):
        return {'product_id': self.kwargs['product_pk']}
