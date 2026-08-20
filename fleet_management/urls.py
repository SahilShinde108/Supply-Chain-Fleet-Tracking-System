from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('logout/', views.logout_view, name='logout'),
    path('', views.dashboard, name='dashboard'),

    # Shipment URLs
    path('shipment/add/', views.add_shipment, name='add_shipment'),
    path('shipment/<int:pk>/', views.shipment_detail, name='shipment_detail'),
    path('shipment/<int:pk>/edit/', views.edit_shipment, name='edit_shipment'),
    path('shipment/<int:pk>/delete/', views.delete_shipment, name='delete_shipment'),
    path('shipment/<int:pk>/update-status/', views.update_shipment_status, name='update_shipment_status'),
    path('track/', views.track_shipment_lookup, name='track_shipment_lookup'),

    # Route & Multi-Stop URLs
    path('route/add/', views.add_route, name='add_route'),
    path('route/<int:pk>/', views.route_detail, name='route_detail'),
    path('route/<int:pk>/edit/', views.edit_route, name='edit_route'),
    path('route/<int:pk>/delete/', views.delete_route, name='delete_route'),
    path('route/<int:route_pk>/add-stop/', views.add_route_stop, name='add_route_stop'),
    path('route/<int:route_pk>/dispatch-all/', views.dispatch_route_all, name='dispatch_route_all'),
    path('stop/<int:stop_pk>/remove/', views.remove_route_stop, name='remove_route_stop'),
    path('stop/<int:stop_pk>/move/<str:direction>/', views.move_route_stop, name='move_route_stop'),
    path('stop/<int:stop_pk>/update-status/', views.update_stop_status, name='update_stop_status'),

    # Driver Manifest & Portal URLs
    path('driver/portal/', views.driver_portal, name='driver_portal'),


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

