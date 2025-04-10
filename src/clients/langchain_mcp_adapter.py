# python3.11.4
# _*_ coding: utf-8 _*_
#
# 版权所有 (C) ${2024} - 2025 AerKa 保留所有权利  
#
# @Time    : 2025/4/9 20:11
# @Author  : AerKa
# @File    : langchain_mcp_adapter.py
# @IDE     : PyCharm
import os
from contextlib import AsyncExitStack
from pathlib import Path
from types import TracebackType
from typing import Any, Literal, Optional, TypedDict, cast, Union

from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.tools import BaseTool
from mcp import ClientSession, StdioServerParameters
from mcp.client.sse import sse_client
from mcp.client.stdio import stdio_client

from langchain_mcp_adapters.prompts import load_mcp_prompt

from src.clients.tools import load_mcp_tools

EncodingErrorHandler = Literal["strict", "ignore", "replace"]

DEFAULT_ENCODING = "utf-8"
DEFAULT_ENCODING_ERROR_HANDLER: EncodingErrorHandler = "strict"

DEFAULT_HTTP_TIMEOUT = 5
DEFAULT_SSE_READ_TIMEOUT = 60 * 5


class StdioConnection(TypedDict):
    transport: Literal["stdio"]

    command: str
    """要运行以启动服务器的可执行文件。"""

    args: list[str]
    """要传递给可执行文件的命令行参数。"""

    env: Optional[dict[str, str]]
    """生成进程时使用的环境。"""

    cwd: Union[str, Path, None]
    """生成进程时使用的工作目录。"""

    encoding: str
    """向服务器发送/接收消息时使用的文本编码。"""

    encoding_error_handler: EncodingErrorHandler
    """
    文本编码错误处理程序。

    请参阅 https://docs.python.org/3/library/codecs.html#codec-base-classes
    可能值的解释
    """

    session_kwargs: Optional[dict[str, Any]]
    """要传递给 ClientSession 的其他关键字参数"""


class SSEConnection(TypedDict):
    transport: Literal["sse"]

    url: str
    """要连接到的 SSE 终端节点的 URL。"""

    headers: Optional[dict[str, Any]]
    """要发送到 SSE 终端节点的 HTTP 标头"""

    timeout: float
    """HTTP 超时"""

    sse_read_timeout: float
    """SSE 读取超时"""

    session_kwargs: Optional[dict[str, Any]]
    """要传递给 ClientSession 的其他关键字参数"""


class MultiServerMCPClient:
    """Client 端，用于连接多个 MCP 服务器并从中加载兼容 LangChain 的工具。"""

    def __init__(
        self, connections: Optional[dict[str, Union[StdioConnection, SSEConnection]]] = None
    ) -> None:
        """使用 MCP 服务器连接初始化 MultiServerMCPClient。

        Args:
            connections: 将服务器名称映射到连接配置的字典。
                每个配置可以是 StdioConnection 或 SSEConnection。
                如果为 None，则不建立初始连接。
        """
        self.connections: dict[str, Union[StdioConnection, SSEConnection]] = connections or {}
        self.exit_stack = AsyncExitStack()
        self.sessions: dict[str, ClientSession] = {}
        self.server_name_to_tools: dict[str, list[BaseTool]] = {}

    async def _initialize_session_and_load_tools(
        self, server_name: str, session: ClientSession
    ) -> None:
        """初始化会话并从中加载工具。

        Args:
            server_name: 用于标识此服务器连接的名称
            session: 要初始化的 ClientSession
        """
        # 初始化会话
        await session.initialize()
        self.sessions[server_name] = session

        # 从此服务器加载工具
        server_tools = await load_mcp_tools(session)
        self.server_name_to_tools[server_name] = server_tools

    async def connect_to_server(
        self,
        server_name: str,
        *,
        transport: Literal["stdio", "sse"] = "stdio",
        **kwargs,
    ) -> None:
        """使用 stdio 或 SSE 连接到 MCP 服务器。

        这是一个泛型方法，调用 connect_to_server_via_stdio 或 connect_to_server_via_sse
        基于提供的 transport 参数。

        Args:
            server_name:用于标识此服务器连接的名称
            transport: 要使用的传输类型（“stdio” 或 “sse”），默认为 “stdio”
            **kwargs: 要传递给特定连接方法的其他参数

        Raises:
            ValueError: 如果无法识别传输
            ValueError: 如果缺少指定传输的必需参数
        """
        if transport == "sse":
            if "url" not in kwargs:
                raise ValueError("SSE 连接需要 'url' 参数")
            await self.connect_to_server_via_sse(
                server_name,
                url=kwargs["url"],
                headers=kwargs.get("headers"),
                timeout=kwargs.get("timeout", DEFAULT_HTTP_TIMEOUT),
                sse_read_timeout=kwargs.get("sse_read_timeout", DEFAULT_SSE_READ_TIMEOUT),
                session_kwargs=kwargs.get("session_kwargs"),
            )
        elif transport == "stdio":
            if "command" not in kwargs:
                raise ValueError("stdio 连接需要 'command' 参数")
            if "args" not in kwargs:
                raise ValueError("stdio 连接需要 'args' 参数")
            await self.connect_to_server_via_stdio(
                server_name,
                command=kwargs["command"],
                args=kwargs["args"],
                env=kwargs.get("env"),
                encoding=kwargs.get("encoding", DEFAULT_ENCODING),
                encoding_error_handler=kwargs.get(
                    "encoding_error_handler", DEFAULT_ENCODING_ERROR_HANDLER
                ),
                session_kwargs=kwargs.get("session_kwargs"),
            )
        else:
            raise ValueError(f"不支持的传输方式：{transport}。必须是 'stdio' 或 'sse'")

    async def connect_to_server_via_stdio(
        self,
        server_name: str,
        *,
        command: str,
        args: list[str],
        env: Optional[dict[str, str]] = None,
        encoding: str = DEFAULT_ENCODING,
        encoding_error_handler: Literal[
            "strict", "ignore", "replace"
        ] = DEFAULT_ENCODING_ERROR_HANDLER,
        session_kwargs: Optional[dict[str, Any]] = None,
    ) -> None:
        """使用 stdio 连接到特定的 MCP 服务器

        Args:
            server_name: 用于标识此服务器连接的名称
            command: 要执行的命令
            args: 命令的参数
            env: 命令的环境变量
            encoding: 字符编码
            encoding_error_handler: 如何处理编码错误
            session_kwargs: 要传递给 ClientSession 的其他关键字参数
        """
        env = env or {}
        if "PATH" not in env:
            env["PATH"] = os.environ.get("PATH", "")

        server_params = StdioServerParameters(
            command=command,
            args=args,
            env=env,
            encoding=encoding,
            encoding_error_handler=encoding_error_handler,
        )

        # 创建并存储连接
        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
        read, write = stdio_transport
        session_kwargs = session_kwargs or {}
        session = cast(
            ClientSession,
            await self.exit_stack.enter_async_context(ClientSession(read, write, **session_kwargs)),
        )

        await self._initialize_session_and_load_tools(server_name, session)

    async def connect_to_server_via_sse(
        self,
        server_name: str,
        *,
        url: str,
        headers: Optional[dict[str, Any]] = None,
        timeout: float = DEFAULT_HTTP_TIMEOUT,
        sse_read_timeout: float = DEFAULT_SSE_READ_TIMEOUT,
        session_kwargs: Optional[dict[str, Any]] = None,
    ) -> None:
        """使用 SSE 连接到特定的 MCP 服务器

        Args:
            server_name: 用于标识此服务器连接的名称
            url: SSE 服务器的 URL
            headers: 要发送到 SSE 终端节点的 HTTP 标头
            timeout: HTTP 超时
            sse_read_timeout: SSE 读取超时
            session_kwargs: 要传递给 ClientSession 的其他关键字参数
        """
        # 创建并存储连接
        sse_transport = await self.exit_stack.enter_async_context(
            sse_client(url, headers, timeout, sse_read_timeout)
        )
        read, write = sse_transport
        session_kwargs = session_kwargs or {}
        session = cast(
            ClientSession,
            await self.exit_stack.enter_async_context(ClientSession(read, write, **session_kwargs)),
        )

        await self._initialize_session_and_load_tools(server_name, session)

    def get_tools(self) -> list[BaseTool]:
        """从所有连接的服务器获取所有工具的列表。"""
        all_tools: list[BaseTool] = []
        for server_tools in self.server_name_to_tools.values():
            all_tools.extend(server_tools)
        return all_tools

    async def get_prompt(
        self, server_name: str, prompt_name: str, arguments: Optional[dict[str, Any]]
    ) -> list[Union[HumanMessage, AIMessage]]:
        """从给定的 MCP 服务器获取提示。"""
        session = self.sessions[server_name]
        return await load_mcp_prompt(session, prompt_name, arguments)

    async def __aenter__(self) -> "MultiServerMCPClient":
        try:
            connections = self.connections or {}
            for server_name, connection in connections.items():
                await self.connect_to_server(server_name, **connection)

            return self
        except Exception:
            await self.exit_stack.aclose()
            raise

    async def __aexit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        await self.exit_stack.aclose()
