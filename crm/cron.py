from datetime import datetime
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

def update_low_stock():
    """Execute low stock update mutation and log results"""
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
        data = result.get('updateLowStockProducts', {})
        
        # Format log entry
        log_entry = f"[{timestamp}] {data.get('message', '')}\n"
        for product in data.get('products', []):
            log_entry += f"  - {product['name']} (Stock: {product['stock']})\n"
        
        with open("/tmp/low_stock_updates_log.txt", "a") as f:
            f.write(log_entry)
            
    except Exception as e:
        error_msg = f"[{timestamp}] Error: {str(e)}\n"
        with open("/tmp/low_stock_updates_log.txt", "a") as f:
            f.write(error_msg)
