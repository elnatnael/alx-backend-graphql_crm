#!/usr/bin/env python3
"""
CRM heartbeat monitoring with GraphQL check
"""

from datetime import datetime
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport
import os

def log_crm_heartbeat():
    """Log CRM heartbeat and optionally check GraphQL endpoint"""
    timestamp = datetime.now().strftime("%d/%m/%Y-%H:%M:%S")
    log_message = f"{timestamp} CRM is alive"
    
    # Optional GraphQL endpoint check
    try:
        transport = RequestsHTTPTransport(
            url="http://localhost:8000/graphql",
            verify=True,
            retries=1,
        )
        client = Client(transport=transport, fetch_schema_from_transport=True)
        query = gql("query { hello }")
        result = client.execute(query)
        if result.get('hello'):
            log_message += " - GraphQL endpoint responsive"
    except Exception as e:
        log_message += f" - GraphQL check failed: {str(e)}"
    
    # Append to log file
    with open("/tmp/crm_heartbeat_log.txt", "a") as log_file:
        log_file.write(log_message + "\n")
