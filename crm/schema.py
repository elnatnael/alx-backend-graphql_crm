import graphene
from graphene_django import DjangoObjectType
from crm.models import Product
from products.models import Product


class ProductType(DjangoObjectType):
    class Meta:
        model = Product
        fields = ("id", "name", "stock")  # Only necessary fields

class UpdateLowStockProducts(graphene.Mutation):
    class Arguments:
        pass

    products = graphene.List(ProductType)
    message = graphene.String()

    @classmethod
    def mutate(cls, root, info):
        # Get and update low stock products
        low_stock = Product.objects.filter(stock__lt=10)
        updated = []
        
        for product in low_stock:
            product.stock += 10  # Increment stock by 10
            product.save()
            updated.append(product)
        
        return cls(
            products=updated,
            message=f"Restocked {len(updated)} products"
        )

class Mutation(graphene.ObjectType):
    update_low_stock_products = UpdateLowStockProducts.Field()

schema = graphene.Schema(mutation=Mutation)