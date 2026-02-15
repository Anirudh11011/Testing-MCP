from typing import List, Dict, Any, Optional
from mcp.server.fastmcp import FastMCP
from ddgs import DDGS
import requests
from bs4 import BeautifulSoup

mcp = FastMCP("my-tools")


# -------------------------
# Tool 1: Web search
# -------------------------
@mcp.tool()
def web_search(query: str, max_results: int = 6) -> List[Dict[str, Any]]:
    """
    Web search (DuckDuckGo via ddgs).
    Returns list of {title, url, snippet}.
    """
    out: List[Dict[str, Any]] = []
    with DDGS() as ddgs:
        for r in ddgs.text(query, max_results=max_results):
            out.append({
                "title": r.get("title"),
                "url": r.get("href"),
                "snippet": r.get("body"),
            })
    return out


# -------------------------
# Tool 2: Fetch a URL and return readable text
# -------------------------
@mcp.tool()
def fetch_url(url: str, timeout_s: int = 15, max_chars: int = 8000) -> Dict[str, Any]:
    """
    Downloads a page and returns cleaned visible text.
    Useful after search, so LLM can read the page.
    """
    try:
        headers = {"User-Agent": "Mozilla/5.0 (compatible; MCPBot/1.0)"}
        resp = requests.get(url, headers=headers, timeout=timeout_s)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")

        # remove scripts/styles
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()

        text = soup.get_text(separator=" ", strip=True)
        if len(text) > max_chars:
            text = text[:max_chars] + " ...[truncated]"

        return {
            "url": url,
            "status_code": resp.status_code,
            "text": text,
        }
    except Exception as e:
        return {
            "url": url,
            "error": str(e),
        }


# -------------------------
# Tool 3: Simple calculator (example extra tool)
# -------------------------
@mcp.tool()
def calc(expression: str) -> Dict[str, Any]:
    """
    Very small calculator tool.
    Only supports safe characters: digits + - * / ( ) . and spaces.
    """
    allowed = set("0123456789+-*/(). ")
    if any(c not in allowed for c in expression):
        return {"error": "Unsupported characters in expression."}
    try:
        value = eval(expression, {"__builtins__": {}}, {})
        return {"expression": expression, "result": value}
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    # IMPORTANT: stdio transport is the common pattern for Colab/local
    mcp.run(transport="stdio")
