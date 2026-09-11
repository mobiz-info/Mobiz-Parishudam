from django.db import models
from django.contrib.auth.models import User

class Branch(models.Model):
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    )
    branch_code = models.CharField(max_length=20, blank=True, null=True)
    name = models.CharField(max_length=100)
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Branches"
        ordering = ['name']


class StaffProfile(models.Model):
    ROLE_CHOICES = (
        ('ADMIN', 'Admin'),
        ('STAFF', 'Staff'),
    )
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='STAFF')
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True, related_name='staff_members')
    phone = models.CharField(max_length=20, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - {self.role} ({self.branch.name if self.branch else 'All Branches'})"

    @property
    def is_admin(self):
        return self.role == 'ADMIN' or self.user.is_superuser

class Unit(models.Model):
    name = models.CharField(max_length=50, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']

class Product(models.Model):
    product_name = models.CharField(max_length=150)
    unit = models.ForeignKey(Unit, on_delete=models.PROTECT, related_name='products')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.product_name

    class Meta:
        ordering = ['product_name']


class ProductPackingSize(models.Model):
    PACKING_UNIT_CHOICES = (
        ('ml', 'ml'),
        ('litre', 'Litre'),
    )

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='packing_sizes')
    packing_name = models.CharField(max_length=100)
    packing_value = models.DecimalField(max_digits=10, decimal_places=2)
    packing_unit = models.CharField(max_length=10, choices=PACKING_UNIT_CHOICES, default='litre')
    base_qty_unit = models.DecimalField(max_digits=10, decimal_places=2)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.product.product_name} - {self.packing_name}"

    class Meta:
        ordering = ['product', 'packing_value']
        constraints = [
            models.UniqueConstraint(
                fields=['product', 'packing_name'],
                name='unique_product_packing_name'
            )
        ]           

class ExpenseHead(models.Model):
    name = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']