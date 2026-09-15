from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import datetime, date, timedelta
from calendar import monthrange

from core.models import Branch, StaffProfile, Product, ProductPackingSize
from operations.models import DailySale, Expense

# --- DAILY P&L REPORT ---
@login_required
def report_daily_view(request):
    user_profile = getattr(request.user, 'profile', None)
    is_admin = user_profile.is_admin if user_profile else request.user.is_superuser

    date_str = request.GET.get('date')
    if date_str:
        try:
            report_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            report_date = timezone.now().date()
    else:
        report_date = timezone.now().date()

    if not is_admin and user_profile and user_profile.branch:
        selected_branch = user_profile.branch
    else:
        branch_id = request.GET.get('branch_id')
        selected_branch = Branch.objects.filter(id=branch_id).first() if branch_id else Branch.objects.filter(status='active').first()

    sales = DailySale.objects.filter(sale_date=report_date)
    expenses = Expense.objects.filter(expense_date=report_date)

    if selected_branch:
        sales = sales.filter(branch=selected_branch)
        expenses = expenses.filter(branch=selected_branch)

    sales_detail = sales.select_related('product', 'product_packing')
    expenses_detail = expenses.select_related('expense_head', 'staff')

    gross_profit = sales.aggregate(val=Sum('profit'))['val'] or 0.00
    total_expense = expenses.aggregate(val=Sum('amount'))['val'] or 0.00
    net_profit = float(gross_profit) - float(total_expense)
    total_volume_litres = sales.aggregate(val=Sum('base_quantity'))['val'] or 0.0000

    branches = Branch.objects.filter(status='active')

    return render(request, 'reports/report_daily.html', {
        'report_date': report_date,
        'selected_branch': selected_branch,
        'branches': branches,
        'sales_detail': sales_detail,
        'expenses_detail': expenses_detail,
        'gross_profit': gross_profit,
        'total_expense': total_expense,
        'net_profit': net_profit,
        'total_volume_litres': total_volume_litres,
        'is_admin': is_admin
    })


