from django.core.management.base import BaseCommand
from django.utils import timezone
from discounts.models import Discount

class Command(BaseCommand):
    help = 'Обновление статусов скидок'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Только показать что будет изменено'
        )
    
    def handle(self, *args, **options):
        now = timezone.now()
        dry_run = options['dry_run']
        
        discounts = Discount.objects.exclude(status='cancelled')
        updated_count = 0
        
        for discount in discounts:
            current_status = discount.status
            expected_status = self.calculate_correct_status(discount, now)
            
            if current_status != expected_status:
                if dry_run:
                    self.stdout.write(
                        f"#{discount.id} '{discount.name}' "
                        f"{current_status} -> {expected_status}"
                    )
                else:
                    discount.status = expected_status
                    discount.save(update_fields=['status', 'updated_at'])
                    updated_count += 1
        
        if dry_run:
            self.stdout.write(f"Найдено проблем: {updated_count}")
        else:
            self.stdout.write(f"Обновлено скидок: {updated_count}")
    
    def calculate_correct_status(self, discount, now):
        if now > discount.end_date:
            return 'expired'
        elif discount.start_date <= now <= discount.end_date:
            return 'active'
        else:  
            return 'upcoming'