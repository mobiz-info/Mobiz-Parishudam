from rest_framework import serializers
from django.contrib.auth.models import User
from core.models import Branch, StaffProfile, Product, ProductPackingSize

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

    class Meta:
        model = ProductPackingSize
        fields = ['id', 'product', 'product_name', 'packing_name', 'packing_value', 'packing_unit', 'base_qty_unit', 'selling_price', 'created_at', 'updated_at']
        read_only_fields = ['id', 'product_name', 'created_at', 'updated_at']

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
            raise serializers.ValidationError("Base quantity in litres must be greater than 0.")
        return value

    def validate_selling_price(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("Selling price cannot be negative.")
        return value