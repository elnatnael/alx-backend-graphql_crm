import os
import django
from faker import Faker

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'graphql_crm.settings')
django.setup()

from crm.models import Customer, Product, Order

fake = Faker()

def seed_data():
    # Create 10 customers
    for _ in range(10):
        Customer.objects.create(
            name=fake.name(),
            email=fake.email(),
            phone=fake.phone_number()[:15]
        )

    # Create 5 products
    for i in range(5):
        Product.objects.create(
            name=f"Product {i+1}",
            price=10 + i * 5,
            stock=100 - i * 10
        )

    # Create orders
    customers = Customer.objects.all()
    products = list(Product.objects.all())
    
    for customer in customers[:5]:  # Only create orders for first 5 customers
        order = Order.objects.create(
            customer=customer,
            total_amount=0
        )
        selected_products = products[:3]  # Assign first 3 products to each order
        order.products.set(selected_products)
        order.total_amount = sum(p.price for p in selected_products)
        order.save()

if __name__ == '__main__':
    print("Seeding data...")
    seed_data()
    print("Seeding complete!")