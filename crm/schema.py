import re
from decimal import Decimal
from django.db import transaction
import graphene
from graphene import relay
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
from graphql import GraphQLError
from django.utils.timezone import now
import django_filters

from .models import Customer, Product, Order


# --- Filters ---

class CustomerFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(field_name='name', lookup_expr='icontains')
    email = django_filters.CharFilter(field_name='email', lookup_expr='icontains')
    phone_pattern = django_filters.CharFilter(method='filter_phone_pattern')

    class Meta:
        model = Customer
        fields = ['name', 'email', 'phone_pattern']

    def filter_phone_pattern(self, queryset, name, value):
        return queryset.filter(phone__startswith=value)


class ProductFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(field_name='name', lookup_expr='icontains')
    price_gte = django_filters.NumberFilter(field_name='price', lookup_expr='gte')
    price_lte = django_filters.NumberFilter(field_name='price', lookup_expr='lte')
    stock_gte = django_filters.NumberFilter(field_name='stock', lookup_expr='gte')
    stock_lte = django_filters.NumberFilter(field_name='stock', lookup_expr='lte')

    class Meta:
        model = Product
        fields = ['name', 'price_gte', 'price_lte', 'stock_gte', 'stock_lte']


# --- Graphene Types ---

class CustomerType(DjangoObjectType):
    class Meta:
        model = Customer
        fields = ("id", "name", "email", "phone")
        interfaces = (relay.Node,)
        filterset_class = CustomerFilter


class ProductType(DjangoObjectType):
    class Meta:
        model = Product
        fields = ("id", "name", "price", "stock")
        interfaces = (relay.Node,)
        filterset_class = ProductFilter


class OrderType(DjangoObjectType):
    class Meta:
        model = Order
        interfaces = (relay.Node,)
        fields = '__all__'


class OrderConnection(relay.Connection):
    class Meta:
        node = OrderType


# --- Input Types for mutations ---

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


# --- Validators ---

def validate_phone(phone):
    if phone is None:
        return True
    pattern = re.compile(r"^\+?\d{1,4}?[-.\s]?\(?\d+\)?[-.\s]?\d+[-.\s]?\d+$")
    return bool(pattern.match(phone))


def validate_email_unique(email):
    return not Customer.objects.filter(email=email).exists()


# --- Mutations ---

class CreateCustomer(graphene.Mutation):
    class Arguments:
        input = CustomerInput(required=True)

    customer = graphene.Field(CustomerType)
    message = graphene.String()

    def mutate(self, info, input):
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


# --- Filter Input for Orders ---

class OrderFilterInput(graphene.InputObjectType):
    customerName = graphene.String()
    productName = graphene.String()
    totalAmountGte = graphene.Float()
    totalAmountLte = graphene.Float()
    orderDateGte = graphene.Date()
    orderDateLte = graphene.Date()


# --- Query ---

class Query(graphene.ObjectType):
    all_customers = DjangoFilterConnectionField(CustomerType, filterset_class=CustomerFilter)
    all_products = DjangoFilterConnectionField(ProductType, filterset_class=ProductFilter)
    all_orders = relay.ConnectionField(
        OrderConnection,
        filter=graphene.Argument(OrderFilterInput),
    )
   


    def resolve_all_orders(root, info, **kwargs):
        filter = kwargs.get("filter")
        qs = Order.objects.all()
        if filter:
            if filter.customerName:
                qs = qs.filter(customer__name__icontains=filter.customerName)
            if filter.productName:
                qs = qs.filter(products__name__icontains=filter.productName).distinct()
            if filter.totalAmountGte is not None:
                qs = qs.filter(total_amount__gte=filter.totalAmountGte)
            if filter.totalAmountLte is not None:
                qs = qs.filter(total_amount__lte=filter.totalAmountLte)
            if filter.orderDateGte:
                qs = qs.filter(order_date__gte=filter.orderDateGte)
            if filter.orderDateLte:
                qs = qs.filter(order_date__lte=filter.orderDateLte)
        return qs


# --- Mutation ---

class Mutation(graphene.ObjectType):
    create_customer = CreateCustomer.Field()
    bulk_create_customers = BulkCreateCustomers.Field()
    create_product = CreateProduct.Field()
    create_order = CreateOrder.Field()


# --- Schema ---

schema = graphene.Schema(query=Query, mutation=Mutation)
