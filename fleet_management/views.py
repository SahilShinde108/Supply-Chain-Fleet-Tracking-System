from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.views import LoginView
from django.contrib.auth import logout, login
from django.contrib import messages
from django.db.models import Q
from django.core.exceptions import ValidationError
from .models import Warehouse, Vehicle, Driver, Route, Shipment, ShipmentStatusLog
from .forms import (
    WarehouseForm, VehicleForm, DriverForm, SignUpForm,
    RouteForm, ShipmentForm, ShipmentStatusUpdateForm
)

# Check user role (Dispatcher, Manager, or Superuser)
def is_dispatcher_or_manager(user):
    if user.is_superuser:
        return True
    return user.groups.filter(name__in=['DISPATCHER', 'MANAGER']).exists()

class CustomLoginView(LoginView):
    template_name = 'fleet_management/login.html'
    redirect_authenticated_user = True

def signup_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            role = form.cleaned_data.get('role', '').title()
            messages.success(request, f"Welcome to LogiTrack, {user.username}! Your {role} account has been registered.")
            return redirect('dashboard')
    else:
        form = SignUpForm()

    return render(request, 'fleet_management/signup.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('login')

@login_required
def dashboard(request):
    tab = request.GET.get('tab', 'shipments')
    status_filter = request.GET.get('status', '')
    query = request.GET.get('q', '').strip()

    warehouses = Warehouse.objects.all()
    vehicles = Vehicle.objects.all()
    drivers = Driver.objects.all()
    routes = Route.objects.all().select_related('origin_warehouse', 'destination_warehouse', 'driver', 'vehicle').prefetch_related('shipments')

    shipments_qs = Shipment.objects.all().select_related('origin_warehouse', 'route', 'route__driver', 'route__vehicle').order_by('-created_at')

    # Apply filters
    if status_filter:
        shipments_qs = shipments_qs.filter(status=status_filter)
    if query:
        shipments_qs = shipments_qs.filter(
            Q(tracking_number__icontains=query) |
            Q(title__icontains=query) |
            Q(recipient_name__icontains=query) |
            Q(destination_address__icontains=query)
        )

    driver_profile = None
    driver_assigned_routes = []
    if hasattr(request.user, 'driver'):
        driver_profile = request.user.driver
        driver_assigned_routes = routes.filter(driver=driver_profile)

    can_manage = is_dispatcher_or_manager(request.user)

    context = {
        'active_tab': tab,
        'status_filter': status_filter,
        'query': query,
        'shipments': shipments_qs,
        'routes': routes,
        'warehouses': warehouses,
        'vehicles': vehicles,
        'drivers': drivers,
        'shipment_count': Shipment.objects.count(),
        'route_count': routes.count(),
        'processing_count': Shipment.objects.filter(status='PROCESSING').count(),
        'dispatched_count': Shipment.objects.filter(status='DISPATCHED').count(),
        'in_transit_count': Shipment.objects.filter(status='IN_TRANSIT').count(),
        'delivered_count': Shipment.objects.filter(status='DELIVERED').count(),
        'warehouse_count': warehouses.count(),
        'vehicle_count': vehicles.count(),
        'driver_count': drivers.count(),
        'driver_profile': driver_profile,
        'driver_assigned_routes': driver_assigned_routes,
        'can_manage': can_manage,
    }
    return render(request, 'fleet_management/dashboard.html', context)


# ==========================================
# --- Shipment Views & State Transitions ---
# ==========================================

@login_required
@user_passes_test(is_dispatcher_or_manager)
def add_shipment(request):
    if request.method == 'POST':
        form = ShipmentForm(request.POST)
        if form.is_valid():
            shipment = form.save()
            messages.success(request, f"Shipment #{shipment.tracking_number} created successfully with status 'Processing'.")
            return redirect(f'/?tab=shipments')
    else:
        form = ShipmentForm()
    return render(request, 'fleet_management/form_page.html', {'form': form, 'title': 'Create New Shipment', 'active_tab': 'shipments'})

@login_required
def shipment_detail(request, pk):
    shipment = get_object_or_404(Shipment.objects.select_related('origin_warehouse', 'route', 'route__driver', 'route__vehicle'), pk=pk)
    logs = shipment.status_logs.select_related('changed_by').all()
    allowed_transitions = shipment.get_allowed_transitions()
    can_manage = is_dispatcher_or_manager(request.user)

    # Check if driver is assigned to this shipment's route
    is_assigned_driver = False
    if hasattr(request.user, 'driver') and shipment.route and shipment.route.driver == request.user.driver:
        is_assigned_driver = True

    can_update_status = can_manage or is_assigned_driver

    context = {
        'shipment': shipment,
        'logs': logs,
        'allowed_transitions': allowed_transitions,
        'can_manage': can_manage,
        'can_update_status': can_update_status,
        'active_tab': 'shipments',
    }
    return render(request, 'fleet_management/shipment_detail.html', context)

@login_required
def update_shipment_status(request, pk):
    shipment = get_object_or_404(Shipment, pk=pk)
    if request.method == 'POST':
        target_status = request.POST.get('target_status')
        notes = request.POST.get('notes', '').strip()

        try:
            shipment.transition_to(target_status, user=request.user, notes=notes)
            messages.success(request, f"Shipment #{shipment.tracking_number} transitioned to '{shipment.get_status_display()}'.")
        except ValidationError as e:
            messages.error(request, str(e.message if hasattr(e, 'message') else e))

    return redirect('shipment_detail', pk=shipment.pk)

@login_required
@user_passes_test(is_dispatcher_or_manager)
def edit_shipment(request, pk):
    shipment = get_object_or_404(Shipment, pk=pk)
    if request.method == 'POST':
        form = ShipmentForm(request.POST, instance=shipment)
        if form.is_valid():
            form.save()
            messages.success(request, f"Shipment #{shipment.tracking_number} updated.")
            return redirect('shipment_detail', pk=shipment.pk)
    else:
        form = ShipmentForm(instance=shipment)
    return render(request, 'fleet_management/form_page.html', {'form': form, 'title': f'Edit Shipment #{shipment.tracking_number}', 'active_tab': 'shipments'})

@login_required
@user_passes_test(is_dispatcher_or_manager)
def delete_shipment(request, pk):
    shipment = get_object_or_404(Shipment, pk=pk)
    if request.method == 'POST':
        tracking = shipment.tracking_number
        shipment.delete()
        messages.info(request, f"Shipment #{tracking} was deleted.")
        return redirect('/?tab=shipments')
    return render(request, 'fleet_management/confirm_delete.html', {'object': shipment, 'type': 'Shipment', 'active_tab': 'shipments'})

@login_required
def track_shipment_lookup(request):
    tracking_query = request.GET.get('tracking', '').strip()
    if tracking_query:
        shipment = Shipment.objects.filter(tracking_number__iexact=tracking_query).first()
        if shipment:
            return redirect('shipment_detail', pk=shipment.pk)
        else:
            messages.warning(request, f"No shipment found with tracking code '{tracking_query}'.")
    return redirect('/?tab=shipments')


# ==========================================
# --- Route Views ---
# ==========================================

@login_required
@user_passes_test(is_dispatcher_or_manager)
def add_route(request):
    if request.method == 'POST':
        form = RouteForm(request.POST)
        if form.is_valid():
            route = form.save()
            messages.success(request, f"Route '{route.name}' ({route.route_code}) created.")
            return redirect('/?tab=routes')
    else:
        form = RouteForm()
    return render(request, 'fleet_management/form_page.html', {'form': form, 'title': 'Create New Route', 'active_tab': 'routes'})

@login_required
def route_detail(request, pk):
    route = get_object_or_404(Route.objects.select_related('origin_warehouse', 'destination_warehouse', 'driver', 'vehicle').prefetch_related('shipments'), pk=pk)
    shipments = route.shipments.all().order_by('-created_at')
    can_manage = is_dispatcher_or_manager(request.user)

    # Capacity percentage
    capacity_pct = 0
    if route.vehicle and route.vehicle.capacity > 0:
        capacity_pct = min(100, int((route.total_weight / route.vehicle.capacity) * 100))

    context = {
        'route': route,
        'shipments': shipments,
        'capacity_pct': capacity_pct,
        'can_manage': can_manage,
        'active_tab': 'routes',
    }
    return render(request, 'fleet_management/route_detail.html', context)

@login_required
@user_passes_test(is_dispatcher_or_manager)
def edit_route(request, pk):
    route = get_object_or_404(Route, pk=pk)
    if request.method == 'POST':
        form = RouteForm(request.POST, instance=route)
        if form.is_valid():
            form.save()
            messages.success(request, f"Route '{route.route_code}' updated.")
            return redirect('route_detail', pk=route.pk)
    else:
        form = RouteForm(instance=route)
    return render(request, 'fleet_management/form_page.html', {'form': form, 'title': f'Edit Route: {route.route_code}', 'active_tab': 'routes'})

@login_required
@user_passes_test(is_dispatcher_or_manager)
def delete_route(request, pk):
    route = get_object_or_404(Route, pk=pk)
    if request.method == 'POST':
        code = route.route_code
        route.delete()
        messages.info(request, f"Route '{code}' was removed.")
        return redirect('/?tab=routes')
    return render(request, 'fleet_management/confirm_delete.html', {'object': route, 'type': 'Route', 'active_tab': 'routes'})


# ==========================================
# --- Warehouse CRUD ---
# ==========================================

@login_required
@user_passes_test(is_dispatcher_or_manager)
def add_warehouse(request):
    if request.method == 'POST':
        form = WarehouseForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Warehouse added.")
            return redirect('/?tab=warehouses')
    else:
        form = WarehouseForm()
    return render(request, 'fleet_management/form_page.html', {'form': form, 'title': 'Add Warehouse', 'active_tab': 'warehouses'})

@login_required
@user_passes_test(is_dispatcher_or_manager)
def edit_warehouse(request, pk):
    warehouse = get_object_or_404(Warehouse, pk=pk)
    if request.method == 'POST':
        form = WarehouseForm(request.POST, instance=warehouse)
        if form.is_valid():
            form.save()
            messages.success(request, f"Warehouse '{warehouse.name}' updated.")
            return redirect('/?tab=warehouses')
    else:
        form = WarehouseForm(instance=warehouse)
    return render(request, 'fleet_management/form_page.html', {'form': form, 'title': f'Edit Warehouse: {warehouse.name}', 'active_tab': 'warehouses'})

@login_required
@user_passes_test(is_dispatcher_or_manager)
def delete_warehouse(request, pk):
    warehouse = get_object_or_404(Warehouse, pk=pk)
    if request.method == 'POST':
        warehouse.delete()
        messages.info(request, f"Warehouse '{warehouse.name}' deleted.")
        return redirect('/?tab=warehouses')
    return render(request, 'fleet_management/confirm_delete.html', {'object': warehouse, 'type': 'Warehouse', 'active_tab': 'warehouses'})


# ==========================================
# --- Vehicle CRUD ---
# ==========================================

@login_required
@user_passes_test(is_dispatcher_or_manager)
def add_vehicle(request):
    if request.method == 'POST':
        form = VehicleForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Vehicle registered.")
            return redirect('/?tab=vehicles')
    else:
        form = VehicleForm()
    return render(request, 'fleet_management/form_page.html', {'form': form, 'title': 'Add Vehicle', 'active_tab': 'vehicles'})

@login_required
@user_passes_test(is_dispatcher_or_manager)
def edit_vehicle(request, pk):
    vehicle = get_object_or_404(Vehicle, pk=pk)
    if request.method == 'POST':
        form = VehicleForm(request.POST, instance=vehicle)
        if form.is_valid():
            form.save()
            messages.success(request, f"Vehicle '{vehicle.license_plate}' updated.")
            return redirect('/?tab=vehicles')
    else:
        form = VehicleForm(instance=vehicle)
    return render(request, 'fleet_management/form_page.html', {'form': form, 'title': f'Edit Vehicle: {vehicle.license_plate}', 'active_tab': 'vehicles'})

@login_required
@user_passes_test(is_dispatcher_or_manager)
def delete_vehicle(request, pk):
    vehicle = get_object_or_404(Vehicle, pk=pk)
    if request.method == 'POST':
        vehicle.delete()
        messages.info(request, f"Vehicle '{vehicle.license_plate}' deleted.")
        return redirect('/?tab=vehicles')
    return render(request, 'fleet_management/confirm_delete.html', {'object': vehicle, 'type': 'Vehicle', 'active_tab': 'vehicles'})


# ==========================================
# --- Driver CRUD ---
# ==========================================

@login_required
@user_passes_test(is_dispatcher_or_manager)
def add_driver(request):
    if request.method == 'POST':
        form = DriverForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Driver registered.")
            return redirect('/?tab=drivers')
    else:
        form = DriverForm()
    return render(request, 'fleet_management/form_page.html', {'form': form, 'title': 'Register Driver', 'active_tab': 'drivers'})

@login_required
@user_passes_test(is_dispatcher_or_manager)
def edit_driver(request, pk):
    driver = get_object_or_404(Driver, pk=pk)
    if request.method == 'POST':
        form = DriverForm(request.POST, instance=driver)
        if form.is_valid():
            form.save()
            messages.success(request, f"Driver '{driver.name}' updated.")
            return redirect('/?tab=drivers')
    else:
        form = DriverForm(instance=driver)
    return render(request, 'fleet_management/form_page.html', {'form': form, 'title': f'Edit Driver: {driver.name}', 'active_tab': 'drivers'})

@login_required
@user_passes_test(is_dispatcher_or_manager)
def delete_driver(request, pk):
    driver = get_object_or_404(Driver, pk=pk)
    if request.method == 'POST':
        driver.delete()
        messages.info(request, f"Driver '{driver.name}' deleted.")
        return redirect('/?tab=drivers')
    return render(request, 'fleet_management/confirm_delete.html', {'object': driver, 'type': 'Driver', 'active_tab': 'drivers'})

