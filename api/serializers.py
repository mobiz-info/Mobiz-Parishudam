from rest_framework import serializers
from django.contrib.auth.models import User
from core.models import Branch, StaffProfile, Product, ProductPackingSize,ProductMargin,Vehicle

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']

class BranchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = '__all__'

class StaffProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    branch = BranchSerializer(read_only=True)
    branch_id = serializers.PrimaryKeyRelatedField(queryset=Branch.objects.all(), source='branch', write_only=True, required=False)

    class Meta:
        model = StaffProfile
        fields = '__all__'


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'product_name', 'unit', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_product_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Product name is required.")
        return value

class ProductPackingSizeSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.product_name', read_only=True)
    packing_unit_name = serializers.CharField(source='packing_unit.name', read_only=True)

    class Meta:
        model = ProductPackingSize
        fields = [
            'id',
            'product',
            'product_name',
            'packing_name',
            'packing_value',
            'packing_unit',
            'packing_unit_name',
            'base_qty_unit',
            'selling_price',
            'created_at',
            'updated_at'
        ]
        read_only_fields = [
            'id',
            'product_name',
            'packing_unit_name',
            'created_at',
            'updated_at'
        ]

    def validate_packing_name(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError("Packing name is required.")

        return value

    def validate_packing_value(self, value):
        if value <= 0:
            raise serializers.ValidationError("Packing value must be greater than 0.")

        return value

    def validate_base_qty_unit(self, value):
        if value <= 0:
            raise serializers.ValidationError("Base quantity must be greater than 0.")

        return value

    def validate_selling_price(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("Selling price cannot be negative.")

        return value
    
class ProductMarginSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.product_name', read_only=True)
    packing_name = serializers.CharField(source='packing_size.packing_name', read_only=True)

    class Meta:
        model = ProductMargin
        fields = [
            'id',
            'product',
            'product_name',
            'packing_size',
            'packing_name',
            'margin_amount',
            'effective_date',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'product_name', 'packing_name', 'created_at', 'updated_at']

    def validate_margin_amount(self, value):
        if value < 0:
            raise serializers.ValidationError("Margin amount cannot be negative.")
        return value

class VehicleSerializer(serializers.ModelSerializer):
    branch_name = serializers.CharField(source='branch.name', read_only=True)

    class Meta:
        model = Vehicle
        fields = [
            'id',
            'vehicle_number',
            'vehicle_type',
            'branch',
            'branch_name',
            'driver_name',
            'driver_phone',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'branch_name', 'created_at', 'updated_at']