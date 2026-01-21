from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta, datetime
from django.contrib.auth.models import User

from .models import Product, ProductCategory, Discount, DiscountUsage
from .serializers import (
    ProductSerializer, ProductCategorySerializer,
    DiscountSerializer, DiscountUsageSerializer
)

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 5
    page_size_query_param = 'page_size'
    max_page_size = 100
    
    def get_paginated_response(self, data):
        return Response({
            'count': self.page.paginator.count,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'current_page': self.page.number,
            'total_pages': self.page.paginator.num_pages,
            'results': data
        })

class ProductCategoryViewSet(viewsets.ModelViewSet):
    queryset = ProductCategory.objects.all()
    serializer_class = ProductCategorySerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['name', 'description']

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category']
    search_fields = ['name', 'sku', 'description']
    ordering_fields = ['name', 'price', 'created_at', 'updated_at']
    ordering = ['name']

class DiscountViewSet(viewsets.ModelViewSet):
    queryset = Discount.objects.all()
    serializer_class = DiscountSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'discount_type', 'created_by']
    search_fields = ['name']
    ordering_fields = ['start_date', 'end_date', 'created_at', 'name']
    ordering = ['-start_date']
    
    @action(detail=True, methods=['POST'])
    def apply_to_cart(self, request, pk=None):
        discount = self.get_object()
        
        if not discount.is_active():
            return Response(
                {'error': 'Скидка не активна'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        product_ids = request.data.get('product_ids', [])
        quantities = request.data.get('quantities', {})
        
        total_original = 0
        total_final = 0
        applied_items = []
        
        for product_id in product_ids:
            try:
                product = Product.objects.get(id=product_id)
            except Product.DoesNotExist:
                continue
                
            quantity = quantities.get(str(product_id), 1)
            
            # Проверяем, применяется ли скидка к этому товару
            if (product in discount.products.all() or 
                product.category in discount.categories.all()):
                
                # Рассчитываем цену со скидкой
                if discount.discount_type == 'percentage':
                    item_final = product.price * (1 - discount.value / 100)
                elif discount.discount_type == 'fixed':
                    item_final = max(0, product.price - discount.value)
                else:  # bundle
                    item_final = product.price  # Упрощенная версия
                
                total_original += product.price * quantity
                total_final += item_final * quantity
                
                applied_items.append({
                    'product_id': product.id,
                    'product_name': product.name,
                    'quantity': quantity,
                    'original_price': float(product.price),
                    'final_price': float(item_final)
                })
        
        # Проверяем минимальное количество
        total_quantity = sum(quantities.values())
        if total_quantity < discount.min_quantity:
            return Response(
                {'error': f'Минимальное количество для скидки: {discount.min_quantity}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return Response({
            'discount_id': discount.id,
            'discount_name': discount.name,
            'discount_type': discount.get_discount_type_display(),
            'discount_value': float(discount.value),
            'applied_items': applied_items,
            'total_original': float(total_original),
            'total_final': float(total_final),
            'total_saved': float(total_original - total_final)
        })
    
    def perform_create(self, serializer):
        """Сохранение с автоматической установкой пользователя"""
        if self.request.user.is_authenticated:
            serializer.save(created_by=self.request.user)
        else:
            serializer.save()

class DiscountUsageViewSet(viewsets.ModelViewSet):
    queryset = DiscountUsage.objects.all()
    serializer_class = DiscountUsageSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['discount', 'product', 'user']
    ordering_fields = ['used_at', 'final_price']
    ordering = ['-used_at']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Фильтрация по датам
        used_at_after = self.request.query_params.get('used_at_after')
        used_at_before = self.request.query_params.get('used_at_before')
        
        if used_at_after:
            queryset = queryset.filter(used_at__gte=used_at_after)
        if used_at_before:
            queryset = queryset.filter(used_at__lte=used_at_before)
            
        return queryset
    
    def perform_create(self, serializer):
        """Сохранение с автоматической установкой пользователя"""
        user = serializer.validated_data.get('user')
        if not user and self.request.user.is_authenticated:
            serializer.save(user=self.request.user)
        else:
            serializer.save()