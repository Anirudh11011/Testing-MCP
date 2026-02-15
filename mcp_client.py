# mcp_client.py
import asyncio
import nest_asyncio
import json

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

nest_asyncio.apply()

SERVER_FILE = "mcp_server.py"

# Use a real file for stderr to avoid fileno() issue in Colab
_errlog_file = open("mcp_stderr.log", "w")


def _parse_content_blocks(content):
    """
    MCP often returns content blocks (TextContent) with JSON in .text.
    This converts them into Python dict/list when possible.
    """
    if not isinstance(content, list):
            return content

    parsed = []

    for item in content:
        text = getattr(item, "text", None)
        if isinstance(text, str):
            t = text.strip()
            try:
                parsed.append(json.loads(t))
            except Exception:
                parsed.append(t)
        else:
            parsed.append(item)

    # 🔥 NEW: if only one item, return it directly
    if len(parsed) == 1:
        return parsed[0]

    return parsed


async def _call_tool_async(tool_name: str, args: dict):
    server_params = StdioServerParameters(command="python", args=[SERVER_FILE])
    async with stdio_client(server_params, errlog=_errlog_file) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(tool_name, args)
            return _parse_content_blocks(result.content)


def call_tool(tool_name: str, **kwargs):
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(_call_tool_async(tool_name, kwargs))


def list_tools():
    async def _list_async():
        server_params = StdioServerParameters(command="python", args=[SERVER_FILE])
        async with stdio_client(server_params, errlog=_errlog_file) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                return await session.list_tools()

    loop = asyncio.get_event_loop()
    return loop.run_until_complete(_list_async())
