from http import HTTPStatus
from os import stat
import random
from urllib import request
import requests
from uuid import uuid1
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
from core.models import User

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

    def create(self, request, *args, **kwargs):
        productHash = request.data.get('product_hash')

        # send request data, receive pubkey hash, compare with following
        try:
            # use productHash later
            response = requests.get(
                'http://localhost:8080/item/owner/' + productHash)
            if 'item_owner' in response.json().keys() and request.user.public_key_hash == response.json()['item_owner']:
                serializer = self.get_serializer(data=request.data)
                serializer.is_valid(raise_exception=True)
                self.perform_create(serializer)
                headers = self.get_success_headers(serializer.data)
                return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
            return Response({'error': 'Item not registered under the provided user\'s address'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': 'An unknown error occured'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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

    @action(detail=True, methods=['get', 'put'])
    def visibility(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        if request.method == 'GET':
            return Response({})
        else:
            if (request.query_params.get('visible') == 'true'):
                product.visible = True
            elif (request.query_params.get('visible') == 'false'):
                product.visible = False
            else:
                return Response({})
            product.save()
            Bid.objects.filter(product=product).delete()
            Transfer.objects.filter(product=product).delete()
            product = Product.objects.get(pk=pk)
            serializer = ProductSerializer(product)
            return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    def get_serializer_context(self):
        return {'user': self.request.user}


class CustomerViewSet(CreateModelMixin, RetrieveModelMixin, UpdateModelMixin, GenericViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer

    @action(detail=False, methods=['GET', 'PUT'])
    def me(self, request):
        customer = get_object_or_404(Customer, user_id=request.user.id)
        if request.method == 'GET':
            serializer = CustomerSerializer(customer)
            return Response(serializer.data)
        elif request.method == 'PUT':
            serializer = CustomerSerializer(customer, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)

    @action(detail=False, methods=['GET'])
    def get_token(self, request):
        user = get_object_or_404(User, pk=request.user.id)
        if (user.verified):
            customer = Customer.object.get(user=user)
            serializer = CustomerSerializer(customer)
            return Response(serializer.data, status=status.HTTP_200_OK)
        user.randomString = uuid1(random.randint(0, 281474976710655))
        user.save()
        return Response({'token': user.randomString}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['POST'])
    def verify_token(self, request):
        # To be implemented
        originalToken = request.user.randomString
        publicKey = request.user.public_key
        # Make request
        try:
            signedToken = request.data.get('signed_token')
            payload = {
                "token": str(originalToken),
                "signed_token": str(signedToken),
                "public_key": publicKey,
            }
            response = requests.post(
                'http://localhost:8080/token/verify', json=payload)
            if 'verified' in response.json().keys():
                user = User.objects.get(pk=request.user.id)
                user.verified = True
                user.save()
                return Response({'success': 'User Verified Successfully '}, status=status.HTTP_202_ACCEPTED)
            else:
                raise Response(
                    {'error': 'Token could not be verified '}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': 'Some unknown error occured'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
        transfer = Transfer.objects.get(
            product=bid.product, seller=user.customer, buyer=bid.customer)
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
        productHash = transfer.product.product_hash
        # check if the transfer is done in blockchain
        response = requests.get('http://localhost:8080/item/owner/' + productHash)
        if 'item_owner' in response.json().keys() and request.user.public_key_hash == response.json()['item_owner']:
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
        else:
            return Response({ 'error': 'Error verifying from blockchain'}, status=status.HTTP_402_PAYMENT_REQUIRED);

        product = Product.objects.get(pk=product_id)
        serializer = ProductSerializer(product)
        return Response(serializer.data, status=status.HTTP_200_OK)
