from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Sum, Q
from django.utils import timezone
from datetime import datetime, date, timedelta

from core.models import Branch, StaffProfile

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    error = None
    if request.method == 'POST':
        u_name = request.POST.get('username')
        p_word = request.POST.get('password')
        user = authenticate(request, username=u_name, password=p_word)
        if user is not None:
            if hasattr(user, 'profile') and user.profile.status == 'inactive':
                error = "Your account is deactivated. Please contact admin."
            else:
                login(request, user)
                return redirect('dashboard')
        else:
            error = "Invalid username or password"
            
    return render(request, 'login.html', {'error': error})

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def dashboard_view(request):
    user_profile = getattr(request.user, 'profile', None)
    is_admin = user_profile.is_admin if user_profile else request.user.is_superuser
    
    today = timezone.now().date()
    branches = Branch.objects.filter(status='active')

    context = {
        'today': today,
        'branches': branches,
        'is_admin': is_admin,
    }

    return render(request, 'dashboard.html', context)


# --- BRANCH MANAGEMENT ---
@login_required
def branch_list_view(request):
    if not request.user.profile.is_admin:
        messages.error(request, "Permission denied.")
        return redirect('dashboard')
        
    branches = Branch.objects.all()
    return render(request, 'branches/branch_list.html', {'branches': branches})

@login_required
def branch_create_view(request):
    if not request.user.profile.is_admin:
        messages.error(request, "Permission denied.")
        return redirect('dashboard')

    if request.method == 'POST':
        name = request.POST.get('name')
        address = request.POST.get('address', '')
        phone = request.POST.get('phone', '')

        if not name:
            messages.error(request, "Branch name is required.")
        else:
            Branch.objects.create(name=name, address=address, phone=phone)
            messages.success(request, f"Branch '{name}' created successfully.")
            return redirect('branch_list')

    return render(request, 'branches/branch_form.html', {'title': 'Add New Branch'})

@login_required
def branch_edit_view(request, pk):
    if not request.user.profile.is_admin:
        messages.error(request, "Permission denied.")
        return redirect('dashboard')

    branch = get_object_or_404(Branch, pk=pk)

    if request.method == 'POST':
        branch.name = request.POST.get('name')
        branch.address = request.POST.get('address', '')
        branch.phone = request.POST.get('phone', '')
        branch.save()
        messages.success(request, f"Branch '{branch.name}' updated successfully.")
        return redirect('branch_list')

    return render(request, 'branches/branch_form.html', {'branch': branch, 'title': f'Edit Branch: {branch.name}'})

@login_required
def branch_delete_view(request, pk):
    if not request.user.profile.is_admin:
        messages.error(request, "Permission denied.")
        return redirect('dashboard')

    branch = get_object_or_404(Branch, pk=pk)
    branch_name = branch.name
    branch.delete()
    messages.success(request, f"Branch '{branch_name}' deleted successfully.")
    return redirect('branch_list')


# --- STAFF MANAGEMENT ---
@login_required
def staff_list_view(request):
    if not request.user.profile.is_admin:
        messages.error(request, "Permission denied.")
        return redirect('dashboard')

    staff_members = StaffProfile.objects.select_related('user', 'branch').all()
    return render(request, 'staff/staff_list.html', {'staff_members': staff_members})

@login_required
def staff_create_view(request):
    if not request.user.profile.is_admin:
        messages.error(request, "Permission denied.")
        return redirect('dashboard')

    branches = Branch.objects.filter(status='active')

    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email', '')
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        password = request.POST.get('password')
        role = request.POST.get('role', 'STAFF')
        branch_id = request.POST.get('branch_id')
        phone = request.POST.get('phone', '')

        if User.objects.filter(username=username).exists():
            messages.error(request, f"Username '{username}' is already taken.")
        else:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            branch = Branch.objects.filter(id=branch_id).first() if branch_id else None
            StaffProfile.objects.create(
                user=user,
                role=role,
                branch=branch,
                phone=phone,
                status='active'
            )
            messages.success(request, f"Staff '{username}' created successfully.")
            return redirect('staff_list')

    return render(request, 'staff/staff_form.html', {'branches': branches, 'title': 'Add New Staff'})

@login_required
def staff_edit_view(request, pk):
    if not request.user.profile.is_admin:
        messages.error(request, "Permission denied.")
        return redirect('dashboard')

    profile = get_object_or_404(StaffProfile.select_related('user'), pk=pk)
    branches = Branch.objects.filter(status='active')

    if request.method == 'POST':
        user = profile.user
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.email = request.POST.get('email', '')
        
        new_password = request.POST.get('password')
        if new_password and new_password.strip():
            user.set_password(new_password)
        user.save()

        profile.role = request.POST.get('role', 'STAFF')
        branch_id = request.POST.get('branch_id')
        profile.branch = Branch.objects.filter(id=branch_id).first() if branch_id else None
        profile.phone = request.POST.get('phone', '')
        profile.status = request.POST.get('status', 'active')
        profile.save()

        messages.success(request, f"Staff '{user.username}' updated successfully.")
        return redirect('staff_list')

    return render(request, 'staff/staff_form.html', {'profile': profile, 'branches': branches, 'title': f'Edit Staff: {profile.user.username}'})

@login_required
def staff_toggle_view(request, pk):
    if not request.user.profile.is_admin:
        messages.error(request, "Permission denied.")
        return redirect('dashboard')

    profile = get_object_or_404(StaffProfile, pk=pk)
    profile.status = 'inactive' if profile.status == 'active' else 'active'
    profile.save()
    messages.success(request, f"Staff '{profile.user.username}' status updated to {profile.status.upper()}.")
    return redirect('staff_list')
