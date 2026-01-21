from django.urls import path
from . import views_site

urlpatterns = [
    path('', views_site.index, name='index'),
    path('products/', views_site.products_page, name='products'),
    path('discounts/', views_site.discounts_page, name='discounts'),
    path('categories/', views_site.categories_page, name='categories'),
    path('usage/', views_site.usage_page, name='usage'),
]