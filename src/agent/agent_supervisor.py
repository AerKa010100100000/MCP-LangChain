# python3.11.4
# _*_ coding: utf-8 _*_
#
# 版权所有 (C) ${2024} - 2025 AerKa 保留所有权利  
#
# @Time    : 2025/4/9 20:10
# @Author  : AerKa
# @File    : agent_supervisor.py
# @IDE     : PyCharm
from typing import Literal

from langchain_core.output_parsers import JsonOutputParser
from langgraph.types import Command
from langchain_core.messages import SystemMessage
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnableConfig

from src.workflows.state import State
from src.workflows.options import OPTIONS, Information
from src.workflows.entity import Router
from src.agent.prompts import SUPERVISOR_AGENT_PROMPT_TEMPLATE

model = ChatOpenAI(
    model="qwen2.5-14b-instruct",
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
    api_key="sk-65e4d0e55eb44fab8c5a05670d3d9add",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)

parser = JsonOutputParser(pydantic_object=Router)


# 主管
async def supervisor_node(state: State, config: RunnableConfig) -> Command[Literal[*OPTIONS]]:
    # 获取文件上传标识
    upload_file_id = config.get('configurable', {}).get('file_id')
    is_upload_file = 'yes' if upload_file_id else 'no'
    # 构建系统提示词
    system_prompt_template = PromptTemplate(
        input_variables=["members", "Information", "is_upload_file"],
        template=SUPERVISOR_AGENT_PROMPT_TEMPLATE,
        partial_variables={"format_instructions": parser.get_format_instructions()}
    )
    system_prompt = system_prompt_template.invoke({
        "members": str(OPTIONS),
        "Information": Information,
        "is_upload_file": is_upload_file,
    }).to_string()
    messages = [
        SystemMessage(content=system_prompt),
    ] + state["messages"]
    response = await model.with_structured_output(Router).ainvoke(messages)
    goto = response.next
    return Command(goto=goto, update={"next": goto})