# python3.11.4
# _*_ coding: utf-8 _*_
#
# 版权所有 (C) ${2024} - 2025 AerKa 保留所有权利  
#
# @Time    : 2025/4/10 14:37
# @Author  : AerKa
# @File    : models.py
# @IDE     : PyCharm
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()  # 加载 .env 文件中的变量

chat_model = ChatOpenAI(
    model=os.getenv("MODEL"),
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
    api_key=os.getenv("API_KEY"),
    base_url=os.getenv("BASE_URL"),
)

