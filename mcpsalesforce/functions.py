# Salesforce REST API integration functions for MCP tools
import os
import requests
from typing import List, Dict, Any

# Environment variables for Salesforce connection
SALESFORCE_ACCESS_TOKEN = os.getenv("SALESFORCE_ACCESS_TOKEN")
SALESFORCE_DOMAIN = os.getenv("SALESFORCE_DOMAIN")
SALESFORCE_VERSION = os.getenv("SALESFORCE_VERSION")

# Common headers for Salesforce REST API requests
HEADERS = {
    "Authorization": f"Bearer {SALESFORCE_ACCESS_TOKEN}",
    "Content-Type": "application/json"
}

# List all accessible Salesforce object types (e.g., Account, Contact, Case)
def list_salesforce_objects() -> List[str]:
    url = f"{SALESFORCE_DOMAIN}/services/data/{SALESFORCE_VERSION}/sobjects/"
    resp = requests.get(url, headers=HEADERS)
    resp.raise_for_status()
    data = resp.json()
    # The 'sobjects' key contains a list of objects, each with a 'name' field
    return [obj['name'] for obj in data.get('sobjects', [])]

# Get schema details (fields, types, labels) for a specific Salesforce object
def describe_salesforce_object(object_name: str) -> List[Dict[str, Any]]:
    url = f"{SALESFORCE_DOMAIN}/services/data/{SALESFORCE_VERSION}/sobjects/{object_name}/describe/"
    resp = requests.get(url, headers=HEADERS)
    resp.raise_for_status()
    data = resp.json()
    fields = []
    for field in data.get('fields', []):
        field_info = {
            "name": field.get("name"),
            "type": field.get("type"),
            "label": field.get("label"),
        }
        # Add picklist values if present
        if field.get("picklistValues"):
            field_info["values"] = [v["value"] for v in field["picklistValues"] if v.get("active", True)]
        # Add formula if present
        if field.get("calculatedFormula"):
            field_info["formula"] = field["calculatedFormula"]
        # Add referenceTo if present
        if field.get("referenceTo"):
            field_info["referenceTo"] = field["referenceTo"]
        fields.append(field_info)
    return fields

# Execute a SOQL query against Salesforce to retrieve records
def query_salesforce_records(query: str) -> List[Dict[str, Any]]:
    import urllib.parse
    url = f"{SALESFORCE_DOMAIN}/services/data/{SALESFORCE_VERSION}/query/?q={urllib.parse.quote(query)}"
    resp = requests.get(url, headers=HEADERS)
    resp.raise_for_status()
    data = resp.json()
    return data.get("records", []) 