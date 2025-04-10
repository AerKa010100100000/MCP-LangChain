# python3.11.4
# _*_ coding: utf-8 _*_
#
# 版权所有 (C) ${2024} - 2025 AerKa 保留所有权利  
#
# @Time    : 2025/4/9 20:09
# @Author  : AerKa
# @File    : agent_qa.py
# @IDE     : PyCharm
from typing import Literal

from langchain_core.messages import AIMessage
from langgraph.types import Command

from src.workflows.state import State
from src.agent.models import chat_model


async def qa_specialist(state: State) -> Command[Literal["__end__"]]:
    results = await chat_model.ainvoke(state["messages"])
    return Command(
        update={
            "messages": [
                AIMessage(content=results.content, name="qa_specialist")
            ]
        },
        goto="__end__",
    )
