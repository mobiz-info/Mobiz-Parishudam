from django.contrib import admin
from django.urls import path, include

from core.views import (
    login_view, logout_view, dashboard_view,
    branch_list_view, branch_create_view, branch_edit_view, branch_delete_view,
    staff_list_view, staff_create_view, staff_edit_view, staff_toggle_view,
    product_list_view, product_create_view, product_edit_view, product_delete_view,
    product_packing_size_list_view, product_packing_size_create_view, product_packing_size_edit_view, product_packing_size_delete_view,
    unit_list_view, unit_create_view, unit_delete_view,
    margin_list_view, margin_create_view,  margin_edit_view, margin_delete_view,
    packing_unit_list_view, packing_unit_create_view, packing_unit_edit_view, packing_unit_delete_view,
)   
from operations.views import (
    sales_entry_view, sales_list_view,
    expense_head_list_view, expense_head_create_view, expense_head_delete_view,
    vehicle_list_view, vehicle_create_view, vehicle_edit_view, vehicle_delete_view, 
    expense_list_view, expense_entry_view ,expense_edit_view, expense_delete_view, expense_vehicle_details_view,expense_export_excel_view,
     
)

from reports.views import (
    report_daily_view, report_weekly_view, report_monthly_yearly_view,
    report_daily_export_excel_view, report_weekly_export_excel_view,report_monthly_yearly_export_excel_view,
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

    path('packing-units/', packing_unit_list_view, name='packing_unit_list'),
    path('packing-units/create/', packing_unit_create_view, name='packing_unit_create'),
    path('packing-units/<int:pk>/edit/', packing_unit_edit_view, name='packing_unit_edit'),
    path('packing-units/<int:pk>/delete/', packing_unit_delete_view, name='packing_unit_delete'),

    #expense
    path('expense-heads/', expense_head_list_view, name='expense_head_list'),
    path('expense-heads/create/', expense_head_create_view, name='expense_head_create'),
    path('expense-heads/<int:pk>/delete/', expense_head_delete_view, name='expense_head_delete'),

    #margins
    path('margins/', margin_list_view, name='margin_list'),
    path('margins/create/', margin_create_view, name='margin_create'),
    path('margins/<int:pk>/edit/', margin_edit_view, name='margin_edit'),
    path('margins/<int:pk>/delete/', margin_delete_view, name='margin_delete'),

    # Operations: Sales & Expenses
    path('sales/entry/', sales_entry_view, name='sales_entry'),
    path('sales/', sales_list_view, name='sales_list'),

    #vehicles
    path('vehicles/', vehicle_list_view, name='vehicle_list'),
    path('vehicles/create/', vehicle_create_view, name='vehicle_create'),
    path('vehicles/<int:pk>/edit/', vehicle_edit_view, name='vehicle_edit'),
    path('vehicles/<int:pk>/delete/', vehicle_delete_view, name='vehicle_delete'),

    path('expenses/', expense_list_view, name='expense_list'),
    path('expenses/add/', expense_entry_view, name='expense_entry'),
    path('expenses/<int:pk>/edit/', expense_edit_view, name='expense_edit'),

    path('expense/vehicle-details/',expense_vehicle_details_view,name='expense_vehicle_details'),
    path('expenses/export-excel/', expense_export_excel_view,name='expense_export_excel'),

    #reports
    path('reports/daily-profit-loss/', report_daily_view, name='report_daily'),
    path('reports/weekly-profit-loss/', report_weekly_view, name='report_weekly'),
    path('reports/monthly-yearly-profit-loss/', report_monthly_yearly_view, name='report_monthly_yearly'),
    path('reports/daily-profit-loss/export-excel/', report_daily_export_excel_view, name='report_daily_export_excel'),
    path('reports/weekly-profit-loss/export-excel/', report_weekly_export_excel_view, name='report_weekly_export_excel'),
    path('reports/monthly-yearly-profit-loss/export-excel/', report_monthly_yearly_export_excel_view, name='report_monthly_yearly_export_excel'),

    #Api
    path('api/', include('api.urls')),
]

