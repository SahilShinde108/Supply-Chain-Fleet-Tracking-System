from django import forms
from .models import Warehouse, Vehicle, Driver

input_css = "w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition shadow-sm text-slate-800 bg-white"

class WarehouseForm(forms.ModelForm):
    class Meta:
        model = Warehouse
        fields = ['name', 'address', 'latitude', 'longitude']
        widgets = {
            'name': forms.TextInput(attrs={'class': input_css, 'placeholder': 'e.g. Central Logistics Hub'}),
            'address': forms.Textarea(attrs={'class': input_css, 'rows': 3, 'placeholder': 'Full street address...'}),
            'latitude': forms.NumberInput(attrs={'class': input_css, 'step': '0.000001', 'placeholder': '37.774929'}),
            'longitude': forms.NumberInput(attrs={'class': input_css, 'step': '0.000001', 'placeholder': '-122.419416'}),
        }

class VehicleForm(forms.ModelForm):
    class Meta:
        model = Vehicle
        fields = ['license_plate', 'capacity', 'vehicle_type']
        widgets = {
            'license_plate': forms.TextInput(attrs={'class': input_css, 'placeholder': 'e.g. ABC-1234'}),
            'capacity': forms.NumberInput(attrs={'class': input_css, 'step': '0.01', 'placeholder': 'Capacity in kg'}),
            'vehicle_type': forms.Select(attrs={'class': input_css}),
        }

class DriverForm(forms.ModelForm):
    class Meta:
        model = Driver
        fields = ['name', 'phone', 'vehicle']
        widgets = {
            'name': forms.TextInput(attrs={'class': input_css, 'placeholder': 'Driver Full Name'}),
            'phone': forms.TextInput(attrs={'class': input_css, 'placeholder': '+1 (555) 000-0000'}),
            'vehicle': forms.Select(attrs={'class': input_css}),
        }
