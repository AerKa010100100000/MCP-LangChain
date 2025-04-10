# python3.11.4
# _*_ coding: utf-8 _*_
#
# 版权所有 (C) ${2024} - 2025 AerKa 保留所有权利  
#
# @Time    : 2025/4/9 20:10
# @Author  : AerKa
# @File    : chainlitUI.py
# @IDE     : PyCharm
from uuid import uuid4

from aiofiles import os
from langchain_core.messages import HumanMessage, AIMessageChunk, AIMessage
from langchain_core.runnables import RunnableConfig

import chainlit as cl

from src.workflows.graph import get_graph


@cl.on_chat_start
async def on_chat_start():
    session_id = str(uuid4())
    workflows = await get_graph(session_id=session_id)
    file_cache = []
    cl.user_session.set("file_cache", file_cache)
    cl.user_session.set("session_id", session_id)
    cl.user_session.set("workflows", workflows)


@cl.on_message
async def on_message(msg: cl.Message):

    if msg.elements:
        file_cache = cl.user_session.get("file_cache")
        file_cache.append(msg.elements[0].path)
        cl.user_session.set("file_cache", file_cache)

    answer = cl.Message(content="")
    workflow = cl.user_session.get('workflows')
    config: RunnableConfig = {
        "configurable": {
            "session_id": cl.user_session.get("session_id"),
            "thread_id": cl.context.session.thread_id,
            "file_id": msg.elements[0].id if msg.elements else None,
            "file_path": msg.elements[0].path if msg.elements else None
        }
    }

    # 动态生成系统提示词
    async for message, metadata in workflow.astream(
            {
                "messages": [
                    HumanMessage(content=msg.content)
                ]
            },
            stream_mode="messages",
            config=RunnableConfig(**config)
    ):
        if (
                message.content
                and isinstance(message, AIMessage)
                and metadata["langgraph_node"] != "supervisor"
        ):
            await answer.stream_token(message.content)

    await answer.send()


@cl.on_chat_end
async def on_chat_end():
    file_cache = cl.user_session.get("file_cache")
    if file_cache:
        for path in file_cache:
            try:
                # 使用 aiofiles 的异步 isfile
                if await os.path.isfile(path):  # 这里使用 await 调用 aiofiles 的异步 isfile
                    await os.remove(path)  # 这里使用 await 调用 aiofiles 的异步 remove
            except Exception as e:
                print(f"Failed to delete {path}: {e}")