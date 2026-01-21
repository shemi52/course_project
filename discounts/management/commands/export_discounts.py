from django.core.management.base import BaseCommand
from django.utils import timezone
from discounts.models import Discount
import csv

class Command(BaseCommand):
    help = 'Экспорт активных скидок в CSV файл'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--output',
            type=str,
            default='active_discounts.csv',
            help='Имя выходного файла'
        )
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Сколько дней вперед смотреть'
        )
    
    def handle(self, *args, **options):
        output_file = options['output']
        days = options['days']
        
        now = timezone.now()
        future_date = now + timezone.timedelta(days=days)
        
        from django.db.models import Q
        
        discounts = Discount.objects.filter(
            Q(status='active', end_date__gte=now) |
            Q(status='upcoming', start_date__lte=future_date, start_date__gte=now)
        ).select_related('created_by').prefetch_related('products')
        
        self.stdout.write(f'Найдено {discounts.count()} скидок для экспорта')
        
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'ID', 'Название', 'Тип', 'Значение', 'Статус',
                'Дата начала', 'Дата окончания', 'Создатель',
                'Количество товаров', 'Минимальное количество'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            
            for discount in discounts:
                writer.writerow({
                    'ID': discount.id,
                    'Название': discount.name,
                    'Тип': discount.get_discount_type_display(),
                    'Значение': discount.value,
                    'Статус': discount.get_status_display(),
                    'Дата начала': discount.start_date.strftime('%Y-%m-%d %H:%M'),
                    'Дата окончания': discount.end_date.strftime('%Y-%m-%d %H:%M'),
                    'Создатель': discount.created_by.username if discount.created_by else 'Неизвестно',
                    'Количество товаров': discount.products.count(),
                    'Минимальное количество': discount.min_quantity
                })
        
        self.stdout.write(self.style.SUCCESS(f'Успешно экспортировано в {output_file}'))