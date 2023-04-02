from rest_framework import status
from rest_framework.permissions import BasePermission


class IsManager(BasePermission):
    message = "You don't have right permission to perfom this action."
    status = status.HTTP_403_FORBIDDEN

    def has_permission(self, request, view):
        return request.user.groups.filter(name="manager").exists()


class IsCustomer(BasePermission):
    message = "You don't have right permission to perform this action."
    status = status.HTTP_403_FORBIDDEN

    def has_permission(self, request, view):
        return request.user.groups.filter(name="customer").exists()


class IsDeliveryCrew(BasePermission):
    message = "You don't have right permission to perform this action."
    status = status.HTTP_403_FORBIDDEN

    def has_permission(self, request, view):
        return request.user.groups.filter(name="delivery_crew").exists()
