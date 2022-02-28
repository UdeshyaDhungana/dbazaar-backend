from math import perm, prod
from rest_framework import permissions

from store.models import Product


class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_staff)


class IsProductOwner(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, product):
        return product.owner.user == request.user


class IsCommentor(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, comment):
        return comment.commentor.user == request.user


class IsBidder(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, bid):
        return bid.customer.user == request.user


class IsItemOwner(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, bid):
        return request.user and bid.product.owner.user == request.user


class NotIsItemOwner(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        pk = view.kwargs['product_pk']
        product = Product.objects.get(pk=pk)
        return bool(request.user and request.user.is_authenticated and product.owner.user != request.user)

    def has_object_permission(self, request, view, bid):
        return request.user and bid.product.owner.user != request.user
