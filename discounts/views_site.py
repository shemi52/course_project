# discounts/views_site.py
from django.shortcuts import render
# Убираем @login_required с публичных страниц

def index(request):
    """Главная страница"""
    return render(request, 'index.html')

def products_page(request):
    """Страница товаров"""
    return render(request, 'products.html')

def discounts_page(request):
    """Страница скидок"""
    return render(request, 'discounts.html')

def categories_page(request):
    """Страница категорий"""
    return render(request, 'categories.html')

def usage_page(request):
    """Страница истории использования"""
    return render(request, 'usage.html')