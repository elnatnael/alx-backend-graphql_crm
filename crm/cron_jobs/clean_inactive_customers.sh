#!/bin/bash
# Script to clean up inactive customers from CRM system

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Execute Django command to delete inactive customers
OUTPUT=$(cd "$PROJECT_DIR" && python manage.py shell -c "
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
inactive_customers.delete()
print(count)
")

# Log results with timestamp
TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")
echo "[$TIMESTAMP] Deleted $OUTPUT inactive customers" >> /tmp/customer_cleanup_log.txt
