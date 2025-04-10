# python3.11.4
# _*_ coding: utf-8 _*_
#
# 版权所有 (C) ${2024} - 2025 AerKa 保留所有权利  
#
# @Time    : 2025/4/9 20:36
# @Author  : AerKa
# @File    : tools.py
# @IDE     : PyCharm
import copy
from typing import Any, Union, Optional

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import BaseTool, StructuredTool, ToolException
from mcp import ClientSession
from mcp.types import (
    CallToolResult,
    EmbeddedResource,
    ImageContent,
    TextContent,
)
from mcp.types import (
    Tool as MCPTool,
)

NonTextContent = Union[ImageContent, EmbeddedResource]


def _convert_call_tool_result(
        call_tool_result: CallToolResult,
) -> tuple[Union[str, list[str]], Optional[list[NonTextContent]]]:
    text_contents: list[TextContent] = []
    non_text_contents = []
    for content in call_tool_result.content:
        if isinstance(content, TextContent):
            text_contents.append(content)
        else:
            non_text_contents.append(content)

    tool_content: Union[str, list[str]] = [content.text for content in text_contents]
    if len(text_contents) == 1:
        tool_content = tool_content[0]

    if call_tool_result.isError:
        raise ToolException(tool_content)

    return tool_content, non_text_contents or None


def convert_mcp_tool_to_langchain_tool(
        session: ClientSession,
        tool: MCPTool,
) -> BaseTool:
    """将 MCP 工具转换为 LangChain 工具。

    NOTE: 此工具只能在活动 MCP 客户端会话的上下文中执行。

    Args:
        session: MCP 客户端会话
        tool: MCP 工具进行转换

    Returns:
        LangChain 工具
    """

    async def call_tool(
            config: RunnableConfig,
            **arguments: dict[str, Any],
    ) -> tuple[Union[str, list[str]], Optional[list[NonTextContent]]]:
        schema_fields = tool.inputSchema.get('properties', {}).keys()
        filtered_config = {
            key: copy.deepcopy(config["configurable"].get(key))
            for key in schema_fields
            if key in config["configurable"]
        }
        arguments = {
            **arguments,
            **filtered_config
        }
        call_tool_result = await session.call_tool(tool.name, arguments)
        return _convert_call_tool_result(call_tool_result)

    return StructuredTool(
        name=tool.name,
        description=tool.description or "",
        args_schema=tool.inputSchema,
        coroutine=call_tool,
        response_format="content_and_artifact",
    )


async def load_mcp_tools(session: ClientSession) -> list[BaseTool]:
    """加载所有可用的 MCP 工具并将它们转换为 LangChain 工具。"""
    tools = await session.list_tools()
    return [convert_mcp_tool_to_langchain_tool(session, tool) for tool in tools.tools]
