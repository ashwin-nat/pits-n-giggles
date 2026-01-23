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

import asyncio
import json
from typing import Dict, Any, List, Callable, Awaitable, Optional
from dataclasses import dataclass

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool

from lib.logger import get_logger

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

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

    def tool(
        self,
        *,
        name: str,
        description: str,
        input_schema: dict | None = None,
    ):
        def decorator(func):
            self.register(
                name=name,
                description=description,
                handler=func,
                input_schema=input_schema,
            )
            return func

        return decorator

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
            t.mcp_tool
            for t in self._tools.values()
        ]

    async def call_tool(
        self,
        name: str,
        arguments: Dict[str, Any],
        context: Any,
    ) -> Dict[str, Any]:
        """Execute a tool by name with defensive error handling"""

        if name not in self._tools:
            return {
                "error": {
                    "type": "unknown_tool",
                    "message": f"Unknown tool: {name}",
                }
            }

        tool = self._tools[name]

        try:
            return await tool.handler(context, arguments)

        except KeyError as e:
            return {
                "error": {
                    "type": "invalid_arguments",
                    "message": f"Missing required argument: {e.args[0]}",
                    "required": tool.input_schema.get("required", []),
                    "received": list(arguments.keys()),
                }
            }

        except Exception as e:  # pylint: disable=broad-except
            return {
                "error": {
                    "type": "tool_execution_error",
                    "message": str(e),
                }
            }
