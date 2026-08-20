import uuid
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone

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

class Route(models.Model):
    ROUTE_STATUS_CHOICES = (
        ('PLANNED', 'Planned'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    )
    route_code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=150)
    origin_warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='origin_routes')
    destination_warehouse = models.ForeignKey(Warehouse, on_delete=models.SET_NULL, null=True, blank=True, related_name='destination_routes')
    driver = models.ForeignKey(Driver, on_delete=models.SET_NULL, null=True, blank=True, related_name='routes')
    vehicle = models.ForeignKey(Vehicle, on_delete=models.SET_NULL, null=True, blank=True, related_name='routes')
    status = models.CharField(max_length=20, choices=ROUTE_STATUS_CHOICES, default='PLANNED')
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.route_code} - {self.name}"

    @property
    def total_weight(self):
        stop_weight = sum(s.shipment.weight for s in self.stops.all())
        if stop_weight > 0:
            return stop_weight
        return sum(shp.weight for shp in self.shipments.all())

    @property
    def is_overcapacity(self):
        if self.vehicle and self.vehicle.capacity > 0:
            return self.total_weight > self.vehicle.capacity
        return False

    @property
    def ordered_stops(self):
        return self.stops.select_related('shipment', 'shipment__origin_warehouse').order_by('stop_number')

    @property
    def completed_stops_count(self):
        return self.stops.filter(status='COMPLETED').count()

    @property
    def progress_percentage(self):
        total = self.stops.count()
        if total == 0:
            return 0
        return int((self.completed_stops_count / total) * 100)

    def add_stop(self, shipment, stop_number=None, instructions=""):
        if stop_number is None:
            max_num = self.stops.aggregate(models.Max('stop_number'))['stop_number__max']
            stop_number = (max_num or 0) + 1

        stop, created = RouteStop.objects.update_or_create(
            route=self,
            shipment=shipment,
            defaults={
                'stop_number': stop_number,
                'instructions': instructions
            }
        )
        shipment.route = self
        shipment.save()
        return stop

    def reorder_stops(self):
        for idx, stop in enumerate(self.stops.order_by('stop_number', 'id'), start=1):
            if stop.stop_number != idx:
                RouteStop.objects.filter(id=stop.id).update(stop_number=idx)


class Shipment(models.Model):
    STATUS_PROCESSING = 'PROCESSING'
    STATUS_DISPATCHED = 'DISPATCHED'
    STATUS_IN_TRANSIT = 'IN_TRANSIT'
    STATUS_DELIVERED = 'DELIVERED'
    STATUS_CANCELLED = 'CANCELLED'

    STATUS_CHOICES = (
        (STATUS_PROCESSING, 'Processing'),
        (STATUS_DISPATCHED, 'Dispatched'),
        (STATUS_IN_TRANSIT, 'In Transit'),
        (STATUS_DELIVERED, 'Delivered'),
        (STATUS_CANCELLED, 'Cancelled'),
    )

    # Strict State Machine definition
    ALLOWED_TRANSITIONS = {
        STATUS_PROCESSING: [STATUS_DISPATCHED, STATUS_CANCELLED],
        STATUS_DISPATCHED: [STATUS_IN_TRANSIT, STATUS_PROCESSING, STATUS_CANCELLED],
        STATUS_IN_TRANSIT: [STATUS_DELIVERED, STATUS_CANCELLED],
        STATUS_DELIVERED: [],
        STATUS_CANCELLED: [],
    }

    tracking_number = models.CharField(max_length=50, unique=True, editable=False)
    title = models.CharField(max_length=150, help_text="Package name / description")
    origin_warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT, related_name='origin_shipments')
    destination_address = models.TextField()
    recipient_name = models.CharField(max_length=100)
    recipient_phone = models.CharField(max_length=30)
    weight = models.DecimalField(max_digits=10, decimal_places=2, help_text="Weight in kg")
    route = models.ForeignKey(Route, on_delete=models.SET_NULL, null=True, blank=True, related_name='shipments')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PROCESSING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    delivered_at = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        if not self.tracking_number:
            self.tracking_number = f"SHP-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)
        if is_new:
            ShipmentStatusLog.objects.create(
                shipment=self,
                from_status=None,
                to_status=self.status,
                notes="Shipment created in system."
            )

    def __str__(self):
        return f"{self.tracking_number} - {self.title} ({self.get_status_display()})"

    def can_transition_to(self, target_status):
        allowed = self.ALLOWED_TRANSITIONS.get(self.status, [])
        return target_status in allowed

    def get_allowed_transitions(self):
        return self.ALLOWED_TRANSITIONS.get(self.status, [])

    def transition_to(self, target_status, user=None, notes=''):
        if not self.can_transition_to(target_status):
            status_dict = dict(self.STATUS_CHOICES)
            allowed_str = ', '.join([status_dict.get(s, s) for s in self.get_allowed_transitions()]) or 'None (Terminal state)'
            raise ValidationError(
                f"Invalid transition from '{status_dict.get(self.status, self.status)}' to '{status_dict.get(target_status, target_status)}'. Allowed transitions: {allowed_str}."
            )

        old_status = self.status
        self.status = target_status
        if target_status == self.STATUS_DELIVERED and not self.delivered_at:
            self.delivered_at = timezone.now()
        self.save()

        ShipmentStatusLog.objects.create(
            shipment=self,
            from_status=old_status,
            to_status=target_status,
            changed_by=user,
            notes=notes or f"Status changed from {dict(self.STATUS_CHOICES).get(old_status)} to {dict(self.STATUS_CHOICES).get(target_status)}."
        )

class ShipmentStatusLog(models.Model):
    shipment = models.ForeignKey(Shipment, on_delete=models.CASCADE, related_name='status_logs')
    from_status = models.CharField(max_length=20, choices=Shipment.STATUS_CHOICES, blank=True, null=True)
    to_status = models.CharField(max_length=20, choices=Shipment.STATUS_CHOICES)
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.shipment.tracking_number}: {self.from_status} -> {self.to_status} at {self.timestamp.strftime('%Y-%m-%d %H:%M')}"

class RouteStop(models.Model):
    STOP_STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('ARRIVED', 'Arrived'),
        ('COMPLETED', 'Completed'),
        ('SKIPPED', 'Skipped'),
    )
    route = models.ForeignKey(Route, on_delete=models.CASCADE, related_name='stops')
    shipment = models.ForeignKey(Shipment, on_delete=models.CASCADE, related_name='route_stops')
    stop_number = models.PositiveIntegerField(help_text="Sequence order of the stop (1, 2, 3...)")
    status = models.CharField(max_length=20, choices=STOP_STATUS_CHOICES, default='PENDING')
    estimated_arrival = models.DateTimeField(blank=True, null=True)
    actual_arrival = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    instructions = models.CharField(max_length=255, blank=True, null=True, help_text="Special delivery instructions for driver")

    class Meta:
        ordering = ['stop_number', 'id']
        unique_together = ('route', 'shipment')

    def __str__(self):
        return f"Stop #{self.stop_number} on {self.route.route_code}: {self.shipment.tracking_number}"


    def mark_arrived(self):
        self.status = 'ARRIVED'
        self.actual_arrival = timezone.now()
        self.save()

    def mark_completed(self, user=None):
        self.status = 'COMPLETED'
        self.completed_at = timezone.now()
        self.save()
        if self.shipment.can_transition_to(Shipment.STATUS_DELIVERED):
            self.shipment.transition_to(Shipment.STATUS_DELIVERED, user=user, notes=f"Delivered at Route Stop #{self.stop_number}")


