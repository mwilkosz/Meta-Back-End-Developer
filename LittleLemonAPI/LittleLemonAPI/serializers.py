from django.contrib.auth.models import User
from rest_framework import serializers, status
from rest_framework.validators import UniqueTogetherValidator

from .models import Cart, Category, MenuItem, Order, OrderItem


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["email", "id", "username"]


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "title"]


class MenuItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = MenuItem
        fields = ["id", "title", "price", "category", "featured"]


class CartSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Cart
        fields = ["user", "menuitem", "quantity", "unit_price", "price"]
        read_only_fields = ["unit_price", "price"]
        validators = [
            UniqueTogetherValidator(
                queryset=Cart.objects.all(),
                fields=["user", "menuitem"],
                message="Item is already in the cart.",
            )
        ]

    def validate(self, attrs):
        if attrs["quantity"] <= 0:
            raise serializers.ValidationError(
                detail="Quantity cannot be 0 or less than 0."
            )
        return attrs

    def create(self, validated_data):
        validated_data["unit_price"] = validated_data["menuitem"].price
        validated_data["price"] = (
            validated_data["unit_price"] * validated_data["quantity"]
        )
        return super().create(validated_data)


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ["id", "user", "delivery_crew", "status", "total", "date"]
        read_only_fields = ["user", "total", "date"]

    def create(self, validated_data):
        user = self.context["request"].user

        if not Cart.objects.filter(user=user).exists():
            raise serializers.ValidationError(
                detail="Cart is empty", code=status.HTTP_400_BAD_REQUEST
            )

        carts = Cart.objects.filter(user=user)
        total = sum([cart.price for cart in carts])
        order = Order.objects.create(user=user, total=total)

        order_items = []
        for cart in carts:
            order_item = OrderItem(
                order=order,
                menuitem=cart.menuitem,
                quantity=cart.quantity,
                unit_price=cart.unit_price,
                price=cart.price,
            )
            order_items.append(order_item)

        OrderItem.objects.bulk_create(order_items)
        carts.delete()

        return order


class OrderItemSerializer(serializers.ModelSerializer):
    menuitem = serializers.StringRelatedField()

    class Meta:
        model = OrderItem
        fields = ["menuitem", "quantity", "unit_price", "price"]
