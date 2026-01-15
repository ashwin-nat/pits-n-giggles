# MIT License
#
# Copyright (c) [2024] [Ashwin Natarajan]
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# -------------------------------------- IMPORTS -----------------------------------------------------------------------

import logging
import json
from typing import Dict, Any, List, Callable, Awaitable, Optional
from dataclasses import dataclass

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool

from .tools_infra import ToolRegistry
from meta.meta import APP_NAME

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

class MCPBridge:
    """MCP Bridge for sim racing telemetry"""

    def __init__(self, logger: logging.Logger, version: str) -> None:
        self.registry: ToolRegistry = ToolRegistry()
        self.logger: logging.Logger = logger
        self.version: str = version
        self._register_tools()
        self._init_infra()
        self.logger.debug("MCPBridge initialized with tools: %s", list(self.registry._tools.keys()))

    def _register_tools(self):
        """Register all tools"""
        @self.registry.tool(
            name="get_example_data",
            description="Example tool that returns hardcoded data",
        )
        async def handle_get_example_data(
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

    def _init_infra(self, server: Server) -> None:
        """Initialize infrastructure components if any"""
        @server.list_tools()
        async def list_tools():
            tools = self.registry.get_tool_list()
            self.logger.debug("Listing registered tools: %s", tools)
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

    # ========================================================================
    # MCP Server Setup
    # ========================================================================

    async def run(self):
        """Main entry point - run MCP server over stdio"""
        server = Server(
            name=f"{APP_NAME} MCP Server",
            version=self.version)
        self._init_infra(server)
        self.logger.debug("MCP Server initialized.")

        # Run MCP server
        async with stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                server.create_initialization_options()
            )
