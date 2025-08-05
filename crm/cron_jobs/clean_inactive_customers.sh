#!/bin/bash
# Script to clean up inactive customers from CRM system

# Change to project directory
cd /path/to/alx-backend-graphql_crm

# Execute Django command to delete inactive customers
OUTPUT=$(python manage.py shell -c "
from django.utils import timezone
from datetime import timedelta
from customers.models import Customer
from orders.models import Order

cutoff_date = timezone.now() - timedelta(days=365)
inactive_customers = Customer.objects.filter(
    orders__isnull=True,
    date_joined__lt=cutoff_date
).distinct()
count = inactive_customers.count()
if count > 0:
    inactive_customers.delete()
print(count)
")

# Log results with timestamp
TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")
echo "[$TIMESTAMP] Deleted $OUTPUT inactive customers" >> /tmp/customer_cleanup_log.txt
