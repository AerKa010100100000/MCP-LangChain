# python3.11.4
# _*_ coding: utf-8 _*_
#
# 版权所有 (C) ${2024} - 2025 AerKa 保留所有权利  
#
# @Time    : 2025/4/9 20:16
# @Author  : AerKa
# @File    : graph.py
# @IDE     : PyCharm
from langgraph.constants import START
from langgraph.graph import StateGraph, MessagesState
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph.graph import CompiledGraph
from langgraph.graph.state import CompiledStateGraph

from src.agent.agent_dp import dp_specialist
from src.agent.agent_qa import qa_specialist
from src.agent.agent_supervisor import supervisor_node

# 全局会话缓存池
_graph_cache: dict[str, CompiledGraph] = {}


# 构建图
async def build_graph(memory: MemorySaver) -> CompiledStateGraph:
    builder = StateGraph(MessagesState)
    builder.add_node("supervisor", supervisor_node)
    builder.add_node("dp_specialist", dp_specialist)
    builder.add_node("qa_specialist", qa_specialist)
    builder.add_edge(START, "supervisor")
    graph = builder.compile(checkpointer=memory)
    return graph


# 通过会话ID获取图
async def get_graph(session_id: str) -> CompiledGraph:
    """获取或创建属于会话的工作流图"""
    if session_id not in _graph_cache:
        memory = MemorySaver()
        _graph_cache[session_id] = await build_graph(memory)
    return _graph_cache[session_id]
