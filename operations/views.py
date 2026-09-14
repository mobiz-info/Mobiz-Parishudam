from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import datetime
from decimal import Decimal

from core.models import Branch, StaffProfile, Product, ProductPackingSize, ProductMargin, ExpenseHead
from operations.models import DailySale, Expense


# --- DAILY SALES MATRIX ENTRY ---
@login_required
def sales_entry_view(request):
    user_profile = getattr(request.user, 'profile', None)
    is_admin = user_profile.is_admin if user_profile else request.user.is_superuser

    # Determine branch
    branch_id = request.GET.get('branch_id')
    if not is_admin and user_profile and user_profile.branch:
        branch = user_profile.branch
    elif branch_id:
        branch = get_object_or_404(Branch, id=branch_id)
    else:
        branch = Branch.objects.filter(status='active').first()

    # Determine date
    date_str = request.GET.get('sale_date')
    if date_str:
        try:
            sale_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            sale_date = timezone.now().date()
    else:
        sale_date = timezone.now().date()

    branches = Branch.objects.filter(status='active')
    packings = ProductPackingSize.objects.select_related('product', 'packing_unit').all()

    if request.method == 'POST':
        # Process matrix submission
        form_sale_date_str = request.POST.get('sale_date')
        if form_sale_date_str:
            sale_date = datetime.strptime(form_sale_date_str, '%Y-%m-%d').date()

        selected_branch_id = request.POST.get('branch_id')
        if is_admin and selected_branch_id:
            branch = get_object_or_404(Branch, id=selected_branch_id)

        saved_count = 0
        for p in packings:
            count_key = f"quantity_{p.id}"
            margin_key = f"margin_{p.id}"
            
            count_val = request.POST.get(count_key)
            margin_val = request.POST.get(margin_key)

            if count_val is not None and count_val.strip() != "":
                try:
                    count_int = int(count_val)
                    if count_int < 0:
                        count_int = 0
                except ValueError:
                    count_int = 0

                try:
                    if margin_val and margin_val.strip() != "":
                        margin_dec = Decimal(margin_val)
                    else:
                        margin_obj = ProductMargin.objects.filter(
                            product=p.product,
                            packing_size=p,
                            effective_date__lte=sale_date
                        ).order_by('-effective_date').first()
                        margin_dec = margin_obj.margin_amount if margin_obj else Decimal('0.00')
                except Exception:
                    margin_obj = ProductMargin.objects.filter(
                        product=p.product,
                        packing_size=p,
                        effective_date__lte=sale_date
                    ).order_by('-effective_date').first()
                    margin_dec = margin_obj.margin_amount if margin_obj else Decimal('0.00')

                if count_int >= 0:
                    daily_sale, created = DailySale.objects.get_or_create(
                        branch=branch,
                        sale_date=sale_date,
                        product_packing=p,
                        defaults={
                            'staff': request.user,
                            'product': p.product,
                            'packing_count': count_int,
                            'margin': margin_dec,
                            'created_by': request.user,
                            'updated_by': request.user,
                        }
                    )
                    if not created:
                        daily_sale.packing_count = count_int
                        daily_sale.margin = margin_dec
                        daily_sale.updated_by = request.user
                        daily_sale.save()
                    saved_count += 1

        messages.success(request, f"Daily sales for {branch.name} on {sale_date.strftime('%d-%b-%Y')} saved successfully.")
        return redirect(f"/sales/entry/?sale_date={sale_date.strftime('%Y-%m-%d')}&branch_id={branch.id}")

    # Build packing matrix data
    matrix = []
    for p in packings:
        existing_sale = DailySale.objects.filter(branch=branch, sale_date=sale_date, product_packing=p).first()
        if existing_sale:
            effective_margin = existing_sale.margin
        else:
            margin_obj = ProductMargin.objects.filter(
                product=p.product,
                packing_size=p,
                effective_date__lte=sale_date
            ).order_by('-effective_date').first()
            effective_margin = margin_obj.margin_amount if margin_obj else Decimal('0.00')

        qty_count = existing_sale.packing_count if existing_sale else 0
        profit_calc = qty_count * float(effective_margin)
        base_litres = qty_count * float(p.base_qty_unit)

        matrix.append({
            'packing': p,
            'margin': effective_margin,
            'count': qty_count,
            'profit': profit_calc,
            'base_litres': base_litres
        })

    context = {
        'branch': branch,
        'branches': branches,
        'sale_date': sale_date,
        'matrix': matrix,
        'is_admin': is_admin,
    }
    return render(request, 'operations/sales_entry.html', context)


@login_required
def sales_list_view(request):
    user_profile = getattr(request.user, 'profile', None)
    is_admin = user_profile.is_admin if user_profile else request.user.is_superuser

    sales_qs = DailySale.objects.select_related('branch', 'staff', 'product', 'product_packing').all()

    if not is_admin and user_profile and user_profile.branch:
        sales_qs = sales_qs.filter(branch=user_profile.branch)
    else:
        branch_id = request.GET.get('branch_id')
        if branch_id:
            sales_qs = sales_qs.filter(branch_id=branch_id)

    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    if date_from:
        sales_qs = sales_qs.filter(sale_date__gte=date_from)
    if date_to:
        sales_qs = sales_qs.filter(sale_date__lte=date_to)

    branches = Branch.objects.filter(status='active')
    return render(request, 'operations/sales_list.html', {
        'sales': sales_qs,
        'branches': branches,
        'is_admin': is_admin
    })





