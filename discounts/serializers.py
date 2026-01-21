from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Product, ProductCategory, Discount, DiscountUsage, UserProfile

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['phone', 'company', 'position']

class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'profile']

class ProductCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductCategory
        fields = ['id', 'name', 'description']

class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    current_discounts = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'sku', 'category', 'category_name', 
            'price', 'description', 'created_at', 'updated_at',
            'current_discounts'
        ]
    
    def get_current_discounts(self, obj):
        from django.utils import timezone
        now = timezone.now()
        active_discounts = obj.discounts.filter(
            status='active',
            start_date__lte=now,
            end_date__gte=now
        )
        return DiscountShortSerializer(active_discounts, many=True).data

class DiscountShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Discount
        fields = ['id', 'name', 'discount_type', 'value']

class DiscountSerializer(serializers.ModelSerializer):
    products_detail = ProductSerializer(source='products', many=True, read_only=True)
    categories_detail = ProductCategorySerializer(source='categories', many=True, read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = Discount
        fields = [
            'id', 'name', 'discount_type', 'value', 'products', 'products_detail',
            'categories', 'categories_detail', 'start_date', 'end_date', 'status',
            'min_quantity', 'created_by', 'created_by_username', 'created_at',
            'updated_at', 'is_active'
        ]
    
    def validate(self, data):
        if data['start_date'] >= data['end_date']:
            raise serializers.ValidationError("Дата окончания должна быть позже даты начала")
        
        if data['discount_type'] == 'percentage' and (data['value'] <= 0 or data['value'] > 100):
            raise serializers.ValidationError("Процентная скидка должна быть от 0 до 100")
        
        if data['discount_type'] == 'fixed' and data['value'] <= 0:
            raise serializers.ValidationError("Фиксированная скидка должна быть больше 0")
        
        return data

class DiscountUsageSerializer(serializers.ModelSerializer):
    discount_name = serializers.CharField(source='discount.name', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True, allow_null=True)
    
    class Meta:
        model = DiscountUsage
        fields = [
            'id', 'discount', 'discount_name', 'product', 'product_name',
            'user', 'username', 'original_price', 'final_price',
            'quantity', 'used_at'
        ]
        read_only_fields = ['used_at']