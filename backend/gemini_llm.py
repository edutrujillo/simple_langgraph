import os
import google.generativeai as genai
import requests
import re

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = "models/gemini-2.5-flash-lite-preview-06-17"
MCP_TOOLS = "http://localhost:8010/tools"

genai.configure(api_key=GEMINI_API_KEY)

def ask_gemini(prompt: str) -> str:
    # Fetch MCP tools
    try:
        resp = requests.get(MCP_TOOLS)
        resp.raise_for_status()
        tools = resp.json().get("result", {}).get("tools", [])
    except Exception as e:
        print(f"[Gemini] Failed to fetch MCP tools: {e}")
        tools = []
    if not tools:
        return "failback"
    # Build tool list string for LLM
    tool_list = "\n".join([f"- {tool['name']}: {tool['description']}" for tool in tools])
    tool_names = [tool['name'] for tool in tools]
    llm_prompt = (
        "Given the following user request and the list of available tools, "
        "decide which tool (by name) is best suited to resolve the request. "
        "If none are suitable, answer failback.\n"
        f"User request: {prompt}\n"
        f"Available tools:\n{tool_list}\n"
        "Respond with only the tool name (e.g., 'list_salesforce_objects') or 'failback'."
    )
    response = genai.GenerativeModel(MODEL_NAME).generate_content(llm_prompt)
    print("[Gemini tool match raw]", response)
    if hasattr(response, 'text'):
        tool_name = response.text.strip().split()[0]  # Only first word, in case LLM adds extra
    elif hasattr(response, 'candidates') and response.candidates:
        tool_name = response.candidates[0].text.strip().split()[0]
    else:
        return "failback"
    # Validate tool name
    if tool_name in tool_names:
        print("returned tool: " + tool_name)
        return tool_name
    return "failback"

def ask_gemini_final(prompt: object) -> str:
    final_prompt = (
        "Please read the following JSON response and provide a natural language summary of its contents. "
        "Make the summary as clear and human-friendly as possible. If the response include a query please maintain it\n"
        f"JSON:\n{prompt}"
    )
    response = genai.GenerativeModel(MODEL_NAME).generate_content(final_prompt)
    print("[Gemini SOQL raw]", response)
    if hasattr(response, 'text'):
        return response.text.strip()
    elif hasattr(response, 'candidates') and response.candidates:
        return response.candidates[0].text.strip()
    else:
        return str(response) 

def extract_soql_from_prompt(prompt: str) -> str:
    soql_prompt = (
        "Convert the following user request into a Salesforce SOQL query. "
        "Only return the SOQL query, nothing else. Remove all decorators\nRequest: " + prompt
    )
    response = genai.GenerativeModel(MODEL_NAME).generate_content(soql_prompt)
    print("[Gemini SOQL raw]", response)
    if hasattr(response, 'text'):
        soql = response.text.strip()
    elif hasattr(response, 'candidates') and response.candidates:
        soql = response.candidates[0].text.strip()
    else:
        soql = str(response)
    # Remove leading 'sql\n' or 'soql\n' (case-insensitive)
    soql = re.sub(r'^(sql|soql)\s*\n', '', soql, flags=re.IGNORECASE)
    # Clean SOQL: allow only letters, numbers, spaces, and SOQL symbols
    soql = re.sub(r"[^a-zA-Z0-9 \n\t\(\)\,\.\*\=\>\<\%\_\'\"-]", "", soql)
    return soql.strip()

def extract_objectname_from_prompt(prompt: str) -> str:
    soql_prompt = (
        "Get from the following user request the Salesforce object that the user wants to know de details. "
        "Only return the Object Name, nothing else.\nRequest: " + prompt
    )
    response = genai.GenerativeModel(MODEL_NAME).generate_content(soql_prompt)
    print("[Gemini SOQL raw]", response)
    if hasattr(response, 'text'):
        soql = response.text.strip()
    elif hasattr(response, 'candidates') and response.candidates:
        soql = response.candidates[0].text.strip()
    else:
        soql = str(response)
    # Clean SOQL: allow only letters, numbers, spaces, and SOQL symbols
    soql = re.sub(r"[^a-zA-Z0-9 \n\t\(\)\,\.\*\=\>\<\%\_\'\"-]", "", soql)
    return soql.strip() 