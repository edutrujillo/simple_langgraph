# Tool definitions for the MCP Salesforce server
# Each tool describes a callable operation, its parameters, and its purpose.

TOOLS = [
    {
        "name": "list_salesforce_objects",
        "description": "Lists all accessible Salesforce object types (e.g., Account, Contact, Case). Useful for discovering what data can be queried.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "describe_salesforce_object",
        "description": "Provides schema details (fields, types, labels) for a specific Salesforce object. Helps in understanding object structure for SOQL or record creation.",
        "parameters": {
            "type": "object",
            "properties": {
                "object_name": {"type": "string", "description": "The API name of the Salesforce object (e.g., 'Account', 'Case')."}
            },
            "required": ["object_name"]
        }
    },
    {
        "name": "query_salesforce_records",
        "description": "Executes a SOQL query against Salesforce to retrieve records. Use for searching or fetching specific data.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The SOQL query string to execute (e.g., 'SELECT Name, Phone FROM Account WHERE Industry = 'Technology'')."}
            },
            "required": ["query"]
        }
    }
]

# To add a new tool, append a new dictionary to the TOOLS list with the required fields.
# Each tool should have a unique 'name', a 'description', and a 'parameters' schema. 