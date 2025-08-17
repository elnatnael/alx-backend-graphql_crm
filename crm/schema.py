import graphene
from graphene import InputObjectType, Mutation, Field, List, String, ID, Decimal, Int, DateTime
from graphene_django.types import DjangoObjectType
from .models import Customer, Product, Order
from .utils import validate_email, validate_phone
from django.db import transaction
from datetime import datetime

# Types
class CustomerType(DjangoObjectType):
    class Meta:
        model = Customer

class ProductType(DjangoObjectType):
    class Meta:
        model = Product

class OrderType(DjangoObjectType):
    total_amount = Decimal()
    
    class Meta:
        model = Order
    
    def resolve_total_amount(self, info):
        return sum(product.price for product in self.products.all())

# Input Types
class CustomerInput(InputObjectType):
    name = String(required=True)
    email = String(required=True)
    phone = String()

class ProductInput(InputObjectType):
    name = String(required=True)
    price = Decimal(required=True)
    stock = Int(default_value=0)

class OrderInput(InputObjectType):
    customer_id = ID(required=True)
    product_ids = List(ID, required=True)
    order_date = DateTime()

# Mutations
class CreateCustomer(Mutation):
    class Arguments:
        input = CustomerInput(required=True)
    
    customer = Field(CustomerType)
    message = String()
    
    @staticmethod
    def mutate(root, info, input):
        try:
            # Validate email and phone
            if not validate_email(input.email):
                raise Exception("Invalid email format")
            if hasattr(input, 'phone') and input.phone and not validate_phone(input.phone):
                raise Exception("Invalid phone format")
            
            # Check for existing email
            if Customer.objects.filter(email=input.email).exists():
                raise Exception("Email already exists")
            
            customer = Customer(
                name=input.name,
                email=input.email,
                phone=input.phone if hasattr(input, 'phone') else None
            )
            customer.save()
            
            return CreateCustomer(customer=customer, message="Customer created successfully")
        except Exception as e:
            return CreateCustomer(customer=None, message=str(e))

class BulkCreateCustomers(Mutation):
    class Arguments:
        inputs = List(CustomerInput, required=True)
    
    customers = List(CustomerType)
    errors = List(String)
    
    @staticmethod
    @transaction.atomic
    def mutate(root, info, inputs):
        customers = []
        errors = []
        
        for input in inputs:
            try:
                # Validate email and phone
                if not validate_email(input.email):
                    raise Exception(f"Invalid email format for {input.email}")
                if hasattr(input, 'phone') and input.phone and not validate_phone(input.phone):
                    raise Exception(f"Invalid phone format for {input.email}")
                
                # Check for existing email
                if Customer.objects.filter(email=input.email).exists():
                    raise Exception(f"Email {input.email} already exists")
                
                customer = Customer(
                    name=input.name,
                    email=input.email,
                    phone=input.phone if hasattr(input, 'phone') else None
                )
                customer.save()
                customers.append(customer)
            except Exception as e:
                errors.append(str(e))
                continue
        
        return BulkCreateCustomers(customers=customers, errors=errors)

class CreateProduct(Mutation):
    class Arguments:
        input = ProductInput(required=True)
    
    product = Field(ProductType)
    
    @staticmethod
    def mutate(root, info, input):
        try:
            if input.price <= 0:
                raise Exception("Price must be positive")
            if input.stock < 0:
                raise Exception("Stock cannot be negative")
            
            product = Product(
                name=input.name,
                price=input.price,
                stock=input.stock
            )
            product.save()
            
            return CreateProduct(product=product)
        except Exception as e:
            return CreateProduct(product=None, message=str(e))

class CreateOrder(Mutation):
    class Arguments:
        input = OrderInput(required=True)
    
    order = Field(OrderType)
    
    @staticmethod
    @transaction.atomic
    def mutate(root, info, input):
        try:
            # Validate customer exists
            try:
                customer = Customer.objects.get(pk=input.customer_id)
            except Customer.DoesNotExist:
                raise Exception("Customer does not exist")
            
            # Validate products exist
            if not input.product_ids:
                raise Exception("At least one product is required")
            
            products = []
            for product_id in input.product_ids:
                try:
                    product = Product.objects.get(pk=product_id)
                    products.append(product)
                except Product.DoesNotExist:
                    raise Exception(f"Product with ID {product_id} does not exist")
            
            # Create order
            order = Order(
                customer=customer,
                order_date=input.order_date if hasattr(input, 'order_date') else datetime.now()
            )
            order.save()
            order.products.set(products)
            
            return CreateOrder(order=order)
        except Exception as e:
            return CreateOrder(order=None, message=str(e))

# Mutation Class
class Mutation(graphene.ObjectType):
    create_customer = CreateCustomer.Field()
    bulk_create_customers = BulkCreateCustomers.Field()
    create_product = CreateProduct.Field()
    create_order = CreateOrder.Field()