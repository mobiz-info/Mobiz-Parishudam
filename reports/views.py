from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.http import HttpResponse
from django.utils import timezone
from datetime import datetime, timedelta

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill

from core.models import Branch
from operations.models import DailySale, Expense


# =========================================================
# PROFIT & LOSS REPORT
# =========================================================

@login_required
def report_daily_view(request):
    user_profile = getattr(request.user, 'profile', None)
    is_admin = (
        user_profile.is_admin
        if user_profile
        else request.user.is_superuser
    )

    today = timezone.now().date()

    # -----------------------------------------------------
    # Report type
    # -----------------------------------------------------

    report_type = request.GET.get(
        'report_type',
        'weekly'
    )

    if report_type not in [
        'weekly',
        'monthly',
        'yearly'
    ]:
        report_type = 'weekly'

    # -----------------------------------------------------
    # Branch selection
    # -----------------------------------------------------

    if not is_admin and user_profile and user_profile.branch:
        selected_branch = user_profile.branch

    else:
        branch_id = request.GET.get('branch_id')

        if branch_id:
            selected_branch = Branch.objects.filter(
                id=branch_id,
                status='active'
            ).first()
        else:
            selected_branch = None

    # -----------------------------------------------------
    # Default values
    # -----------------------------------------------------

    date_from = today
    date_to = today + timedelta(days=6)

    selected_month = today.strftime('%Y-%m')
    selected_year = str(today.year)

    # -----------------------------------------------------
    # WEEKLY
    # -----------------------------------------------------

    if report_type == 'weekly':

        date_from_str = request.GET.get('date_from')

        if date_from_str:
            try:
                date_from = datetime.strptime(
                    date_from_str,
                    '%Y-%m-%d'
                ).date()
            except ValueError:
                date_from = today

        date_to = date_from + timedelta(days=6)

    # -----------------------------------------------------
    # MONTHLY
    # -----------------------------------------------------

    elif report_type == 'monthly':

        month_str = request.GET.get('month')

        if month_str:
            try:
                selected_month_date = datetime.strptime(
                    month_str,
                    '%Y-%m'
                ).date()

                selected_month = month_str

            except ValueError:
                selected_month_date = today
                selected_month = today.strftime('%Y-%m')

        else:
            selected_month_date = today
            selected_month = today.strftime('%Y-%m')

        date_from = selected_month_date.replace(
            day=1
        )

        if date_from.month == 12:

            next_month = date_from.replace(
                year=date_from.year + 1,
                month=1,
                day=1
            )

        else:

            next_month = date_from.replace(
                month=date_from.month + 1,
                day=1
            )

        date_to = next_month - timedelta(days=1)

    # -----------------------------------------------------
    # YEARLY
    # -----------------------------------------------------

    elif report_type == 'yearly':

        year_str = request.GET.get(
            'year',
            str(today.year)
        )

        try:
            year_value = int(year_str)

        except (ValueError, TypeError):
            year_value = today.year

        selected_year = str(year_value)

        date_from = datetime(
            year_value,
            1,
            1
        ).date()

        date_to = datetime(
            year_value,
            12,
            31
        ).date()

    # -----------------------------------------------------
    # Querysets
    # -----------------------------------------------------

    sales = DailySale.objects.filter(
        sale_date__range=[
            date_from,
            date_to
        ]
    )

    expenses = Expense.objects.filter(
        expense_date__range=[
            date_from,
            date_to
        ]
    )

    # -----------------------------------------------------
    # Branch filter
    # -----------------------------------------------------

    if selected_branch:

        sales = sales.filter(
            branch=selected_branch
        )

        expenses = expenses.filter(
            branch=selected_branch
        )

    # -----------------------------------------------------
    # Summary
    # -----------------------------------------------------

    sale_profit = sales.aggregate(
        total=Sum('profit')
    )['total'] or 0

    total_expense = expenses.aggregate(
        total=Sum('amount')
    )['total'] or 0

    total_sold_volume = sales.aggregate(
        total=Sum('base_quantity')
    )['total'] or 0

    net_profit = (
        float(sale_profit)
        - float(total_expense)
    )

    # -----------------------------------------------------
    # Report rows
    # -----------------------------------------------------

    report_rows = []

    # -----------------------------------------------------
    # WEEKLY / MONTHLY - DAY WISE
    # -----------------------------------------------------

    if report_type in [
        'weekly',
        'monthly'
    ]:

        current_date = date_from

        while current_date <= date_to:

            day_sales = sales.filter(
                sale_date=current_date
            )

            day_expenses = expenses.filter(
                expense_date=current_date
            )

            row_sale_profit = day_sales.aggregate(
                total=Sum('profit')
            )['total'] or 0

            row_expense = day_expenses.aggregate(
                total=Sum('amount')
            )['total'] or 0

            row_net_profit = (
                float(row_sale_profit)
                - float(row_expense)
            )

            report_rows.append({
                'date': current_date,
                'period': current_date.strftime(
                    '%d-%b-%Y'
                ),
                'day': current_date.strftime(
                    '%A'
                ),
                'sale_profit': row_sale_profit,
                'expense': row_expense,
                'net_profit': row_net_profit,
            })

            current_date += timedelta(days=1)

    # -----------------------------------------------------
    # YEARLY - MONTH WISE
    # -----------------------------------------------------

    elif report_type == 'yearly':

        current_date = date_from

        while current_date <= date_to:

            if current_date.month == 12:

                next_month = current_date.replace(
                    year=current_date.year + 1,
                    month=1,
                    day=1
                )

            else:

                next_month = current_date.replace(
                    month=current_date.month + 1,
                    day=1
                )

            month_end = next_month - timedelta(days=1)

            if month_end > date_to:
                month_end = date_to

            month_sales = sales.filter(
                sale_date__range=[
                    current_date,
                    month_end
                ]
            )

            month_expenses = expenses.filter(
                expense_date__range=[
                    current_date,
                    month_end
                ]
            )

            row_sale_profit = month_sales.aggregate(
                total=Sum('profit')
            )['total'] or 0

            row_expense = month_expenses.aggregate(
                total=Sum('amount')
            )['total'] or 0

            row_net_profit = (
                float(row_sale_profit)
                - float(row_expense)
            )

            report_rows.append({
                'date': current_date,
                'period': current_date.strftime(
                    '%B'
                ),
                'day': str(current_date.year),
                'sale_profit': row_sale_profit,
                'expense': row_expense,
                'net_profit': row_net_profit,
            })

            current_date = next_month

    # -----------------------------------------------------
    # Branches
    # -----------------------------------------------------

    branches = Branch.objects.filter(
        status='active'
    )

    # -----------------------------------------------------
    # Years for dropdown
    # -----------------------------------------------------

    years = range(
        today.year - 5,
        today.year + 6
    )

    # -----------------------------------------------------
    # Render
    # -----------------------------------------------------

    return render(
        request,
        'reports/report_daily.html',
        {
            'report_type': report_type,
            'date_from': date_from,
            'date_to': date_to,
            'selected_month': selected_month,
            'selected_year': selected_year,
            'selected_branch': selected_branch,
            'branches': branches,
            'sale_profit': sale_profit,
            'total_expense': total_expense,
            'net_profit': net_profit,
            'total_sold_volume': total_sold_volume,
            'report_rows': report_rows,
            'is_admin': is_admin,
            'years': years,
        }
    )

@login_required
def report_daily_export_excel_view(request):
    user_profile = getattr(request.user, 'profile', None)
    is_admin = (
        user_profile.is_admin
        if user_profile
        else request.user.is_superuser
    )

    today = timezone.now().date()

    report_type = request.GET.get(
        'report_type',
        'weekly'
    )

    if report_type not in [
        'weekly',
        'monthly',
        'yearly'
    ]:
        report_type = 'weekly'

    # Branch
    if not is_admin and user_profile and user_profile.branch:
        selected_branch = user_profile.branch
    else:
        branch_id = request.GET.get('branch_id')

        if branch_id:
            selected_branch = Branch.objects.filter(
                id=branch_id,
                status='active'
            ).first()
        else:
            selected_branch = None

    # Date range
    date_from = today
    date_to = today + timedelta(days=6)

    if report_type == 'weekly':

        date_from_str = request.GET.get('date_from')

        if date_from_str:
            try:
                date_from = datetime.strptime(
                    date_from_str,
                    '%Y-%m-%d'
                ).date()
            except ValueError:
                date_from = today

        date_to = date_from + timedelta(days=6)

    elif report_type == 'monthly':

        month_str = request.GET.get('month')

        try:
            selected_month_date = datetime.strptime(
                month_str,
                '%Y-%m'
            ).date() if month_str else today
        except ValueError:
            selected_month_date = today

        date_from = selected_month_date.replace(day=1)

        if date_from.month == 12:
            next_month = date_from.replace(
                year=date_from.year + 1,
                month=1,
                day=1
            )
        else:
            next_month = date_from.replace(
                month=date_from.month + 1,
                day=1
            )

        date_to = next_month - timedelta(days=1)

    elif report_type == 'yearly':

        year_str = request.GET.get(
            'year',
            str(today.year)
        )

        try:
            year_value = int(year_str)
        except (ValueError, TypeError):
            year_value = today.year

        date_from = datetime(
            year_value,
            1,
            1
        ).date()

        date_to = datetime(
            year_value,
            12,
            31
        ).date()

    # Querysets
    sales = DailySale.objects.filter(
        sale_date__range=[date_from, date_to]
    )

    expenses = Expense.objects.filter(
        expense_date__range=[date_from, date_to]
    )

    if selected_branch:
        sales = sales.filter(
            branch=selected_branch
        )

        expenses = expenses.filter(
            branch=selected_branch
        )

    # Totals
    sale_profit = sales.aggregate(
        total=Sum('profit')
    )['total'] or 0

    total_expense = expenses.aggregate(
        total=Sum('amount')
    )['total'] or 0

    net_profit = (
        float(sale_profit)
        - float(total_expense)
    )

    # Excel workbook
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = 'P&L Report'

    sheet.append([
        'Date / Period',
        'Day',
        'Sale Profit',
        'Expense',
        'Net Profit'
    ])

    # Weekly / Monthly
    if report_type in ['weekly', 'monthly']:

        current_date = date_from

        while current_date <= date_to:

            day_sales = sales.filter(
                sale_date=current_date
            )

            day_expenses = expenses.filter(
                expense_date=current_date
            )

            day_sale_profit = day_sales.aggregate(
                total=Sum('profit')
            )['total'] or 0

            day_expense = day_expenses.aggregate(
                total=Sum('amount')
            )['total'] or 0

            day_net_profit = (
                float(day_sale_profit)
                - float(day_expense)
            )

            sheet.append([
                current_date,
                current_date.strftime('%A'),
                float(day_sale_profit),
                float(day_expense),
                float(day_net_profit)
            ])

            current_date += timedelta(days=1)

    # Yearly
    else:

        current_date = date_from

        while current_date <= date_to:

            if current_date.month == 12:

                next_month = current_date.replace(
                    year=current_date.year + 1,
                    month=1,
                    day=1
                )

            else:

                next_month = current_date.replace(
                    month=current_date.month + 1,
                    day=1
                )

            month_end = next_month - timedelta(days=1)

            if month_end > date_to:
                month_end = date_to

            month_sales = sales.filter(
                sale_date__range=[
                    current_date,
                    month_end
                ]
            )

            month_expenses = expenses.filter(
                expense_date__range=[
                    current_date,
                    month_end
                ]
            )

            month_sale_profit = month_sales.aggregate(
                total=Sum('profit')
            )['total'] or 0

            month_expense = month_expenses.aggregate(
                total=Sum('amount')
            )['total'] or 0

            month_net_profit = (
                float(month_sale_profit)
                - float(month_expense)
            )

            sheet.append([
                current_date.strftime('%B'),
                current_date.strftime('%Y'),
                float(month_sale_profit),
                float(month_expense),
                float(month_net_profit)
            ])

            current_date = next_month

    # Single TOTAL row
    sheet.append([
        'TOTAL',
        '',
        float(sale_profit),
        float(total_expense),
        float(net_profit)
    ])

    total_row = sheet.max_row

    # Header
    for cell in sheet[1]:
        cell.font = Font(bold=True)
        cell.alignment = Alignment(
            horizontal='center',
            vertical='center'
        )

    # Total row
    for cell in sheet[total_row]:
        cell.font = Font(bold=True)
        cell.alignment = Alignment(
            horizontal='center',
            vertical='center'
        )
        cell.fill = PatternFill(
            fill_type='solid',
            fgColor='E0E7FF'
        )

    # Date format
    for cell in sheet['A'][1:]:
        if hasattr(cell.value, 'strftime'):
            cell.number_format = 'DD-MM-YYYY'

    # Alignment
    for row in sheet.iter_rows():
        for cell in row:
            cell.alignment = Alignment(
                horizontal='center',
                vertical='center'
            )

    # Column widths
    sheet.column_dimensions['A'].width = 20
    sheet.column_dimensions['B'].width = 18
    sheet.column_dimensions['C'].width = 18
    sheet.column_dimensions['D'].width = 18
    sheet.column_dimensions['E'].width = 18

    response = HttpResponse(
        content_type=(
            'application/vnd.openxmlformats-officedocument.'
            'spreadsheetml.sheet'
        )
    )

    response['Content-Disposition'] = (
        'attachment; filename="profit_loss_report.xlsx"'
    )

    workbook.save(response)

    return response