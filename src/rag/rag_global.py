# python3.11.4
# _*_ coding: utf-8 _*_
#
# 版权所有 (C) ${2024} - 2025 AerKa 保留所有权利  
#
# @Time    : 2025/4/9 20:13
# @Author  : AerKa
# @File    : rag_global.py
# @IDE     : PyCharm
from typing import Dict
from src.rag.rag_summary import SummaryRAG

# 文件缓存池
session_rag_cache: Dict[str, Dict[str, SummaryRAG]] = {}


# 采用二级缓存结构
def get_rag_for_user_file(session_id: str, file_id: str) -> SummaryRAG:
    # 会话缓存
    if session_id not in session_rag_cache:
        session_rag_cache[session_id] = {}

    # 文件缓存
    if file_id not in session_rag_cache[session_id]:
        session_rag_cache[session_id][file_id] = SummaryRAG()

    return session_rag_cache[session_id][file_id]