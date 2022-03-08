from http import HTTPStatus
from urllib import request
from django.db import DatabaseError, transaction
from django.db.models import Count
from django.http import Http404
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import permissions, status
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.mixins import (CreateModelMixin,
                                   RetrieveModelMixin, UpdateModelMixin)
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet, ModelViewSet

from store.filters import ProductFilter
from store.pagination import DefaultPagination
from store.permissions import (IsAdminOrReadOnly, IsBidder, IsBuyer, IsCommentor,
                               IsItemOwner, IsProductOwner, NotIsItemOwner)

from .models import Bid, Collection, Comment, Customer, Product, Transfer
from .serializers import (ApproveBidSerializer, ApproveTransferSerializer, BidSerializer,
                          CollectionSerializer, CommentSerializer,
                          CreateBidSerializer, CreateCommentSerializer,
                          CreateProductSerializer, CustomerSerializer,
                          ProductSerializer, TransferSerializer)


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
        queryset = Product.objects.filter().prefetch_related('collection', 'owner__user')
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
    http_method_names = ['get', 'post', 'put', 'delete']

    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            return [AllowAny()]
        elif self.request.method == 'POST':
            return [IsAuthenticated()]
        return [IsCommentor()]

    def get_serializer_class(self):
        if self.request.method in permissions.SAFE_METHODS:
            return CommentSerializer
        return CreateCommentSerializer

    def get_queryset(self):
        return Comment.objects.filter(product_id=self.kwargs['product_pk']).order_by('-date').prefetch_related('commentor__user', 'product')

    def get_serializer_context(self):
        return {
            'product_id': self.kwargs['product_pk'],
            'user': self.request.user,
        }


class BidViewSet(ModelViewSet):
    http_method_names = ['get', 'post', 'put', 'delete']

    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            return [IsAuthenticated(), ]
        elif self.request.method == 'POST':
            return [NotIsItemOwner()]
        elif self.request.method == 'PUT':
            return [IsItemOwner()]
        return [IsBidder()]

    def get_serializer_class(self):
        if self.request.method in permissions.SAFE_METHODS:
            return BidSerializer
        elif self.request.method == "PUT":
            return ApproveBidSerializer
        return CreateBidSerializer

    def get_queryset(self):
        return Bid.objects.filter(product_id=self.kwargs['product_pk']).order_by('-placed_at').prefetch_related('customer__user', 'product')

    def get_serializer_context(self):
        return {
            'product_id': self.kwargs['product_pk'],
            'user': self.request.user,
        }

    def update(self, request, *args, **kwargs):
        bid = get_object_or_404(Bid, pk=self.kwargs['pk'])
        user = request.user
        try:
            with transaction.atomic():
                transfer = Transfer.objects.create(
                    product=bid.product, seller=user.customer, buyer=bid.customer)
                product = Product.objects.get(pk=bid.product.id)
                product.visible = False
                bid.approved = True
                transfer.save()
                product.save()
                bid.save()
        except (DatabaseError):
            return Response(
                {
                    "error": "Internal Server Error while performing transaction"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        transfer = Transfer.objects.get(product=bid.product, seller=user.customer, buyer=bid.customer)
        serializer = TransferSerializer(transfer)
        return Response({'data': serializer.data, }, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            if (instance.approved):
                return Response({'error': "Cannot delete approved bid"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
            self.perform_destroy(instance=instance)
        except Http404:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)


class TransferViewset(ModelViewSet):
    http_method_names = ['get', 'put']

    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            return [IsAuthenticated()]
        return [IsBuyer()]

    def get_queryset(self):
        user = self.request.user
        myPurchaseTransfers = Transfer.objects.filter(buyer=user.customer)
        mySalesTransfers = Transfer.objects.filter(seller=user.customer)
        return myPurchaseTransfers | mySalesTransfers

    def get_serializer_class(self):
        if self.request.method == 'PUT':
            return ApproveTransferSerializer
        return TransferSerializer

    def update(self, request, *args, **kwargs):
        transfer = get_object_or_404(Transfer, pk=self.kwargs['pk'])
        product_id = transfer.product.id
        try:
            with transaction.atomic():
                product = Product.objects.get(pk=product_id)
                product.owner = transfer.buyer
                product.save()
                transfer.delete()
                # Delete related bids
                bids = Bid.objects.filter(product=transfer.product)
                bids.delete()
        except DatabaseError:
            return Response({'error': 'Internal Server Error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        serializer = ProductSerializer(Product.objects.get(pk=product_id))
        if serializer.is_valid():
            return Response({"product": serializer.validated_data}, status=status.HTTP_200_OK)
        return Response({'error': 'An unkonwn error occured'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
