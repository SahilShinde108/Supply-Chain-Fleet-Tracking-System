from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('logout/', views.logout_view, name='logout'),
    path('', views.dashboard, name='dashboard'),

    
    # Warehouse URLs
    path('add-warehouse/', views.add_warehouse, name='add_warehouse'),
    path('warehouse/<int:pk>/edit/', views.edit_warehouse, name='edit_warehouse'),
    path('warehouse/<int:pk>/delete/', views.delete_warehouse, name='delete_warehouse'),
    
    # Vehicle URLs
    path('add-vehicle/', views.add_vehicle, name='add_vehicle'),
    path('vehicle/<int:pk>/edit/', views.edit_vehicle, name='edit_vehicle'),
    path('vehicle/<int:pk>/delete/', views.delete_vehicle, name='delete_vehicle'),
    
    # Driver URLs
    path('add-driver/', views.add_driver, name='add_driver'),
    path('driver/<int:pk>/edit/', views.edit_driver, name='edit_driver'),
    path('driver/<int:pk>/delete/', views.delete_driver, name='delete_driver'),
]
