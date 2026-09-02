#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2025 Melle Koning
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
import inspect
from collections.abc import Callable
from typing import Any


def python_type_to_json_type(python_type: type) -> str:
    # Basic type mapping
    if python_type in [str]:
        return "string"
    elif python_type in [int]:
        return "integer"
    elif python_type in [float]:
        return "number"
    elif python_type in [bool]:
        return "boolean"
    elif python_type in [dict]:
        return "object"
    elif python_type in [list, list]:
        return "array"
    else:
        return "string"  # default fallback


def make_tool_schema(func: Callable, description: str | None = None) -> dict[str, Any]:
    """Build an MCP-shaped tool definition from a Python function.

    Returns the MCP tool schema:

        {
          "name": <func.__name__>,
          "description": <docstring>,
          "inputSchema": {"type": "object", "properties": {...}, "required": [...]}
        }

    The ``inputSchema`` key is omitted when the function takes no parameters
    (e.g. ``start_point``), mirroring the original behaviour so that smaller
    LLMs are not confused by an empty parameter object.
    """
    sig = inspect.signature(func)
    doc = description or func.__doc__ or ""

    properties: dict[str, dict[str, str]] = {}
    required: list[str] = []

    for name, param in sig.parameters.items():
        param_type = (
            param.annotation if param.annotation != inspect.Parameter.empty else str
        )
        json_type = python_type_to_json_type(param_type)
        properties[name] = {"type": json_type, "description": f"{name} parameter"}
        if param.default == inspect.Parameter.empty:
            required.append(name)

    schema: dict[str, Any] = {
        "name": func.__name__,
        "description": doc.strip(),
    }

    # If the function has parameters, we add them to the definition
    # as the start_point does not have any properties we deliberately
    # do not add the "inputSchema" key if there are no properties
    # - some smaller LLMs do not understand this and throw an error
    # for the start point function when they try to call it
    if properties:
        schema["inputSchema"] = {
            "type": "object",
            "properties": properties,
            "required": required,
        }

    return schema


def to_openai_tools(mcp_schemas: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Convert MCP-shaped tool schemas to the OpenAI / litellm ``tools`` format.

    Used when sending tool definitions to an OpenAI-compatible LLM endpoint.
    Functions with no ``inputSchema`` (e.g. ``start_point``) omit ``parameters``,
    reproducing the exact shape the original ``function_to_litellm_definition``
    produced.
    """
    openai_tools: list[dict[str, Any]] = []
    for s in mcp_schemas:
        func_def: dict[str, Any] = {
            "name": s["name"],
            "description": s.get("description", ""),
        }
        if "inputSchema" in s:
            func_def["parameters"] = s["inputSchema"]
        openai_tools.append(
            {
                "type": "function",
                "function": func_def,
            }
        )
    return openai_tools
