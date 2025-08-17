import graphene
from graphene import InputObjectType, Mutation, Field, List, String, ID, Decimal, Int, DateTime
from graphene_django.types import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
from .models import Customer, Product, Order
from .utils import validate_email, validate_phone
from django.db import transaction
from datetime import datetime

# Types
class CustomerType(DjangoObjectType):
    class Meta:
        model = Customer
        interfaces = (graphene.relay.Node,)
        filter_fields = {
            'name': ['exact', 'icontains', 'istartswith'],
            'email': ['exact', 'icontains'],
            'phone': ['exact', 'icontains']
        }

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
    name = graphene.String(required=True)
    email = graphene.String(required=True)
    phone = graphene.String()

class ProductInput(InputObjectType):
    name = graphene.String(required=True)
    price = graphene.Decimal(required=True)
    stock = graphene.Int(default_value=0)

class OrderInput(InputObjectType):
    customer_id = graphene.ID(required=True)
    product_ids = graphene.List(graphene.ID, required=True)
    order_date = graphene.DateTime()

# Query Class
class Query(graphene.ObjectType):
    all_customers = DjangoFilterConnectionField(CustomerType)
    customer = graphene.Field(CustomerType, id=graphene.ID())
    
    def resolve_customer(self, info, id):
        return Customer.objects.get(pk=id)

# Mutations
class CreateCustomer(graphene.Mutation):
    class Arguments:
        input = CustomerInput(required=True)
    
    customer = graphene.Field(CustomerType)
    message = graphene.String()
    
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

# ... [keep all your other mutation classes unchanged] ...

# Mutation Class
class Mutation(graphene.ObjectType):
    create_customer = CreateCustomer.Field()
    bulk_create_customers = BulkCreateCustomers.Field()
    create_product = CreateProduct.Field()
    create_order = CreateOrder.Field()

schema = graphene.Schema(query=Query, mutation=Mutation)