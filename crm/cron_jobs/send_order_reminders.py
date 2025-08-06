#!/usr/bin/env python3
"""
Script to send reminders for pending orders via GraphQL
"""

from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport
from datetime import datetime, timedelta
import os

# GraphQL endpoint configuration
transport = RequestsHTTPTransport(
    url="http://localhost:8000/graphql",
    verify=True,
    retries=3,
)
client = Client(transport=transport, fetch_schema_from_transport=True)

# Calculate date range (last 7 days)
one_week_ago = (datetime.now() - timedelta(days=7)).isoformat()

# GraphQL query to get pending orders
query = gql("""
    query GetPendingOrders($since: DateTime!) {
        pendingOrders(since: $since) {
            id
            customer {
                email
            }
        }
    }
""")

def send_order_reminders():
    """Fetch and log pending orders from GraphQL endpoint"""
    try:
        # Execute GraphQL query
        result = client.execute(query, variable_values={"since": one_week_ago})
        orders = result.get('pendingOrders', [])
        
        # Prepare log entry
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entries = [f"[{timestamp}] Processing {len(orders)} orders"]
        
        # Log each order
        for order in orders:
            log_entries.append(
                f"Order ID: {order['id']}, Customer Email: {order['customer']['email']}"
            )
        
        # Write to log file
        with open("/tmp/order_reminders_log.txt", "a") as log_file:
            log_file.write("\n".join(log_entries) + "\n")
        
        print("Order reminders processed!")
        
    except Exception as e:
        error_msg = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Error: {str(e)}"
        with open("/tmp/order_reminders_log.txt", "a") as log_file:
            log_file.write(error_msg + "\n")
        print("Error processing order reminders!")

if __name__ == "__main__":
    send_order_reminders()
