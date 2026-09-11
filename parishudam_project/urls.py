from django.contrib import admin
from django.urls import path, include

from core.views import (
    login_view, logout_view, dashboard_view,
    branch_list_view, branch_create_view, branch_edit_view, branch_delete_view,
    staff_list_view, staff_create_view, staff_edit_view, staff_toggle_view,
    product_list_view, product_create_view, product_edit_view, product_delete_view,
    product_packing_size_list_view, product_packing_size_create_view, product_packing_size_edit_view, product_packing_size_delete_view,
    unit_list_view, unit_create_view, unit_delete_view,
    expense_head_list_view, expense_head_create_view, expense_head_delete_view
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('', dashboard_view, name='dashboard'),

    # Branches
    path('branches/', branch_list_view, name='branch_list'),
    path('branches/create/', branch_create_view, name='branch_create'),
    path('branches/<int:pk>/edit/', branch_edit_view, name='branch_edit'),
    path('branches/<int:pk>/delete/', branch_delete_view, name='branch_delete'),

    # Staff
    path('staff/', staff_list_view, name='staff_list'),
    path('staff/create/', staff_create_view, name='staff_create'),
    path('staff/<int:pk>/edit/', staff_edit_view, name='staff_edit'),
    path('staff/<int:pk>/toggle/', staff_toggle_view, name='staff_toggle'),

    # Units
    path('units/', unit_list_view, name='unit_list'),
    path('units/create/', unit_create_view, name='unit_create'),
    path('units/<int:pk>/delete/', unit_delete_view, name='unit_delete'),

    # Products
    path('products/', product_list_view, name='product_list'),
    path('products/create/', product_create_view, name='product_create'),
    path('products/<int:pk>/edit/', product_edit_view, name='product_edit'),
    path('products/<int:pk>/delete/', product_delete_view, name='product_delete'),

    # Product Packing Sizes
    path('product-packing-sizes/', product_packing_size_list_view, name='product_packing_size_list'),
    path('product-packing-sizes/create/', product_packing_size_create_view, name='product_packing_size_create'),
    path('product-packing-sizes/<int:pk>/edit/', product_packing_size_edit_view, name='product_packing_size_edit'),
    path('product-packing-sizes/<int:pk>/delete/', product_packing_size_delete_view, name='product_packing_size_delete'),

    path('expense-heads/', expense_head_list_view, name='expense_head_list'),
    path('expense-heads/create/', expense_head_create_view, name='expense_head_create'),
    path('expense-heads/<int:pk>/delete/', expense_head_delete_view, name='expense_head_delete'),
    
    # API
    path('api/', include('api.urls')),
]

