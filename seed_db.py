# seed_db.py

import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'alx_backend_graphql.settings')
django.setup()

from crm.models import Customer, Product

def seed_customers():
    customer_data = [
        {"name": "Alice Smith", "email": "alice@example.com", "phone": "+1234567890"},
        {"name": "Bob Johnson", "email": "bob@example.com", "phone": "123-456-7890"},
        {"name": "Carol White", "email": "carol@example.com"},
    ]
    
    for data in customer_data:
        try:
            Customer.objects.get_or_create(email=data["email"], defaults=data)
            print(f"✅ Customer '{data['name']}' seeded.")
        except Exception as e:
            print(f"❌ Error seeding customer '{data['name']}': {e}")

def seed_products():
    product_data = [
        {"name": "Laptop", "price": 999.99, "stock": 10},
        {"name": "Phone", "price": 499.50, "stock": 25},
        {"name": "Headphones", "price": 79.99, "stock": 100},
    ]
    
    for data in product_data:
        try:
            Product.objects.get_or_create(name=data["name"], defaults=data)
            print(f"✅ Product '{data['name']}' seeded.")
        except Exception as e:
            print(f"❌ Error seeding product '{data['name']}': {e}")

if __name__ == "__main__":
    print("🔄 Seeding database...")
    seed_customers()
    seed_products()
    print("✅ Seeding complete.")
