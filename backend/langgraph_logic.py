# Imports and dependencies
from typing import TypedDict
from langgraph.graph import StateGraph, END
from gemini_llm import ask_gemini, extract_soql_from_prompt, ask_gemini_final, extract_objectname_from_prompt
import requests
import json

# Define the state for the graph. This holds all data passed between nodes.
class State(TypedDict, total=False):
    prompt: str  # The user's input
    result: str  # The final result to return
    _mcp_log: list  # Log of all MCP server callouts and responses
    _route: str  # Routing decision from Gemini
    _response: object  # Raw response from MCP server
    _finalanswer: object  # Naturalized answer from Gemini

# Node: entry_node (conditional router)
def entry_node(state: State) -> dict:
    print("[Node] entry_node")
    # Use Gemini to decide which tool (if any) should handle the prompt
    answer = ask_gemini(state["prompt"])
    state["_route"] = answer.strip().lower()
    return state

# Node: query_salesforce_records - Calls MCP to run a SOQL query

def query_salesforce_records(state: State) -> dict:
    print("[Node] query_salesforce_records")
    # Extract SOQL query from the prompt using Gemini
    query = extract_soql_from_prompt(state["prompt"])
    print("     " + query)
    json_rpc_body = {
        "jsonrpc": "2.0",
        "method": "call",
        "params": {
            "name": "query_salesforce_records",
            "arguments": {"query": query}
        },
        "id": 1
    }
    # Ensure MCP log exists
    if "_mcp_log" not in state:
        state["_mcp_log"] = []
    # Log the callout
    state["_mcp_log"].append({
        "type": "call",
        "tool": "query_salesforce_records",
        "payload": json_rpc_body
    })
    try:
        # Make the MCP server call
        resp = requests.post("http://localhost:8010/tools/call", json=json_rpc_body)
        resp.raise_for_status()
        data = resp.json()
        print(data)
        state["_response"] = data
        # Log the response
        state["_mcp_log"].append({
            "type": "response",
            "tool": "query_salesforce_records",
            "response": data
        })
        return state
    except Exception as e:
        print(f"[query_salesforce_records] MCP call failed: {e}")
        state["_mcp_log"].append({
            "type": "response",
            "tool": "query_salesforce_records",
            "response": {"error": str(e)}
        })
        return {"result": f"MCP call failed: {e}"}

# Node: describe_salesforce_object - Calls MCP to get object schema details
def describe_salesforce_object(state: State) -> dict:
    print("[Node] describe_salesforce_object")
    # Extract object name from the prompt using Gemini
    object_name = extract_objectname_from_prompt(state["prompt"])
    json_rpc_body = {
        "jsonrpc": "2.0",
        "method": "call",
        "params": {
            "name": "describe_salesforce_object",
            "arguments": {"object_name": object_name}
        },
        "id": 1
    }
    if "_mcp_log" not in state:
        state["_mcp_log"] = []
    # Log the callout
    state["_mcp_log"].append({
        "type": "call",
        "tool": "describe_salesforce_object",
        "payload": json_rpc_body
    })
    try:
        # Make the MCP server call
        resp = requests.post("http://localhost:8010/tools/call", json=json_rpc_body)
        resp.raise_for_status()
        data = resp.json()
        state["_response"] = data
        # Log the response
        state["_mcp_log"].append({
            "type": "response",
            "tool": "describe_salesforce_object",
            "response": data
        })
        return state
    except Exception as e:
        print(f"[describe_salesforce_object] MCP call failed: {e}")
        state["_mcp_log"].append({
            "type": "response",
            "tool": "describe_salesforce_object",
            "response": {"error": str(e)}
        })
        return {"result": f"MCP call failed: {e}"}

# Node: list_salesforce_objects - Calls MCP to list all objects
def list_salesforce_objects(state: State) -> dict:
    print("[Node] list_salesforce_objects")
    json_rpc_body = {
        "jsonrpc": "2.0",
        "method": "call",
        "params": {
            "name": "list_salesforce_objects",
            "arguments": {}
        },
        "id": 1
    }
    if "_mcp_log" not in state:
        state["_mcp_log"] = []
    # Log the callout
    state["_mcp_log"].append({
        "type": "call",
        "tool": "list_salesforce_objects",
        "payload": json_rpc_body
    })
    try:
        # Make the MCP server call
        resp = requests.post("http://localhost:8010/tools/call", json=json_rpc_body)
        resp.raise_for_status()
        data = resp.json()
        print("     " + str(data))
        state["_response"] = data
        # Log the response
        state["_mcp_log"].append({
            "type": "response",
            "tool": "list_salesforce_objects",
            "response": data
        })
        return state
    except Exception as e:
        print(f"[list_salesforce_objects] MCP call failed: {e}")
        state["_mcp_log"].append({
            "type": "response",
            "tool": "list_salesforce_objects",
            "response": {"error": str(e)}
        })

# Node: final_node - Uses Gemini to naturalize the MCP response
def final_node(state: State) -> dict:
    # Use Gemini to turn the JSON response into a natural language answer
    answer = ask_gemini_final(state.get("_response"))
    state["_finalanswer"] = answer.strip()
    return {"result": state.get("_finalanswer")}

# Node: failback - Handles prompts that can't be mapped to a tool
def failback(state: State) -> dict:
    print("[Node] failback")
    return {"result": "Sorry, your question cannot be translated to a Salesforce context."}

# Conditional router for entry_node
def entry_router(state: State):
    print ("state: " + state.get("_route"))
    return state.get("_route")

# Build the LangGraph workflow
workflow = StateGraph(State)
workflow.add_node("entry_node", entry_node)
workflow.add_node("list_salesforce_objects", list_salesforce_objects)
workflow.add_node("describe_salesforce_object", describe_salesforce_object)
workflow.add_node("query_salesforce_records", query_salesforce_records)
workflow.add_node("failback", failback)
workflow.add_node("final_node", final_node)
workflow.set_entry_point("entry_node")
workflow.add_conditional_edges(
    "entry_node",  entry_router,
    {
        "list_salesforce_objects": "list_salesforce_objects", 
        "describe_salesforce_object": "describe_salesforce_object", 
        "query_salesforce_records": "query_salesforce_records", 
        "failback": "failback"
    }
)
workflow.set_finish_point("failback")
workflow.set_finish_point("final_node")
workflow.add_edge("list_salesforce_objects", "final_node")
workflow.add_edge("describe_salesforce_object", "final_node")
workflow.add_edge("query_salesforce_records", "final_node")
graph = workflow.compile()

# Entrypoint for FastAPI to run the workflow
def run_langgraph(prompt: str) -> dict:
    print('on run_langgraph '+prompt)
    # Initialize state with empty MCP log
    state = {"prompt": prompt, "result": "", "_route": "", "_mcp_log": []}
    result = graph.invoke(state)
    # Return both the final result and the MCP log for frontend display
    return {
        "result": result["result"],
        "mcp_log": result.get("_mcp_log", [])
    } 