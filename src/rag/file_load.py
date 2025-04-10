# python3.11.4
# _*_ coding: utf-8 _*_
#
# 版权所有 (C) ${2024} - 2025 AerKa 保留所有权利  
#
# @Time    : 2025/4/10 15:25
# @Author  : AerKa
# @File    : file_load.py
# @IDE     : PyCharm
import json
import os

from langchain_core.documents import Document
from langchain_community.document_loaders import (
    CSVLoader, JSONLoader, TextLoader, PyMuPDFLoader,
    SQLDatabaseLoader, UnstructuredMarkdownLoader,
)


# 加载数据源
def load(file_path: str, async_load: bool = False) -> list[Document]:
    file_type = os.path.splitext(file_path)[1].lstrip('.')
    # 加载器映射
    loader_map = {
        "pdf": PyMuPDFLoader,
        "csv": CSVLoader,
        "md": UnstructuredMarkdownLoader,
        "json": JSONLoader,
        "txt": TextLoader,
    }
    # 动态构建加载器
    if file_type in loader_map:
        # 读取加载器所需要的参数
        with open('params.json', 'r', encoding='utf-8') as f:
            params = json.load(f)
        # 动态读取参数
        param = params.get(file_type)
        # 更新文件路径
        param["file_path"] = file_path
        # 构建加载器
        loader = loader_map[file_type](**param)
    else:
        raise ValueError(f"不支持的文件类型： {file_type}")
    # 返回Document列表
    return loader.aload() if async_load else loader.load()
