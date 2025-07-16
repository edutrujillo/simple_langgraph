# FastAPI MCP server for Salesforce tool integration
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Any, Dict
from tools import TOOLS
from functions import list_salesforce_objects, describe_salesforce_object, query_salesforce_records

# Create FastAPI app
app = FastAPI()

# Enable CORS for all origins (for development/demo purposes)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Endpoint: Return JSON-RPC tool definitions for MCP tools
@app.get("/tools")
async def get_tools():
    return {
        "jsonrpc": "2.0",
        "result": {
            "status": "success",
            "tools": TOOLS
        },
        "id": 0
    }

# Endpoint: JSON-RPC tool call dispatcher
@app.post("/tools/call")
async def call_tool(request: Request):
    body = await request.json()
    method = body.get("method")
    params = body.get("params", {})
    tool_name = params.get("name")
    arguments = params.get("arguments", {})
    req_id = body.get("id")

    try:
        # Route to the correct tool function based on tool_name
        if tool_name == "list_salesforce_objects":
            objects = list_salesforce_objects()
            return {
                "jsonrpc": "2.0",
                "result": {
                    "status": "success",
                    "tool_name": tool_name,
                    "objects": objects
                },
                "id": req_id
            }
        elif tool_name == "describe_salesforce_object":
            object_name = arguments.get("object_name")
            if not object_name:
                raise ValueError("Missing required parameter: object_name")
            fields = describe_salesforce_object(object_name)
            return {
                "jsonrpc": "2.0",
                "result": {
                    "status": "success",
                    "tool_name": tool_name,
                    "object_name": object_name,
                    "fields": fields
                },
                "id": req_id
            }
        elif tool_name == "query_salesforce_records":
            query = arguments.get("query")
            if not query:
                raise ValueError("Missing required parameter: query")
            records = query_salesforce_records(query)
            return {
                "jsonrpc": "2.0",
                "result": {
                    "status": "success",
                    "tool_name": tool_name,
                    "records": records,
                    "totalSize": len(records),
                    "done": True
                },
                "id": req_id
            }
        else:
            raise Exception(f"Unknown tool: {tool_name}")
    except Exception as e:
        # Return error in JSON-RPC format
        return JSONResponse(
            status_code=200,
            content={
                "jsonrpc": "2.0",
                "error": {
                    "code": -32000,
                    "message": str(e),
                    "data": {
                        "salesforce_error_code": "INVALID_SOQL_SYNTAX",
                        "details": arguments.get("query", "")
                    }
                },
                "id": req_id
            }
        )

# Run the server if executed directly
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8010) 