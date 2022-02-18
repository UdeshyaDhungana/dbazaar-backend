from math import perm
from rest_framework import permissions

class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_staff)
        


class IsProductOwner(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(request.user)

    def has_object_permission(self, request, view, product):
        return request.user and product.owner.user == request.user

