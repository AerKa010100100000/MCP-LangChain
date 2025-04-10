# python3.11.4
# _*_ coding: utf-8 _*_
#
# 版权所有 (C) ${2024} - 2025 AerKa 保留所有权利  
#
# @Time    : 2025/4/9 20:15
# @Author  : AerKa
# @File    : state.py
# @IDE     : PyCharm
from typing import Dict

from langgraph.prebuilt.chat_agent_executor import AgentState


class State(AgentState):
    """路由状态"""
    next: str


class ToolState(State):
    """工具参数状态"""
    config: Dict