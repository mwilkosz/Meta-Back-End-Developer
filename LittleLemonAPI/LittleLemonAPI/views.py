from django.contrib.auth.models import Group, User
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle

from .models import Cart, Category, MenuItem, Order, OrderItem
from .permissions import IsCustomer, IsDeliveryCrew, IsManager
from .serializers import (
    CartSerializer,
    CategorySerializer,
    MenuItemSerializer,
    OrderItemSerializer,
    OrderSerializer,
    UserSerializer,
)


class CategoriesView(generics.ListCreateAPIView):
    """List and create categories."""

    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    throttle_classes = [UserRateThrottle]


class CartView(generics.ListAPIView, generics.CreateAPIView):
    """
    Manage user's shopping cart.

    Allows authenticated customers to view, add, and delete items in their
    shopping cart.
    """

    queryset = Cart.objects.all()
    serializer_class = CartSerializer
    ordering_fields = ["price"]
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]

    def get_permissions(self):
        if self.request.method in ["GET", "POST", "DELETE"]:
            self.permission_classes = [IsCustomer]
        return super().get_permissions()

    def get_queryset(self):
        self.queryset = Cart.objects.filter(user=self.request.user)
        return super().get_queryset()

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        if not self.get_queryset().exists():
            return Response(
                {"message": "Cart is already empty."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        self.get_queryset().delete()

        return Response(status=status.HTTP_200_OK)


class GroupUsersView(generics.ListCreateAPIView, generics.DestroyAPIView):
    """
    Manage users in a group.

    Allows manager the creation and deletion of users in a group.
    """

    queryset = User.objects.all()
    serializer_class = UserSerializer
    group_name = ""
    throttle_classes = [UserRateThrottle]

    def get_queryset(self):
        group = Group.objects.get(name=self.group_name)

        if "pk" in self.kwargs:
            return group.user_set.filter(id=self.kwargs["pk"])
        else:
            return group.user_set.all()

    def post(self, request, *args, **kwargs):
        username = request.data.get("username")

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response(
                {"error": "User with username {} does not exist".format(username)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        group, _ = Group.objects.get_or_create(name=self.group_name)
        group.user_set.add(user)

        return Response(
            {
                "success": "User {} has been added to {} group".format(
                    username, self.group_name
                )
            },
            status=status.HTTP_201_CREATED,
        )

    def delete(self, request, pk, *args, **kwargs):
        try:
            user = User.objects.get(id=pk)
            group = Group.objects.get(name=self.group_name)

            if user in group.user_set.all():
                group.user_set.remove(user)
                return Response(
                    {
                        "success": "User {} has been removed from {} group".format(
                            user.username, self.group_name
                        )
                    },
                    status=status.HTTP_200_OK,
                )

            else:
                return Response(
                    {
                        "error": "User {} is not a member of {} group".format(
                            user.username, self.group_name
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        except User.DoesNotExist:
            return Response(
                {"error": "User with id {} does not exist".format(pk)},
                status=status.HTTP_404_NOT_FOUND,
            )


class ManagerView(GroupUsersView):
    """View manager group management."""

    group_name = "manager"


class DeliveryCrewView(GroupUsersView):
    """View delivery crew group management."""

    group_name = "delivery_crew"


class MenuItemsView(generics.ListCreateAPIView):
    """
    Manage menu items.

    Allows manager listing and creation of menu items.
    """

    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer
    ordering_fields = ["price"]
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]

    def get_permissions(self):
        if self.request.method == "POST":
            self.permission_classes = [IsManager]
        return super().get_permissions()


class OrdersView(generics.ListCreateAPIView):
    """
    Manage orders.

    Allows authenticated users to list and create orders. Permissions are set
    based on the user's group.
    """

    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    ordering_fields = ["id"]
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]

    def get_permissions(self):
        if self.request.method == "POST":
            self.permission_classes = [IsCustomer]
        return super().get_permissions()

    def get_queryset(self):
        user = self.request.user
        group = user.groups.all()

        if group.filter(name="manager").exists():
            self.queryset = Order.objects.all()

        elif group.filter(name="customer").exists():
            self.queryset = Order.objects.filter(user=user)

        elif group.filter(name="delivery_crew").exists():
            self.queryset = Order.objects.filter(delivery_crew__isnull=False)

        return super().get_queryset()

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serialized = self.get_serializer(queryset, many=True)

        for order_data in serialized.data:
            order_items = OrderItem.objects.filter(order=order_data["id"])
            order_item_serialized = OrderItemSerializer(order_items, many=True)
            order_data["order_items"] = order_item_serialized.data

        return Response(serialized.data, status=status.HTTP_200_OK)


class SingleMenuItemView(generics.RetrieveUpdateAPIView, generics.DestroyAPIView):
    """Retrieve, update and delete a single menu item."""

    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]

    def get_permissions(self):
        if self.request.method in ["PUT", "PATCH", "DELETE"]:
            self.permission_classes = [IsManager]
        return super().get_permissions()


class SingleOrderView(
    generics.ListAPIView, generics.RetrieveUpdateAPIView, generics.DestroyAPIView
):
    """Retrieve, update and delete a single order item."""

    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    throttle_classes = [UserRateThrottle]

    def get_permissions(self):
        if self.request.method in ["GET"]:
            self.permission_classes = [IsCustomer | IsManager | IsDeliveryCrew]

        elif self.request.method in ["PATCH"]:
            self.permission_classes = [IsManager | IsDeliveryCrew]

        elif self.request.method in ["DELETE"]:
            self.permission_classes = [IsManager]

        return super().get_permissions()

    def get_queryset(self):
        user = self.request.user
        group = user.groups.all()

        if group.filter(name="manager").exists():
            self.queryset = Order.objects.all()

        elif group.filter(name="customer").exists():
            self.queryset = Order.objects.filter(user=user)

        elif group.filter(name="delivery_crew").exists():
            self.queryset = Order.objects.all()

        return super().get_queryset()

    def list(self, request, *args, **kwargs):
        order_id = kwargs.get("pk")
        queryset = self.filter_queryset(self.get_queryset())

        try:
            order = queryset.get(id=order_id)
        except Order.DoesNotExist:
            return Response(
                {"message": "Order not found"}, status=status.HTTP_404_NOT_FOUND
            )

        serialized = self.get_serializer(order)
        serialized_data = serialized.data
        order_items = OrderItem.objects.filter(order=order_id)
        order_item_serialized = OrderItemSerializer(order_items, many=True)
        serialized_data["order_items"] = order_item_serialized.data

        return Response(serialized_data, status=status.HTTP_200_OK)
