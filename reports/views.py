from datetime import datetime, timedelta, date

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.http import HttpResponse
from django.utils import timezone

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill, Border, Side

from core.models import Branch
from operations.models import DailySale, Expense


# =========================================================
# COMMON HELPER FUNCTIONS
# =========================================================

def get_report_branch_context(request):
    user_profile = getattr(request.user, 'profile', None)

    is_admin = (
        user_profile.is_admin
        if user_profile
        else request.user.is_superuser
    )

    branches = Branch.objects.filter(status='active')

    if not is_admin:
        selected_branch = (
            user_profile.branch
            if user_profile and user_profile.branch
            else None
        )
    else:
        branch_id = request.GET.get('branch_id')

        if branch_id:
            selected_branch = branches.filter(id=branch_id).first()
        else:
            selected_branch = None

    return {
        'user_profile': user_profile,
        'is_admin': is_admin,
        'branches': branches,
        'selected_branch': selected_branch,
    }


def apply_report_branch_filter(queryset, selected_branch, is_admin):
    if selected_branch:
        return queryset.filter(branch=selected_branch)

    if is_admin:
        return queryset.filter(branch__status='active')

    return queryset.none()


def get_report_date(request, parameter='date'):
    date_str = request.GET.get(parameter)

    if date_str:
        try:
            return datetime.strptime(date_str, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            pass

    return timezone.localdate()


def get_report_date_range(request, is_monthly=True):
    today = timezone.localdate()

    if is_monthly:
        month_str = request.GET.get('month')

        try:
            selected_date = (
                datetime.strptime(month_str, '%Y-%m').date()
                if month_str
                else today
            )
        except (ValueError, TypeError):
            selected_date = today

        date_from = selected_date.replace(day=1)

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

        return (
            date_from,
            date_to,
            selected_date.strftime('%Y-%m'),
            str(today.year)
        )

    year_str = request.GET.get('year', str(today.year))

    try:
        year_value = int(year_str)

        if not 1 <= year_value <= 9998:
            raise ValueError

    except (ValueError, TypeError):
        year_value = today.year

    date_from = date(year_value, 1, 1)
    date_to = date(year_value, 12, 31)

    return (
        date_from,
        date_to,
        today.strftime('%Y-%m'),
        str(year_value)
    )


def get_profit_expense_totals(sales, expenses):
    sale_profit = sales.aggregate(
        total=Sum('profit')
    )['total'] or 0

    total_expense = expenses.aggregate(
        total=Sum('amount')
    )['total'] or 0

    net_profit = float(sale_profit) - float(total_expense)

    return sale_profit, total_expense, net_profit


def get_period_report_rows(
    sales,
    expenses,
    date_from,
    date_to,
    yearly=False
):
    """
    Monthly report:
        Display every date in the selected month.

    Yearly report:
        Display all 12 months in the selected year.

    Dates/months without sales or expenses are included with zero values.
    """

    report_rows = []
    current_date = date_from

    while current_date <= date_to:

        # Save the current period before moving to the next one.
        period_start = current_date

        if yearly:
            if period_start.month == 12:
                next_period = period_start.replace(
                    year=period_start.year + 1,
                    month=1,
                    day=1
                )
            else:
                next_period = period_start.replace(
                    month=period_start.month + 1,
                    day=1
                )

            period_end = min(
                next_period - timedelta(days=1),
                date_to
            )

            period_sales = sales.filter(
                sale_date__range=[period_start, period_end]
            )

            period_expenses = expenses.filter(
                expense_date__range=[period_start, period_end]
            )

            period_label = period_start.strftime('%B')
            day_label = period_start.strftime('%Y')

            current_date = next_period

        else:
            # One row for every day, even when no transactions exist.
            period_sales = sales.filter(
                sale_date=period_start
            )

            period_expenses = expenses.filter(
                expense_date=period_start
            )

            period_label = period_start.strftime('%d-%b-%Y')
            day_label = period_start.strftime('%A')

            current_date = period_start + timedelta(days=1)

        period_profit, period_expense, period_net = (
            get_profit_expense_totals(
                period_sales,
                period_expenses
            )
        )

        report_rows.append({
            # Always store the actual date for the template.
            'date': period_start,
            'period': period_label,
            'day': day_label,
            'sale_profit': period_profit,
            'expense': period_expense,
            'net_profit': period_net,
        })

    return report_rows


def create_excel_response(workbook, filename):
    response = HttpResponse(
        content_type=(
            'application/vnd.openxmlformats-officedocument.'
            'spreadsheetml.sheet'
        )
    )

    response['Content-Disposition'] = (
        f'attachment; filename="{filename}"'
    )

    workbook.save(response)

    return response


def style_excel_sheet(sheet, widths):
    header_fill = PatternFill(
        fill_type='solid',
        fgColor='1D4ED8'
    )

    total_fill = PatternFill(
        fill_type='solid',
        fgColor='DBEAFE'
    )

    white_font = Font(
        bold=True,
        color='FFFFFF'
    )

    thin_gray = Side(
        style='thin',
        color='E2E8F0'
    )

    # Style header.
    for cell in sheet[1]:
        cell.font = white_font
        cell.fill = header_fill
        cell.alignment = Alignment(
            horizontal='center',
            vertical='center'
        )

    sheet.row_dimensions[1].height = 25

    # Style all cells and borders.
    for row in sheet.iter_rows():
        for cell in row:
            cell.alignment = Alignment(
                horizontal='center',
                vertical='center'
            )

            cell.border = Border(
                bottom=thin_gray
            )

    # Style the final TOTAL row.
    total_row = sheet.max_row

    for cell in sheet[total_row]:
        cell.font = Font(bold=True)
        cell.fill = total_fill

    # Column widths.
    for column, width in widths.items():
        sheet.column_dimensions[column].width = width

    # Format date cells in column A.
    for cell in sheet['A'][1:]:
        if isinstance(cell.value, (datetime, date)):
            cell.number_format = 'DD-MM-YYYY'

    # Format monetary values.
    for column in ('C', 'D', 'E'):
        for cell in sheet[column][1:]:
            if isinstance(cell.value, (int, float)):
                cell.number_format = '#,##0.00'

    sheet.freeze_panes = 'A2'
    sheet.auto_filter.ref = f'A1:{sheet.cell(sheet.max_row, sheet.max_column).coordinate}'


# =========================================================
# DAILY P&L REPORT
# =========================================================

@login_required
def report_daily_view(request):
    context = get_report_branch_context(request)

    is_admin = context['is_admin']
    selected_branch = context['selected_branch']

    report_date = get_report_date(request)

    sales = DailySale.objects.filter(
        sale_date=report_date
    )

    expenses = Expense.objects.filter(
        expense_date=report_date
    )

    sales = apply_report_branch_filter(
        sales,
        selected_branch,
        is_admin
    )

    expenses = apply_report_branch_filter(
        expenses,
        selected_branch,
        is_admin
    )

    sales_detail = sales.select_related(
        'product',
        'product_packing',
        'branch'
    )

    expenses_detail = expenses.select_related(
        'expense_head',
        'staff',
        'branch'
    )

    gross_profit, total_expense, net_profit = (
        get_profit_expense_totals(
            sales,
            expenses
        )
    )

    total_volume_litres = sales.aggregate(
        total=Sum('base_quantity')
    )['total'] or 0

    return render(
        request,
        'reports/report_daily.html',
        {
            'report_date': report_date,
            'selected_branch': selected_branch,
            'branches': context['branches'],
            'sales_detail': sales_detail,
            'expenses_detail': expenses_detail,
            'gross_profit': gross_profit,
            'total_expense': total_expense,
            'net_profit': net_profit,
            'total_volume_litres': total_volume_litres,
            'is_admin': is_admin,
        }
    )


# =========================================================
# WEEKLY P&L REPORT
# =========================================================

@login_required
def report_weekly_view(request):
    context = get_report_branch_context(request)

    is_admin = context['is_admin']
    selected_branch = context['selected_branch']

    date_from = get_report_date(request, 'date_from')
    date_to = date_from + timedelta(days=6)

    sales = DailySale.objects.filter(
        sale_date__range=[date_from, date_to]
    )

    expenses = Expense.objects.filter(
        expense_date__range=[date_from, date_to]
    )

    sales = apply_report_branch_filter(
        sales,
        selected_branch,
        is_admin
    )

    expenses = apply_report_branch_filter(
        expenses,
        selected_branch,
        is_admin
    )

    sale_profit, total_expense, net_profit = (
        get_profit_expense_totals(
            sales,
            expenses
        )
    )

    total_sold_volume = sales.aggregate(
        total=Sum('base_quantity')
    )['total'] or 0

    report_rows = []
    current_date = date_from

    while current_date <= date_to:
        day_sales = sales.filter(
            sale_date=current_date
        )

        day_expenses = expenses.filter(
            expense_date=current_date
        )

        day_profit, day_expense, day_net = (
            get_profit_expense_totals(
                day_sales,
                day_expenses
            )
        )

        report_rows.append({
            'date': current_date,
            'period': current_date.strftime('%d-%b-%Y'),
            'day': current_date.strftime('%A'),
            'sale_profit': day_profit,
            'expense': day_expense,
            'net_profit': day_net,
        })

        current_date += timedelta(days=1)

    return render(
        request,
        'reports/report_weekly.html',
        {
            'date_from': date_from,
            'date_to': date_to,
            'selected_branch': selected_branch,
            'branches': context['branches'],
            'sale_profit': sale_profit,
            'total_expense': total_expense,
            'total_sold_volume': total_sold_volume,
            'net_profit': net_profit,
            'report_rows': report_rows,
            'is_admin': is_admin,
        }
    )


# =========================================================
# MONTHLY / YEARLY P&L REPORT
# =========================================================

@login_required
def report_monthly_yearly_view(request):
    context = get_report_branch_context(request)

    is_admin = context['is_admin']
    selected_branch = context['selected_branch']

    report_type = request.GET.get(
        'report_type',
        'monthly'
    )

    if report_type not in ('monthly', 'yearly'):
        report_type = 'monthly'

    (
        date_from,
        date_to,
        selected_month,
        selected_year
    ) = get_report_date_range(
        request,
        is_monthly=(report_type == 'monthly')
    )

    sales = DailySale.objects.filter(
        sale_date__range=[date_from, date_to]
    )

    expenses = Expense.objects.filter(
        expense_date__range=[date_from, date_to]
    )

    sales = apply_report_branch_filter(
        sales,
        context['selected_branch'],
        is_admin
    )

    expenses = apply_report_branch_filter(
        expenses,
        context['selected_branch'],
        is_admin
    )

    sale_profit, total_expense, net_profit = (
        get_profit_expense_totals(
            sales,
            expenses
        )
    )

    total_sold_volume = sales.aggregate(
        total=Sum('base_quantity')
    )['total'] or 0

    report_rows = get_period_report_rows(
        sales,
        expenses,
        date_from,
        date_to,
        yearly=(report_type == 'yearly')
    )

    today = timezone.localdate()

    years = range(
        today.year - 5,
        today.year + 6
    )

    return render(
        request,
        'reports/report_monthly_yearly.html',
        {
            'report_type': report_type,
            'date_from': date_from,
            'date_to': date_to,
            'selected_month': selected_month,
            'selected_year': selected_year,
            'selected_branch': selected_branch,
            'branches': context['branches'],
            'sale_profit': sale_profit,
            'total_expense': total_expense,
            'total_sold_volume': total_sold_volume,
            'net_profit': net_profit,
            'report_rows': report_rows,
            'is_admin': is_admin,
            'years': years,
        }
    )


# =========================================================
# DAILY EXCEL EXPORT
# =========================================================

@login_required
def report_daily_export_excel_view(request):
    context = get_report_branch_context(request)

    report_date = get_report_date(request)

    sales = DailySale.objects.filter(
        sale_date=report_date
    )

    expenses = Expense.objects.filter(
        expense_date=report_date
    )

    sales = apply_report_branch_filter(
        sales,
        context['selected_branch'],
        context['is_admin']
    )

    expenses = apply_report_branch_filter(
        expenses,
        context['selected_branch'],
        context['is_admin']
    )

    gross_profit, total_expense, net_profit = (
        get_profit_expense_totals(
            sales,
            expenses
        )
    )

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = 'Daily P&L'

    sheet.append([
        'Date',
        'Branch',
        'Sale Profit',
        'Expense',
        'Net Profit',
    ])

    if context['selected_branch']:
        branch_label = context['selected_branch'].name
    elif context['is_admin']:
        branch_label = 'All Branches'
    else:
        branch_label = 'Unassigned'

    sheet.append([
        report_date,
        branch_label,
        float(gross_profit),
        float(total_expense),
        float(net_profit),
    ])

    sheet.append([
        'TOTAL',
        '',
        float(gross_profit),
        float(total_expense),
        float(net_profit),
    ])

    style_excel_sheet(
        sheet,
        {
            'A': 18,
            'B': 25,
            'C': 18,
            'D': 18,
            'E': 18,
        }
    )

    return create_excel_response(
        workbook,
        'daily_profit_loss.xlsx'
    )


# =========================================================
# WEEKLY EXCEL EXPORT
# =========================================================

@login_required
def report_weekly_export_excel_view(request):
    context = get_report_branch_context(request)

    date_from = get_report_date(request, 'date_from')
    date_to = date_from + timedelta(days=6)

    sales = DailySale.objects.filter(
        sale_date__range=[date_from, date_to]
    )

    expenses = Expense.objects.filter(
        expense_date__range=[date_from, date_to]
    )

    sales = apply_report_branch_filter(
        sales,
        context['selected_branch'],
        context['is_admin']
    )

    expenses = apply_report_branch_filter(
        expenses,
        context['selected_branch'],
        context['is_admin']
    )

    sale_profit, total_expense, net_profit = (
        get_profit_expense_totals(
            sales,
            expenses
        )
    )

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = 'Weekly P&L'

    sheet.append([
        'Date',
        'Day',
        'Sale Profit',
        'Expense',
        'Net Profit',
    ])

    current_date = date_from

    while current_date <= date_to:
        day_sales = sales.filter(
            sale_date=current_date
        )

        day_expenses = expenses.filter(
            expense_date=current_date
        )

        day_profit, day_expense, day_net = (
            get_profit_expense_totals(
                day_sales,
                day_expenses
            )
        )

        sheet.append([
            current_date,
            current_date.strftime('%A'),
            float(day_profit),
            float(day_expense),
            float(day_net),
        ])

        current_date += timedelta(days=1)

    sheet.append([
        'TOTAL',
        '',
        float(sale_profit),
        float(total_expense),
        float(net_profit),
    ])

    style_excel_sheet(
        sheet,
        {
            'A': 18,
            'B': 18,
            'C': 18,
            'D': 18,
            'E': 18,
        }
    )

    return create_excel_response(
        workbook,
        'weekly_profit_loss.xlsx'
    )


# =========================================================
# MONTHLY / YEARLY EXCEL EXPORT
# =========================================================

@login_required
def report_monthly_yearly_export_excel_view(request):
    context = get_report_branch_context(request)

    report_type = request.GET.get(
        'report_type',
        'monthly'
    )

    if report_type not in ('monthly', 'yearly'):
        report_type = 'monthly'

    (
        date_from,
        date_to,
        selected_month,
        selected_year
    ) = get_report_date_range(
        request,
        is_monthly=(report_type == 'monthly')
    )

    sales = DailySale.objects.filter(
        sale_date__range=[date_from, date_to]
    )

    expenses = Expense.objects.filter(
        expense_date__range=[date_from, date_to]
    )

    sales = apply_report_branch_filter(
        sales,
        context['selected_branch'],
        context['is_admin']
    )

    expenses = apply_report_branch_filter(
        expenses,
        context['selected_branch'],
        context['is_admin']
    )

    sale_profit, total_expense, net_profit = (
        get_profit_expense_totals(
            sales,
            expenses
        )
    )

    report_rows = get_period_report_rows(
        sales,
        expenses,
        date_from,
        date_to,
        yearly=(report_type == 'yearly')
    )

    workbook = Workbook()
    sheet = workbook.active

    if report_type == 'monthly':
        sheet.title = 'Monthly P&L'

        sheet.append([
            'Date',
            'Day',
            'Sale Profit',
            'Expense',
            'Net Profit',
        ])

        for row in report_rows:
            sheet.append([
                row['date'],
                row['day'],
                float(row['sale_profit']),
                float(row['expense']),
                float(row['net_profit']),
            ])

    else:
        sheet.title = 'Yearly P&L'

        sheet.append([
            'Month',
            'Year',
            'Sale Profit',
            'Expense',
            'Net Profit',
        ])

        for row in report_rows:
            sheet.append([
                row['period'],
                row['day'],
                float(row['sale_profit']),
                float(row['expense']),
                float(row['net_profit']),
            ])

    sheet.append([
        'TOTAL',
        '',
        float(sale_profit),
        float(total_expense),
        float(net_profit),
    ])

    style_excel_sheet(
        sheet,
        {
            'A': 22,
            'B': 18,
            'C': 18,
            'D': 18,
            'E': 18,
        }
    )

    filename = (
        'monthly_profit_loss.xlsx'
        if report_type == 'monthly'
        else 'yearly_profit_loss.xlsx'
    )

    return create_excel_response(
        workbook,
        filename
    )