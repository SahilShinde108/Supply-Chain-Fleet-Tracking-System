from django import forms
from django.contrib.auth.models import User, Group
from .models import Warehouse, Vehicle, Driver, Route, Shipment

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

class SignUpForm(forms.Form):
    ROLE_CHOICES = (
        ('DISPATCHER', 'Dispatcher - Route & Fleet Coordinator'),
        ('DRIVER', 'Driver - Fleet & Transport Operator'),
        ('MANAGER', 'Manager - Logistics Operations Supervisor'),
    )

    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'class': input_css, 'placeholder': 'Choose a username', 'autocomplete': 'username'})
    )
    first_name = forms.CharField(
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={'class': input_css, 'placeholder': 'First name'})
    )
    last_name = forms.CharField(
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={'class': input_css, 'placeholder': 'Last name'})
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': input_css, 'placeholder': 'name@example.com', 'autocomplete': 'email'})
    )
    role = forms.ChoiceField(
        choices=ROLE_CHOICES,
        initial='DISPATCHER',
        widget=forms.Select(attrs={'class': input_css})
    )
    phone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={'class': input_css, 'placeholder': '+1 (555) 000-0000', 'autocomplete': 'tel'}),
        help_text="Required for Driver accounts."
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': input_css, 'placeholder': 'Create password (min 6 characters)', 'autocomplete': 'new-password'})
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': input_css, 'placeholder': 'Confirm password', 'autocomplete': 'new-password'})
    )

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("This username is already taken. Please choose another.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email address already exists.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        role = cleaned_data.get('role')
        phone = cleaned_data.get('phone')

        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', "Passwords do not match.")

        if password and len(password) < 6:
            self.add_error('password', "Password must be at least 6 characters long.")

        if role == 'DRIVER' and not phone:
            self.add_error('phone', "Phone number is required for Driver accounts.")

        return cleaned_data

    def save(self):
        username = self.cleaned_data['username']
        email = self.cleaned_data['email']
        password = self.cleaned_data['password']
        first_name = self.cleaned_data.get('first_name', '')
        last_name = self.cleaned_data.get('last_name', '')
        role = self.cleaned_data['role']
        phone = self.cleaned_data.get('phone', '')

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )

        group, _ = Group.objects.get_or_create(name=role)
        user.groups.add(group)

        if role == 'DRIVER':
            full_name = f"{first_name} {last_name}".strip() or username
            Driver.objects.create(
                user=user,
                name=full_name,
                phone=phone
            )

        return user

class RouteForm(forms.ModelForm):
    class Meta:
        model = Route
        fields = ['route_code', 'name', 'origin_warehouse', 'destination_warehouse', 'driver', 'vehicle', 'status', 'notes']
        widgets = {
            'route_code': forms.TextInput(attrs={'class': input_css, 'placeholder': 'e.g. RT-NORTH-101'}),
            'name': forms.TextInput(attrs={'class': input_css, 'placeholder': 'e.g. Downtown Metro Express Loop'}),
            'origin_warehouse': forms.Select(attrs={'class': input_css}),
            'destination_warehouse': forms.Select(attrs={'class': input_css}),
            'driver': forms.Select(attrs={'class': input_css}),
            'vehicle': forms.Select(attrs={'class': input_css}),
            'status': forms.Select(attrs={'class': input_css}),
            'notes': forms.Textarea(attrs={'class': input_css, 'rows': 2, 'placeholder': 'Optional route notes, dispatch instructions...'}),
        }

class ShipmentForm(forms.ModelForm):
    class Meta:
        model = Shipment
        fields = ['title', 'origin_warehouse', 'destination_address', 'recipient_name', 'recipient_phone', 'weight', 'route']
        widgets = {
            'title': forms.TextInput(attrs={'class': input_css, 'placeholder': 'e.g. Retail Package / Electronics Batch #12'}),
            'origin_warehouse': forms.Select(attrs={'class': input_css}),
            'destination_address': forms.Textarea(attrs={'class': input_css, 'rows': 3, 'placeholder': 'Street, Building, City, ZIP Code...'}),
            'recipient_name': forms.TextInput(attrs={'class': input_css, 'placeholder': 'e.g. Sarah Connor'}),
            'recipient_phone': forms.TextInput(attrs={'class': input_css, 'placeholder': '+1 (555) 234-5678'}),
            'weight': forms.NumberInput(attrs={'class': input_css, 'step': '0.01', 'placeholder': 'Weight in kg'}),
            'route': forms.Select(attrs={'class': input_css}),
        }

class ShipmentStatusUpdateForm(forms.Form):
    target_status = forms.ChoiceField(
        choices=Shipment.STATUS_CHOICES,
        widget=forms.Select(attrs={'class': input_css})
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': input_css, 'rows': 2, 'placeholder': 'Reason or notes for status transition...'})
    )

