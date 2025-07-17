import re
from decimal import Decimal
from django.db import transaction
import graphene
from graphene_django import DjangoObjectType
from .models import Customer, Product, Order
from django.utils.timezone import now
from graphql import GraphQLError


# DjangoObjectTypes
class CustomerType(DjangoObjectType):
    class Meta:
        model = Customer
        fields = ("id", "name", "email", "phone")


class ProductType(DjangoObjectType):
    class Meta:
        model = Product
        fields = ("id", "name", "price", "stock")


class OrderType(DjangoObjectType):
    class Meta:
        model = Order
        fields = ("id", "customer", "products", "total_amount", "order_date")


# Input Types
class CustomerInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    email = graphene.String(required=True)
    phone = graphene.String(required=False)


class ProductInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    price = graphene.Decimal(required=True)
    stock = graphene.Int(required=False)


class CreateOrderInput(graphene.InputObjectType):
    customer_id = graphene.ID(required=True)
    product_ids = graphene.List(graphene.ID, required=True)
    order_date = graphene.DateTime(required=False)


# Validators
def validate_phone(phone):
    if phone is None:
        return True
    pattern = re.compile(r"^\+?\d{1,4}?[-.\s]?\(?\d+\)?[-.\s]?\d+[-.\s]?\d+$")
    return bool(pattern.match(phone))


def validate_email_unique(email):
    return not Customer.objects.filter(email=email).exists()


# Mutations
class CreateCustomer(graphene.Mutation):
    class Arguments:
        input = CustomerInput(required=True)

    customer = graphene.Field(CustomerType)
    message = graphene.String()

    def mutate(self, info, input):
        # Validation
        if not validate_email_unique(input.email):
            raise GraphQLError("Email already exists.")

        if input.phone and not validate_phone(input.phone):
            raise GraphQLError("Invalid phone number format.")

        customer = Customer(
            name=input.name,
            email=input.email,
            phone=input.phone,
        )
        customer.save()
        return CreateCustomer(customer=customer, message="Customer created successfully.")


class BulkCreateCustomers(graphene.Mutation):
    class Arguments:
        input = graphene.List(CustomerInput, required=True)

    customers = graphene.List(CustomerType)
    errors = graphene.List(graphene.String)

    @transaction.atomic
    def mutate(self, info, input):
        created_customers = []
        errors = []

        for idx, customer_input in enumerate(input):
            # Validate email uniqueness for each input
            if not validate_email_unique(customer_input.email):
                errors.append(f"Customer at index {idx} has duplicate email: {customer_input.email}")
                continue
            if customer_input.phone and not validate_phone(customer_input.phone):
                errors.append(f"Customer at index {idx} has invalid phone number: {customer_input.phone}")
                continue

            customer = Customer(
                name=customer_input.name,
                email=customer_input.email,
                phone=customer_input.phone,
            )
            customer.save()
            created_customers.append(customer)

        return BulkCreateCustomers(customers=created_customers, errors=errors)


class CreateProduct(graphene.Mutation):
    class Arguments:
        input = ProductInput(required=True)

    product = graphene.Field(ProductType)

    def mutate(self, info, input):
        if input.price <= 0:
            raise GraphQLError("Price must be a positive decimal.")

        if input.stock is not None and input.stock < 0:
            raise GraphQLError("Stock cannot be negative.")

        stock = input.stock if input.stock is not None else 0

        product = Product(
            name=input.name,
            price=input.price,
            stock=stock,
        )
        product.save()

        return CreateProduct(product=product)


class CreateOrder(graphene.Mutation):
    class Arguments:
        input = CreateOrderInput(required=True)

    order = graphene.Field(OrderType)

    def mutate(self, info, input):
        try:
            customer = Customer.objects.get(pk=input.customer_id)
        except Customer.DoesNotExist:
            raise GraphQLError("Customer with provided ID does not exist.")

        if not input.product_ids or len(input.product_ids) == 0:
            raise GraphQLError("At least one product ID must be provided.")

        products = []
        for product_id in input.product_ids:
            try:
                product = Product.objects.get(pk=product_id)
                products.append(product)
            except Product.DoesNotExist:
                raise GraphQLError(f"Product with ID {product_id} does not exist.")

        total_amount = sum([product.price for product in products])

        order_date = input.order_date if input.order_date else now()

        order = Order(customer=customer, total_amount=total_amount, order_date=order_date)
        order.save()
        order.products.set(products)
        order.save()

        return CreateOrder(order=order)


# Mutation class
class Mutation(graphene.ObjectType):
    create_customer = CreateCustomer.Field()
    bulk_create_customers = BulkCreateCustomers.Field()
    create_product = CreateProduct.Field()
    create_order = CreateOrder.Field()


# Query stub (you should define your actual queries here)
class Query(graphene.ObjectType):
    customers = graphene.List(CustomerType)
    products = graphene.List(ProductType)
    orders = graphene.List(OrderType)

    def resolve_customers(self, info):
        return Customer.objects.all()

    def resolve_products(self, info):
        return Product.objects.all()

    def resolve_orders(self, info):
        return Order.objects.all()


# Finally, create the schema
schema = graphene.Schema(query=Query, mutation=Mutation)
