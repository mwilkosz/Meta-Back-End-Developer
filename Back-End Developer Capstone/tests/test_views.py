from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from restaurant.models import Menu
from restaurant.serializers import MenuSerializer


class MenuViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        Menu.objects.create(title="Pizza", price=9.99, inventory=1)
        Menu.objects.create(title="Pasta", price=6.99, inventory=2)
        Menu.objects.create(title="Coke", price=1.99, inventory=3)

    def test_detail(self):
        response = self.client.get(reverse("/restaurant/menu/"))

        menus = Menu.objects.all()
        serializer = MenuSerializer(menus, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)
