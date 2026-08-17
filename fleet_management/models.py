from django.db import models
from django.contrib.auth.models import User

class Warehouse(models.Model):
    name = models.CharField(max_length=100)
    address = models.TextField()
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)

    def __str__(self):
        return self.name

class Vehicle(models.Model):
    VEHICLE_TYPES = (
        ('TRUCK', 'Truck'),
        ('VAN', 'Van'),
        ('MOTORCYCLE', 'Motorcycle'),
    )
    license_plate = models.CharField(max_length=20, unique=True)
    capacity = models.DecimalField(max_digits=10, decimal_places=2, help_text="Capacity in kg")
    vehicle_type = models.CharField(max_length=20, choices=VEHICLE_TYPES)

    def __str__(self):
        return f"{self.license_plate} ({self.get_vehicle_type_display()})"

class Driver(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    vehicle = models.OneToOneField(Vehicle, on_delete=models.SET_NULL, null=True, blank=True, related_name='driver')

    def __str__(self):
        return self.name
