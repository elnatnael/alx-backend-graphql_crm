from celery import shared_task
from datetime import datetime
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport
import requests  # Added import for requests

@shared_task
def generate_crm_report():
    """Generate weekly CRM report via GraphQL"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    try:
        transport = RequestsHTTPTransport(
            url="http://localhost:8000/graphql",
            verify=True,
            retries=3,
        )
        client = Client(transport=transport, fetch_schema_from_transport=True)
        
        query = gql("""
            query {
                totalCustomers
                totalOrders
                totalRevenue
            }
        """)
        
        result = client.execute(query)
        
        report = (
            f"{timestamp} - Report: "
            f"{result['totalCustomers']} customers, "
            f"{result['totalOrders']} orders, "
            f"${result['totalRevenue']:,.2f} revenue"
        )
        
        with open("/tmp/crm_report_log.txt", "a") as log_file:
            log_file.write(report + "\n")
            
        return report
        
    except Exception as e:
        error_msg = f"{timestamp} - Report Error: {str(e)}"
        with open("/tmp/crm_report_log.txt", "a") as log_file:
            log_file.write(error_msg + "\n")
        raise