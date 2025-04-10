# python3.11.4
# _*_ coding: utf-8 _*_
#
# 版权所有 (C) ${2024} - 2025 AerKa 保留所有权利  
#
# @Time    : 2025/4/9 20:12
# @Author  : AerKa
# @File    : entity.py
# @IDE     : PyCharm
from pydantic import BaseModel, Field


class Summary(BaseModel):
    summary: str = Field(description="生成的摘要内容，如果没有有效摘要，则为空字符串。")
    memory: str = Field(description="摘要总结的内容，如果摘要为空，则为空字符串。")
