import graphene
from graphene_django import DjangoObjectType
from crm.models import Product
from products.models import Product

class ProductType(DjangoObjectType):
    class Meta:
        model = Product
        fields = "__all__"

class UpdateLowStockProducts(graphene.Mutation):
    class Arguments:
        pass  # No arguments needed for this mutation

    products = graphene.List(ProductType)
    message = graphene.String()

    @classmethod
    def mutate(cls, root, info):
        # Get products with stock < 10
        low_stock_products = Product.objects.filter(stock__lt=10)
        updated_products = []
        
        # Update each product's stock
        for product in low_stock_products:
            product.stock += 10
            product.save()
            updated_products.append(product)
        
        return UpdateLowStockProducts(
            products=updated_products,
            message=f"Updated {len(updated_products)} low-stock products"
        )

class Mutation(graphene.ObjectType):
    update_low_stock_products = UpdateLowStockProducts.Field()

schema = graphene.Schema(mutation=Mutation)
