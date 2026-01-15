# mcp_bridge.py
import asyncio
import json
from typing import Dict, Any, List, Callable, Awaitable, Optional
from dataclasses import dataclass

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool

from lib.logger import get_logger


# ============================================================================
# Tool Registration System
# ============================================================================

@dataclass
class ToolDefinition:
    """Definition of an MCP tool"""
    name: str
    description: str
    input_schema: Dict[str, Any]
    handler: Callable[[Dict[str, Any]], Awaitable[List[Dict[str, Any]]]]
    mcp_tool: Tool

class ToolRegistry:
    """Registry for MCP tools"""

    def __init__(self):
        self._tools: Dict[str, ToolDefinition] = {}

    def register(
        self,
        name: str,
        description: str,
        handler: Callable,
        input_schema: Optional[Dict[str, Any]] = None,
    ):
        schema = input_schema or {"type": "object", "properties": {}}

        mcp_tool = Tool(
            name=name,
            description=description,
            inputSchema=schema,
        )

        self._tools[name] = ToolDefinition(
            name=name,
            description=description,
            input_schema=schema,
            handler=handler,
            mcp_tool=mcp_tool,
        )


    def get_tool_list(self) -> List[Dict[str, Any]]:
        """Get list of all registered tools"""
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "inputSchema": tool.input_schema
            }
            for tool in self._tools.values()
        ]

    async def call_tool(self, name: str, arguments: Dict[str, Any], context: Any) -> List[Dict[str, Any]]:
        """Execute a tool by name"""
        if name not in self._tools:
            raise ValueError(f"Unknown tool: {name}")

        tool = self._tools[name]
        return await tool.handler(context, arguments)


# ============================================================================
# MCP Bridge
# ============================================================================

class MCPBridge:
    """MCP Bridge for sim racing telemetry"""

    def __init__(self, logger):
        self.registry = ToolRegistry()
        self.logger = logger
        self._register_tools()
        self.logger.debug("MCPBridge initialized with tools: %s", list(self.registry._tools.keys()))

    def _register_tools(self):
        """Register all tools"""
        self.registry.register(
            name="get_example_data",
            description="Example tool that returns hardcoded data",
            handler=self.handle_get_example_data,
            input_schema={"type": "object", "properties": {}}
        )

        # Add more tools here
        # self.registry.register(
        #     name="get_telemetry",
        #     description="Get current telemetry",
        #     handler=self.handle_get_telemetry
        # )

    # ========================================================================
    # Tool Handlers
    # ========================================================================

    async def handle_get_example_data(
        self,
        context: "MCPBridge",
        arguments: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        self.logger.debug("handle_get_example_data called with arguments: %s", arguments)
        return [{
            "type": "text",
            "text": json.dumps({
                "speed": 150,
                "rpm": 7500,
                "gear": 4,
                "status": "This is hardcoded example data"
            }, indent=2)
        }]

    # ========================================================================
    # MCP Server Setup
    # ========================================================================

    async def run(self):
        """Main entry point - run MCP server over stdio"""
        server = Server("sim-racing-telemetry")

        @server.list_tools()
        async def list_tools():
            tools = [t.mcp_tool for t in self.registry._tools.values()]
            self.logger.debug("Listing registered tools: %s", [t.name for t in tools])
            return tools

        @server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]):
            try:
                return await self.registry.call_tool(name, arguments, self)
            except Exception as e:
                return [{
                    "type": "text",
                    "text": f"Error: {str(e)}"
                }]

        # Run MCP server
        async with stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                server.create_initialization_options()
            )


# ============================================================================
# Entry Point
# ============================================================================

async def main():
    logger = get_logger("mcp_bridge", debug_mode=True, jsonl=False, file_path="mcp.log")
    bridge = MCPBridge(logger)
    await bridge.run()

# Run using: mcp-inspector poetry run python server.py
if __name__ == "__main__":
    asyncio.run(main())
