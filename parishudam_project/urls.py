from django.contrib import admin
from django.urls import path, include

from core.views import (
    login_view, logout_view, dashboard_view,
    branch_list_view, branch_create_view, branch_edit_view, branch_delete_view,
    staff_list_view, staff_create_view, staff_edit_view, staff_toggle_view
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

    # API
    path('api/', include('api.urls')),
]

