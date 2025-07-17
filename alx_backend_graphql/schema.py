import graphene

# Step 1: Create CRMQuery class
class CRMQuery(graphene.ObjectType):
    hello = graphene.String()

    def resolve_hello(self, info):
        return "Hello, GraphQL!"

# Step 2: Inherit CRMQuery in the main Query class
class Query(CRMQuery, graphene.ObjectType):
    pass

# Step 3: Create the schema
schema = graphene.Schema(query=Query)
