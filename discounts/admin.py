from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from import_export.formats import base_formats
from simple_history.admin import SimpleHistoryAdmin
from django.contrib.auth.models import User

from .models import Product, ProductCategory, Discount, DiscountUsage, UserProfile

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Профиль'
    fk_name = 'user'


class CustomUserAdmin(UserAdmin):
    inlines = (UserProfileInline,)
    list_display = ['username', 'email', 'first_name', 'last_name', 'is_staff', 'get_phone', 'get_company']
    list_filter = ['is_staff', 'is_active']
    
    def get_phone(self, obj):
        try:
            return obj.profile.phone
        except UserProfile.DoesNotExist:
            return '-'
    get_phone.short_description = 'Телефон'
    
    def get_company(self, obj):
        try:
            return obj.profile.company
        except UserProfile.DoesNotExist:
            return '-'
    get_company.short_description = 'Компания'
    
    def get_inline_instances(self, request, obj=None):
        if not obj:
            return list()
        return super().get_inline_instances(request, obj)


admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

class ProductResource(resources.ModelResource):
    class Meta:
        model = Product

class DiscountResource(resources.ModelResource):
    class Meta:
        model = Discount

class ProductInline(admin.TabularInline):
    model = Discount.products.through
    extra = 1

class DiscountUsageInline(admin.TabularInline):
    model = DiscountUsage
    extra = 0
    readonly_fields = ['used_at', 'original_price', 'final_price']
    
    def has_add_permission(self, request, obj=None):
        return False

@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'product_count']
    search_fields = ['name']
    
    def product_count(self, obj):
        return obj.products.count()
    product_count.short_description = 'Количество товаров'

@admin.register(Product)
class ProductAdmin(ImportExportModelAdmin, SimpleHistoryAdmin):
    resource_class = ProductResource
    formats = [base_formats.XLSX, base_formats.CSV]
    
    list_display = ['name', 'sku', 'category_link', 'price', 'created_at']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'sku', 'category', 'price')
        }),
        ('Дополнительная информация', {
            'fields': ('description',),
            'classes': ('collapse',)
        }),
    )
    
    list_filter = ['category', 'created_at']
    search_fields = ['name', 'sku', 'description']
    ordering = ['name']
    
    def category_link(self, obj):
        return format_html(
            '<a href="/admin/discounts/productcategory/{}/change/">{}</a>',
            obj.category.id,
            obj.category.name
        )
    category_link.short_description = 'Категория'
    category_link.admin_order_field = 'category__name'

@admin.register(Discount)
class DiscountAdmin(ImportExportModelAdmin, SimpleHistoryAdmin):
    resource_class = DiscountResource
    formats = [base_formats.XLSX, base_formats.CSV]
    
    list_display = ['name', 'discount_type', 'value', 'status', 
                   'start_date', 'end_date', 'is_active', 
                   'product_count', 'created_by_link']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'discount_type', 'value', 'status')
        }),
        ('Временные параметры', {
            'fields': ('start_date', 'end_date')
        }),
        ('Условия применения', {
            'fields': ('min_quantity', 'categories')
        }),
        ('Создатель', {
            'fields': ('created_by',)
        }),
    )
    
    list_filter = ['status', 'discount_type', 'start_date', 'created_by']
    search_fields = ['name']
    filter_horizontal = ['products', 'categories']
    inlines = [ProductInline, DiscountUsageInline]
    
    def created_by_link(self, obj):
        if obj.created_by:
            return format_html(
                '<a href="/admin/auth/user/{}/change/">{}</a>',
                obj.created_by.id,
                obj.created_by.username
            )
        return '-'
    created_by_link.short_description = 'Создатель'
    created_by_link.admin_order_field = 'created_by__username'
    
    def product_count(self, obj):
        return obj.products.count()
    product_count.short_description = 'Количество товаров'

@admin.register(DiscountUsage)
class DiscountUsageAdmin(admin.ModelAdmin):
    list_display = ['discount_link', 'product_link', 'user_link', 
                   'original_price', 'final_price', 'used_at']
    list_filter = ['used_at', 'discount']
    search_fields = ['discount__name', 'product__name', 'user__username']
    readonly_fields = ['used_at', 'original_price', 'final_price']
    date_hierarchy = 'used_at'
    
    def discount_link(self, obj):
        return format_html(
            '<a href="/admin/discounts/discount/{}/change/">{}</a>',
            obj.discount.id,
            obj.discount.name
        )
    discount_link.short_description = 'Скидка'
    
    def product_link(self, obj):
        return format_html(
            '<a href="/admin/discounts/product/{}/change/">{}</a>',
            obj.product.id,
            obj.product.name
        )
    product_link.short_description = 'Товар'
    
    def user_link(self, obj):
        if obj.user:
            return format_html(
                '<a href="/admin/auth/user/{}/change/">{}</a>',
                obj.user.id,
                obj.user.username
            )
        return '-'
    user_link.short_description = 'Пользователь'

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'phone', 'company', 'position']
    search_fields = ['user__username', 'phone', 'company']
    list_filter = ['company']