# python3.11.4
# _*_ coding: utf-8 _*_
#
# 版权所有 (C) ${2024} - 2025 AerKa 保留所有权利  
#
# @Time    : 2025/4/9 20:13
# @Author  : AerKa
# @File    : server_rag.py
# @IDE     : PyCharm
import sys
import os

from mcp import types
from mcp.types import CallToolResult

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from mcp.server.fastmcp import FastMCP
from src.rag.rag_global import get_rag_for_user_file

mcp = FastMCP("SQLServer")
USER_AGENT = "SQLServer/1.0"


@mcp.tool()
async def rag_retriever(query: str, session_id: str, file_id: str, file_path: str) -> CallToolResult:
    """
    功能1：对用户上传的文件进行处理并检索出与用户问题最相关的内容；
    功能2：支持检索用户之前上传过的文件内容；

    :param query: 用户输入的问题；
    :param session_id: 用户ID（系统配置），不得生成关于该参数的任何内容；
    :param file_id: 文件ID（系统配置），不得生成关于该参数的任何内容；
    :param file_path: 文件路径（系统配置），不得生成关于该参数的任何内容；
    :return: 检索出的内容；
    """

    try:
        rag = get_rag_for_user_file(session_id, file_id)
        if not rag.loaded or rag.current_file_id != file_id:
            rag.load_file(file_path, file_id)
        result = rag.query(query)

        return types.CallToolResult(
            content=[
                types.TextContent(
                    type="text",
                    text=result
                )
            ]
        )
    except Exception as error:
        return types.CallToolResult(
            isError=True,
            content=[
                types.TextContent(
                    type="text",
                    text=f"Error: error: {error}"
                )
            ]
        )


if __name__ == "__main__":
    mcp.run(transport='stdio')
