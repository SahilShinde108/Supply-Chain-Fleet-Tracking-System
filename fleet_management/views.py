from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.views import LoginView
from django.contrib.auth import logout
from .models import Warehouse, Vehicle, Driver
from .forms import WarehouseForm, VehicleForm, DriverForm

# Check user role (Dispatcher, Manager, or Superuser)
def is_dispatcher_or_manager(user):
    if user.is_superuser:
        return True
    return user.groups.filter(name__in=['DISPATCHER', 'MANAGER']).exists()

class CustomLoginView(LoginView):
    template_name = 'fleet_management/login.html'
    redirect_authenticated_user = True

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
@user_passes_test(is_dispatcher_or_manager)
def dashboard(request):
    tab = request.GET.get('tab', 'warehouses')
    warehouses = Warehouse.objects.all()
    vehicles = Vehicle.objects.all()
    drivers = Driver.objects.all()
    context = {
        'active_tab': tab,
        'warehouses': warehouses,
        'vehicles': vehicles,
        'drivers': drivers,
        'warehouse_count': warehouses.count(),
        'vehicle_count': vehicles.count(),
        'driver_count': drivers.count(),
    }
    return render(request, 'fleet_management/dashboard.html', context)

# --- Warehouse CRUD ---
@login_required
@user_passes_test(is_dispatcher_or_manager)
def add_warehouse(request):
    if request.method == 'POST':
        form = WarehouseForm(request.POST)
        if form.is_valid():
            form.save()
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
        return redirect('/?tab=warehouses')
    return render(request, 'fleet_management/confirm_delete.html', {'object': warehouse, 'type': 'Warehouse', 'active_tab': 'warehouses'})


# --- Vehicle CRUD ---
@login_required
@user_passes_test(is_dispatcher_or_manager)
def add_vehicle(request):
    if request.method == 'POST':
        form = VehicleForm(request.POST)
        if form.is_valid():
            form.save()
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
        return redirect('/?tab=vehicles')
    return render(request, 'fleet_management/confirm_delete.html', {'object': vehicle, 'type': 'Vehicle', 'active_tab': 'vehicles'})


# --- Driver CRUD ---
@login_required
@user_passes_test(is_dispatcher_or_manager)
def add_driver(request):
    if request.method == 'POST':
        form = DriverForm(request.POST)
        if form.is_valid():
            form.save()
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
        return redirect('/?tab=drivers')
    return render(request, 'fleet_management/confirm_delete.html', {'object': driver, 'type': 'Driver', 'active_tab': 'drivers'})
