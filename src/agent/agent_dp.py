# python3.11.4
# _*_ coding: utf-8 _*_
#
# 版权所有 (C) ${2024} - 2025 AerKa 保留所有权利  
#
# @Time    : 2025/4/9 20:09
# @Author  : AerKa
# @File    : agent_dp.py
# @IDE     : PyCharm
import json
from contextlib import asynccontextmanager
from pathlib import Path

from langchain_core.messages import AIMessage
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph.graph import CompiledGraph
from langgraph.prebuilt import create_react_agent
from langgraph.types import Command

from src.agent.prompts import DP_SYSTEM_PROMPT_TEMPLATE
from src.clients.langchain_mcp_adapter import MultiServerMCPClient
from src.workflows.state import State
from src.agent.models import chat_model

checkpointer = MemorySaver()
mcp = json.loads(Path('mcp_server.json').read_text(encoding='utf-8'))


@asynccontextmanager
async def tool_graph(config: RunnableConfig) -> CompiledGraph:
    async with MultiServerMCPClient(mcp) as client:
        # 获取文件上传标识
        upload_file_id = config.get('configurable', {}).get('file_id')
        is_upload_file = 'yes' if upload_file_id else 'no'
        # 构建系统提示词
        system_prompt_template = PromptTemplate(
            input_variables=["is_upload_file"],
            template=DP_SYSTEM_PROMPT_TEMPLATE,
        )
        system_prompt = system_prompt_template.invoke({
            "is_upload_file": is_upload_file,
        }).to_string()
        agent = create_react_agent(
            model=chat_model,
            tools=client.get_tools(),
            prompt=system_prompt,
            checkpointer=checkpointer,
            debug=True
        )
        yield agent


async def dp_specialist(state: State, config: RunnableConfig):
    async with tool_graph(config=config) as agent:
        response = await agent.ainvoke(input=state, config=config)

    yield Command(
        update={
            "messages": [
                AIMessage(content=response["messages"][-1].content, name="dp_specialist")
            ]
        },
        goto="__end__",
    )


