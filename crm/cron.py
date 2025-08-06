from datetime import datetime
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

def update_low_stock():
    """Update low-stock products via GraphQL mutation"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    try:
        transport = RequestsHTTPTransport(
            url="http://localhost:8000/graphql",
            verify=True,
            retries=3,
        )
        client = Client(transport=transport, fetch_schema_from_transport=True)
        
        mutation = gql("""
            mutation {
                updateLowStockProducts {
                    products {
                        id
                        name
                        stock
                    }
                    message
                }
            }
        """)
        
        result = client.execute(mutation)
        updates = result.get('updateLowStockProducts', {})
        
        log_entry = f"[{timestamp}] {updates.get('message', 'No updates')}\n"
        
        for product in updates.get('products', []):
            log_entry += (f"  - Updated {product['name']} "
                        f"(New stock: {product['stock']})\n")
        
        with open("/tmp/low_stock_updates_log.txt", "a") as log_file:
            log_file.write(log_entry)
            
    except Exception as e:
        error_msg = f"[{timestamp}] Error: {str(e)}\n"
        with open("/tmp/low_stock_updates_log.txt", "a") as log_file:
            log_file.write(error_msg)
