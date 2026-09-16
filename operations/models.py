from django.db import models
from django.contrib.auth.models import User
from core.models import Branch, Product, ProductPackingSize

class DailySale(models.Model):
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='daily_sales')
    staff = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='sales_entered')
    sale_date = models.DateField()
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='sales')
    product_packing = models.ForeignKey(ProductPackingSize, on_delete=models.CASCADE, related_name='sales')
    packing_count = models.IntegerField(default=0)
    base_quantity = models.DecimalField(max_digits=12, decimal_places=4, default=0.0000)
    margin = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    profit = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_sales')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='updated_sales')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Calculate base_quantity and profit before saving
        if self.product_packing:
            self.base_quantity = self.packing_count * self.product_packing.base_qty_unit
        self.profit = self.packing_count * self.margin
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.branch.name} | {self.sale_date} | {self.product_packing.packing_name} x {self.packing_count} (Profit: ₹{self.profit})"

    class Meta:
        unique_together = ('branch', 'sale_date', 'product_packing')
        ordering = ['-sale_date', 'branch', 'product_packing']

class ExpenseHead(models.Model):
    name = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']



class Expense(models.Model):
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='expenses')
    staff = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='expenses_entered')
    expense_date = models.DateField()
    expense_head = models.ForeignKey(ExpenseHead, on_delete=models.PROTECT, related_name='expenses')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_expenses')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='updated_expenses')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.branch.name} | {self.expense_date} | {self.expense_head.name}: ₹{self.amount}"

    class Meta:
        ordering = ['-expense_date', 'branch']


class Vehicle(models.Model):
    vehicle_number = models.CharField(max_length=50, unique=True)
    vehicle_type = models.CharField(max_length=100)
    branch = models.ForeignKey(Branch, on_delete=models.PROTECT, related_name='vehicles')
    driver_name = models.CharField(max_length=150)
    driver_phone = models.CharField(max_length=15)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.vehicle_number} - {self.vehicle_type}"