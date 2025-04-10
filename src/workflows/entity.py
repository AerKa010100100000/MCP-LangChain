# python3.11.4
# _*_ coding: utf-8 _*_
#
# 版权所有 (C) ${2024} - 2025 AerKa 保留所有权利  
#
# @Time    : 2025/4/9 20:14
# @Author  : AerKa
# @File    : entity.py
# @IDE     : PyCharm
from typing import Literal
from pydantic import BaseModel, Field


from .options import OPTIONS


class Router(BaseModel):
    next: Literal[*OPTIONS] = Field(description="指定成员名称")