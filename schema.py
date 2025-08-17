import graphene
from graphene_django import DjangoObjectType
from django.core.exceptions import ValidationError
from django.db import transaction
from .models import Customer, Product, Order
import re

# Type Definitions
class CustomerType(DjangoObjectType):
    class Meta:
        model = Customer
        fields = ("id", "name", "email", "phone")

class ProductType(DjangoObjectType):
    class Meta:
        model = Product
        fields = ("id", "name", "price", "stock")

class OrderType(DjangoObjectType):
    customer = graphene.Field(CustomerType)
    products = graphene.List(ProductType)
    
    class Meta:
        model = Order
        fields = ("id", "customer", "products", "total_amount", "order_date")

# Input Types
class CustomerInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    email = graphene.String(required=True)
    phone = graphene.String()

class ProductInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    price = graphene.Decimal(required=True)
    stock = graphene.Int()

class OrderInput(graphene.InputObjectType):
    customer_id = graphene.ID(required=True)
    product_ids = graphene.List(graphene.ID, required=True)
    order_date = graphene.DateTime()

# Query Class
class Query(graphene.ObjectType):
    all_customers = graphene.List(CustomerType)
    all_products = graphene.List(ProductType)
    all_orders = graphene.List(OrderType)
    
    customer = graphene.Field(CustomerType, id=graphene.ID(required=True))
    product = graphene.Field(ProductType, id=graphene.ID(required=True))
    order = graphene.Field(OrderType, id=graphene.ID(required=True))

    def resolve_all_customers(self, info):
        return Customer.objects.all()

    def resolve_all_products(self, info):
        return Product.objects.all()

    def resolve_all_orders(self, info):
        return Order.objects.all()

    def resolve_customer(self, info, id):
        return Customer.objects.get(pk=id)

    def resolve_product(self, info, id):
        return Product.objects.get(pk=id)

    def resolve_order(self, info, id):
        return Order.objects.get(pk=id)

# Mutations
class CreateCustomer(graphene.Mutation):
    class Arguments:
        input = CustomerInput(required=True)

    customer = graphene.Field(CustomerType)
    message = graphene.String()

    @staticmethod
    def mutate(root, info, input):
        if not re.match(r'^[^@]+@[^@]+\.[^@]+$', input.email):
            raise ValidationError("Invalid email format")
            
        if input.phone and not re.match(r'^(\+\d{1,15}|\d{3}-\d{3}-\d{4})$', input.phone):
            raise ValidationError("Invalid phone format. Use +1234567890 or 123-456-7890")

        try:
            customer = Customer.objects.create(
                name=input.name,
                email=input.email,
                phone=input.phone
            )
            return CreateCustomer(customer=customer, message="Customer created successfully")
        except Exception as e:
            raise ValidationError(str(e))

class BulkCreateCustomers(graphene.Mutation):
    class Arguments:
        input = graphene.List(CustomerInput, required=True)

    customers = graphene.List(CustomerType)
    errors = graphene.List(graphene.String)

    @staticmethod
    @transaction.atomic
    def mutate(root, info, input):
        customers = []
        errors = []
        
        for idx, customer_data in enumerate(input):
            try:
                if Customer.objects.filter(email=customer_data.email).exists():
                    raise ValidationError(f"Email {customer_data.email} already exists")
                    
                customer = Customer.objects.create(
                    name=customer_data.name,
                    email=customer_data.email,
                    phone=customer_data.phone
                )
                customers.append(customer)
            except Exception as e:
                errors.append(f"Row {idx+1}: {str(e)}")
                continue
        
        return BulkCreateCustomers(customers=customers, errors=errors)

class CreateProduct(graphene.Mutation):
    class Arguments:
        input = ProductInput(required=True)

    product = graphene.Field(ProductType)
    message = graphene.String()

    @staticmethod
    def mutate(root, info, input):
        if input.price <= 0:
            raise ValidationError("Price must be positive")
            
        if input.stock and input.stock < 0:
            raise ValidationError("Stock cannot be negative")

        product = Product.objects.create(
            name=input.name,
            price=input.price,
            stock=input.stock if input.stock else 0
        )
        return CreateProduct(product=product, message="Product created successfully")

class CreateOrder(graphene.Mutation):
    class Arguments:
        input = OrderInput(required=True)

    order = graphene.Field(OrderType)
    message = graphene.String()

    @staticmethod
    @transaction.atomic
    def mutate(root, info, input):
        try:
            customer = Customer.objects.get(pk=input.customer_id)
        except Customer.DoesNotExist:
            raise ValidationError("Customer does not exist")

        if not input.product_ids:
            raise ValidationError("At least one product is required")

        products = []
        total_amount = 0
        
        for product_id in input.product_ids:
            try:
                product = Product.objects.get(pk=product_id)
                products.append(product)
                total_amount += product.price
            except Product.DoesNotExist:
                raise ValidationError(f"Product with ID {product_id} does not exist")

        order = Order.objects.create(
            customer=customer,
            total_amount=total_amount
        )
        order.products.set(products)
        
        return CreateOrder(order=order, message="Order created successfully")

class Mutation(graphene.ObjectType):
    create_customer = CreateCustomer.Field()
    bulk_create_customers = BulkCreateCustomers.Field()
    create_product = CreateProduct.Field()
    create_order = CreateOrder.Field()

schema = graphene.Schema(query=Query, mutation=Mutation)