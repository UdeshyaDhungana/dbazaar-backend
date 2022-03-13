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
            response = requests.get('http://localhost:8080/item/owner/ac269a3d09dcef4b9ccffbde67335f5c2a9d55814c2d204a88f047b02a4c3fa4')
            if 'item_owner' in response.json().keys() and request.user.public_key_hash == response.json()['item_owner']:
                serializer = self.get_serializer(data=request.data)
                serializer.is_valid(raise_exception=True)
                self.perform_create(serializer)
                headers = self.get_success_headers(serializer.data)
                return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
            return Response({ 'error': 'Item not registered under the provided user\'s address' }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({ 'error': 'An unknown error occured' }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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
            signedToken = int(request.data.get('signed_token'), 16)
            payload = {
                "token": str(originalToken),
                "signed_token": "63fd4019550dc76cee65a90d91cad2482131a42422696b1c7a04fe8869170cdf50d271ff1132bce4316ffc97e0b7eaf56a7fe7dcd655c8404a1e7c00ff6b98e2e15869f4fdc383d4d6f25154b5fffe5972a372a046e3d09008b2bd3d52907a1d52c12a12046b946c7f7f59059b85c6dad38ba18fa0d59edaef1b20801eb52ee4c0fe29396da2e0f95f0726ae8e9ca4d9673fa1b0b4d7b69611acb366633fe06231afad2ef9c7c3decb9e88265da60d9e1baa306fe84c630b04cd1e04c2805320ede5ee7c803628df204661556f733c7ff9a897e856b3ba7c3f8fa2cef558e695f995cb7d993c6a1f91246af76991dae9f74347b91321be5be883aaabcf1c6f4d",
                "public_key": "30820122300d06092a864886f70d01010105000382010f003082010a0282010100ac355e3e57cd9c74a64a01a23049047d9633836b21d194817bf3a1d3fbdb33e5206e7a0dddb0640422fe98668026b992cdc84cc4911ccfc202ac5126e3995cc3d552bf8be73f9653bc5d6a4911adfc206a4f4eafad8f3e9dc14329ab643283820f724f466585da991cbc0ad9ffb2c45e545b372970b0adeb87d6add022f34483c5c41579582a15d71734cc97dd2345f2efd9843b5006006a2a14755174ab2e33249951d488c6943c8faeffaebd3799b8c197ab675ce4b81ea67a8d72ab1499afea612982446e466de1f430636a7649552ac82686d100dfe40f1bc72dc0c97db5eabdd6fa001eb03279f859f62bf33a6e926b0942beb22bd96c8ba25603594c650203010001"
            }
            response = requests.post('http://localhost:8080/token/verify', json=payload)
            if 'verified' in response.json().keys():
                user = User.objects.get(pk=request.user.id)
                user.verified = True
                user.save()
                return Response({ 'success': 'User Verified Successfully '}, status=status.HTTP_202_ACCEPTED)
            else:
                raise Response({ 'error': 'Token could not be verified '}, status=status.HTTP_400_BAD_REQUEST)
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

        product = Product.objects.get(pk=product_id)
        serializer = ProductSerializer(product)
        return Response(serializer.data, status=status.HTTP_200_OK)
