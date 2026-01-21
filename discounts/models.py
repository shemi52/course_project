from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from simple_history.models import HistoricalRecords
import uuid

class ProductCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Категория товаров"
        verbose_name_plural = "Категории товаров"


class Product(models.Model):
    name = models.CharField(max_length=200)
    sku = models.CharField(max_length=50, unique=True)
    category = models.ForeignKey(ProductCategory, on_delete=models.CASCADE, related_name='products')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    history = HistoricalRecords(
        history_change_reason_field=models.TextField(null=True),
        table_name='product_history'
    )
    
    def __str__(self):
        return f"{self.name} ({self.sku})"
    
    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('product-detail', kwargs={'pk': self.pk})
    
    class Meta:
        verbose_name = "Товар"
        verbose_name_plural = "Товары"
        ordering = ['name']


class Discount(models.Model):
    DISCOUNT_TYPES = (
        ('percentage', 'Процентная'),
        ('fixed', 'Фиксированная сумма'),
        ('bundle', 'Набор (2+1)'),
    )
    
    STATUS_CHOICES = (
        ('active', 'Активная'),
        ('upcoming', 'Предстоящая'),
        ('expired', 'Завершенная'),
        ('cancelled', 'Отменена'),
    )
    
    name = models.CharField(max_length=200)
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPES, default='percentage')
    value = models.DecimalField(max_digits=10, decimal_places=2)
    products = models.ManyToManyField(Product, related_name='discounts')
    categories = models.ManyToManyField(ProductCategory, blank=True, related_name='discounts')
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='upcoming')
    min_quantity = models.PositiveIntegerField(default=1)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_discounts')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    history = HistoricalRecords(
        history_change_reason_field=models.TextField(null=True),
        table_name='discount_history'
    )
    
    def __str__(self):
        return f"{self.name} ({self.get_discount_type_display()})"
    
    def is_active(self):
        now = timezone.now()
        return self.start_date <= now <= self.end_date and self.status == 'active'
    
    is_active.boolean = True
    is_active.short_description = "Активна сейчас"
    
    def save(self, *args, **kwargs):
        now = timezone.now()
        if now > self.end_date:
            self.status = 'expired'
        elif self.start_date <= now <= self.end_date:
            self.status = 'active'
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('discount-detail', kwargs={'pk': self.pk})
    
    class Meta:
        verbose_name = "Скидка"
        verbose_name_plural = "Скидки"
        ordering = ['-start_date']


class DiscountUsage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    discount = models.ForeignKey(Discount, on_delete=models.CASCADE, related_name='usages')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='discount_usages')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='used_discounts')
    original_price = models.DecimalField(max_digits=10, decimal_places=2)
    final_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)
    used_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Использование {self.discount.name}"
    
    def get_discount_amount(self):
        return self.original_price - self.final_price
    
    def save(self, *args, **kwargs):
        if not self.id:  
            if not self.user and hasattr(self, '_current_user'):
                self.user = self._current_user
        super().save(*args, **kwargs)
    
    class Meta:
        verbose_name = "Использование скидки"
        verbose_name_plural = "Использования скидок"
        ordering = ['-used_at']


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField(max_length=20, blank=True, verbose_name="Телефон")
    company = models.CharField(max_length=100, blank=True, verbose_name="Компания")
    position = models.CharField(max_length=100, blank=True, verbose_name="Должность")
    
    def __str__(self):
        return f"Профиль {self.user.username}"
    
    class Meta:
        verbose_name = "Профиль пользователя"
        verbose_name_plural = "Профили пользователей"