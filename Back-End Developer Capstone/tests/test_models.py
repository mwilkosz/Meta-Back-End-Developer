from django.test import TestCase

from restaurant.models import Booking, Menu


class MenuItemTest(TestCase):
    def test_get_item(self):
        item = Menu.objects.create(title="Pizza", price=10.00, inventory=10)
        self.assertEqual(item.__str__(), "Pizza : 10.0")


class BookingItemTest(TestCase):
    def test_get_item(self):
        item = Booking.objects.create(
            name="Michal", no_of_guests=1, booking_date="2023-04-17 20:00"
        )
        self.assertEqual(item.__str__(), "Michal : 2023-04-17 20:00")
