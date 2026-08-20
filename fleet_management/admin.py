from django.contrib import admin
from .models import Warehouse, Vehicle, Driver, Route, Shipment, ShipmentStatusLog, RouteStop

class ShipmentStatusLogInLine(admin.TabularInline):
    model = ShipmentStatusLog
    extra = 0
    readonly_fields = ('from_status', 'to_status', 'changed_by', 'timestamp', 'notes')
    can_delete = False

class RouteStopInline(admin.TabularInline):
    model = RouteStop
    extra = 1
    fields = ('stop_number', 'shipment', 'status', 'instructions')
    ordering = ('stop_number',)

@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = ('name', 'address', 'latitude', 'longitude')
    search_fields = ('name', 'address')

@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ('license_plate', 'vehicle_type', 'capacity')
    list_filter = ('vehicle_type',)
    search_fields = ('license_plate',)

@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'vehicle', 'user')
    search_fields = ('name', 'phone')

@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    list_display = ('route_code', 'name', 'origin_warehouse', 'destination_warehouse', 'driver', 'vehicle', 'status')
    list_filter = ('status', 'origin_warehouse')
    search_fields = ('route_code', 'name')
    inlines = [RouteStopInline]

@admin.register(RouteStop)
class RouteStopAdmin(admin.ModelAdmin):
    list_display = ('route', 'stop_number', 'shipment', 'status', 'completed_at')
    list_filter = ('status', 'route')
    search_fields = ('route__route_code', 'shipment__tracking_number', 'instructions')


@admin.register(Shipment)
class ShipmentAdmin(admin.ModelAdmin):
    list_display = ('tracking_number', 'title', 'origin_warehouse', 'recipient_name', 'weight', 'route', 'status', 'created_at')
    list_filter = ('status', 'origin_warehouse')
    search_fields = ('tracking_number', 'title', 'recipient_name', 'destination_address')
    readonly_fields = ('tracking_number', 'created_at', 'updated_at', 'delivered_at')
    inlines = [ShipmentStatusLogInLine]

@admin.register(ShipmentStatusLog)
class ShipmentStatusLogAdmin(admin.ModelAdmin):
    list_display = ('shipment', 'from_status', 'to_status', 'changed_by', 'timestamp')
    list_filter = ('to_status', 'timestamp')
    search_fields = ('shipment__tracking_number', 'notes')

