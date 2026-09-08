import os
import django
from datetime import date, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'parishudam_project.settings')
django.setup()

from django.contrib.auth.models import User
from core.models import Branch, StaffProfile
from products.models import Product, ProductPacking, MarginHistory
from operations.models import ExpenseHead, DailySale, Expense
from targets.models import WeeklyTarget, WeeklyTargetItem

def seed_database():
    print("Seeding database for Parishudam Coconut Oil...")

    # 1. Superuser / Admin
    admin_user, created = User.objects.get_or_create(
        username='admin',
        defaults={
            'email': 'admin@parishudam.com',
            'first_name': 'Admin',
            'last_name': 'User',
            'is_staff': True,
            'is_superuser': True
        }
    )
    if created:
        admin_user.set_password('admin123')
        admin_user.save()
        print("Created admin user: admin / admin123")

    admin_profile, _ = StaffProfile.objects.get_or_create(
        user=admin_user,
        defaults={'role': 'ADMIN', 'phone': '9876543210', 'status': 'active'}
    )

    # 2. Branches
    kochi_branch, _ = Branch.objects.get_or_create(
        branch_code='KOC001',
        defaults={'name': 'Kochi', 'address': 'MG Road, Kochi, Kerala', 'phone': '0484-2345678', 'status': 'active'}
    )
    aluva_branch, _ = Branch.objects.get_or_create(
        branch_code='ALU001',
        defaults={'name': 'Aluva', 'address': 'Bank Road, Aluva, Kerala', 'phone': '0484-2456789', 'status': 'active'}
    )
    thrissur_branch, _ = Branch.objects.get_or_create(
        branch_code='THR001',
        defaults={'name': 'Thrissur', 'address': 'Round South, Thrissur, Kerala', 'phone': '0487-2567890', 'status': 'active'}
    )
    print("Created branches: Kochi, Aluva, Thrissur")

    # 3. Staff Users
    staff_data = [
        ('anas', 'anas@parishudam.com', 'Anas', 'K', kochi_branch),
        ('rahul', 'rahul@parishudam.com', 'Rahul', 'M', aluva_branch),
        ('afsal', 'afsal@parishudam.com', 'Afsal', 'P', thrissur_branch),
    ]

    for username, email, first_name, last_name, branch in staff_data:
        user, created = User.objects.get_or_create(
            username=username,
            defaults={'email': email, 'first_name': first_name, 'last_name': last_name}
        )
        if created:
            user.set_password('staff123')
            user.save()
        StaffProfile.objects.get_or_create(
            user=user,
            defaults={'role': 'STAFF', 'branch': branch, 'phone': '9800000000', 'status': 'active'}
        )
        print(f"Created staff user: {username} / staff123 assigned to {branch.name}")

    # 4. Expense Heads
    heads = ['Fuel', 'Transport', 'Salary', 'Electricity', 'Rent', 'Maintenance', 'Vehicle Expense', 'Office Expense', 'Other']
    for head_name in heads:
        ExpenseHead.objects.get_or_create(name=head_name, defaults={'status': 'active'})
    print("Created expense heads")

    # 5. Product & Packing Sizes
    oil_product, _ = Product.objects.get_or_create(
        product_code='PCO001',
        defaults={
            'name': 'Parishudam Coconut Oil',
            'base_unit': 'Litre',
            'description': '100% Pure & Natural Virgin Coconut Oil',
            'status': 'active'
        }
    )

    packings_data = [
        ('500 ml', 500, 'ml', 0.5000, 90.00, 10.00),
        ('1 Litre', 1, 'Litre', 1.0000, 175.00, 25.00),
        ('5 Litre', 5, 'Litre', 5.0000, 850.00, 100.00),
        ('15 Litre', 15, 'Litre', 15.0000, 2550.00, 250.00),
    ]

    effective_date = date(2026, 9, 1)

    for p_name, p_val, p_unit, base_qty, price, default_margin in packings_data:
        packing, _ = ProductPacking.objects.get_or_create(
            product=oil_product,
            packing_name=p_name,
            defaults={
                'packing_value': p_val,
                'packing_unit': p_unit,
                'base_quantity': base_qty,
                'selling_price': price,
                'status': 'active'
            }
        )
        # Margin history
        MarginHistory.objects.get_or_create(
            product_packing=packing,
            effective_from=effective_date,
            defaults={'margin': default_margin, 'created_by': admin_user}
        )
    print("Created product Parishudam Coconut Oil with packing sizes and date-based margins")

    # 6. Weekly Targets (Current Week)
    today = date(2026, 9, 8) # Current simulated date
    start_of_week = today - timedelta(days=today.weekday()) # Monday (2026-09-07)
    end_of_week = start_of_week + timedelta(days=6) # Sunday (2026-09-13)

    target_configs = [
        (kochi_branch, [('500 ml', 500), ('1 Litre', 300), ('5 Litre', 100)]),
        (aluva_branch, [('500 ml', 400), ('1 Litre', 250), ('5 Litre', 80)]),
        (thrissur_branch, [('500 ml', 600), ('1 Litre', 400), ('5 Litre', 120)]),
    ]

    for branch, items in target_configs:
        w_target, _ = WeeklyTarget.objects.get_or_create(
            branch=branch,
            start_date=start_of_week,
            end_date=end_of_week,
            defaults={'created_by': admin_user}
        )
        for p_name, target_count in items:
            packing = ProductPacking.objects.get(product=oil_product, packing_name=p_name)
            WeeklyTargetItem.objects.get_or_create(
                weekly_target=w_target,
                product=oil_product,
                product_packing=packing,
                defaults={'target_packing_count': target_count}
            )
    print("Created weekly targets for all branches")

    # 7. Sample Daily Sales & Expenses for Today
    anas_user = User.objects.get(username='anas')
    p_500ml = ProductPacking.objects.get(product=oil_product, packing_name='500 ml')
    p_1l = ProductPacking.objects.get(product=oil_product, packing_name='1 Litre')
    p_5l = ProductPacking.objects.get(product=oil_product, packing_name='5 Litre')

    # Kochi Sales for Today
    DailySale.objects.get_or_create(
        branch=kochi_branch,
        sale_date=today,
        product_packing=p_500ml,
        defaults={
            'staff': anas_user,
            'product': oil_product,
            'packing_count': 20,
            'margin': p_500ml.get_current_margin(today),
            'created_by': anas_user
        }
    )
    DailySale.objects.get_or_create(
        branch=kochi_branch,
        sale_date=today,
        product_packing=p_1l,
        defaults={
            'staff': anas_user,
            'product': oil_product,
            'packing_count': 30,
            'margin': p_1l.get_current_margin(today),
            'created_by': anas_user
        }
    )
    DailySale.objects.get_or_create(
        branch=kochi_branch,
        sale_date=today,
        product_packing=p_5l,
        defaults={
            'staff': anas_user,
            'product': oil_product,
            'packing_count': 10,
            'margin': p_5l.get_current_margin(today),
            'created_by': anas_user
        }
    )

    # Kochi Expenses for Today
    fuel_head = ExpenseHead.objects.get(name='Fuel')
    Expense.objects.get_or_create(
        branch=kochi_branch,
        expense_date=today,
        expense_head=fuel_head,
        amount=500.00,
        defaults={
            'staff': anas_user,
            'description': 'Delivery vehicle fuel',
            'created_by': anas_user
        }
    )

    print("Database seeding completed successfully!")

if __name__ == '__main__':
    seed_database()
