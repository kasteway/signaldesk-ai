"""Minimal stdio MCP server exposing sourced complaint analysis tools.

Implements JSON-RPC initialize, tools/list and tools/call over newline-delimited
messages. It does not call external services or receive consumer-level text.
"""
from __future__ import annotations
import json
import sys
from .core import ROOT, build
from .brief import answer

TOOLS = [
    {"name":"get_overview","description":"Get the dataset scope, top complaint issues, and alert count.","inputSchema":{"type":"object","properties":{}}},
    {"name":"get_signals","description":"Get weekly issue-count signals from the documented screening rule.","inputSchema":{"type":"object","properties":{"issue":{"type":"string","description":"Optional issue name filter"}}}},
    {"name":"ask_evidence","description":"Retrieve a grounded answer with local project-file citations.","inputSchema":{"type":"object","properties":{"question":{"type":"string"}},"required":["question"]}},
]

def call(name: str, arguments: dict) -> dict:
    data = json.loads((ROOT / "web" / "dashboard.json").read_text())
    if name == "get_overview":
        return {"period":data["period"], "total":data["total"], "top_issues":data["issues"][:5], "signal_count":len(data["signals"]), "source":"web/dashboard.json"}
    if name == "get_signals":
        issue = arguments.get("issue", "").casefold()
        return {"signals":[s for s in data["signals"] if issue in s["issue"].casefold()], "method":data["method"], "source":"web/dashboard.json"}
    if name == "ask_evidence":
        return answer(arguments["question"])
    raise ValueError("Unknown tool")

def handle(message: dict) -> dict | None:
    method = message.get("method")
    ident = message.get("id")
    if method == "notifications/initialized":
        return None
    if method == "initialize":
        result = {"protocolVersion":"2025-03-26","capabilities":{"tools":{}},"serverInfo":{"name":"signaldesk-ai","version":"1.0.0"}}
    elif method == "tools/list":
        result = {"tools":TOOLS}
    elif method == "tools/call":
        params = message.get("params", {})
        try:
            value = call(params["name"], params.get("arguments", {}))
            result = {"content":[{"type":"text","text":json.dumps(value)}]}
        except (KeyError, ValueError) as exc:
            result = {"content":[{"type":"text","text":str(exc)}],"isError":True}
    else:
        if ident is None:
            return None
        return {"jsonrpc":"2.0","id":ident,"error":{"code":-32601,"message":"Method not found"}}
    return {"jsonrpc":"2.0","id":ident,"result":result} if ident is not None else None

def main() -> None:
    if not (ROOT / "web" / "dashboard.json").exists():
        build()
    for line in sys.stdin:
        try:
            response = handle(json.loads(line))
        except Exception as exc:
            response = {"jsonrpc":"2.0","id":None,"error":{"code":-32603,"message":str(exc)}}
        if response is not None:
            print(json.dumps(response), flush=True)

if __name__ == "__main__":
    main()
