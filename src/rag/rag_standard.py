# python3.11.4
# _*_ coding: utf-8 _*_
#
# 版权所有 (C) ${2024} - 2025 AerKa 保留所有权利  
#
# @Time    : 2025/4/10 15:15
# @Author  : AerKa
# @File    : rag_standard.py
# @IDE     : PyCharm

import faiss
from uuid import uuid4

from typing import Optional
from langchain_community.docstore.in_memory import InMemoryDocstore
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_core.vectorstores import VectorStoreRetriever
from langchain_core.output_parsers import JsonOutputParser
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface.embeddings import HuggingFaceEmbeddings

from src.rag.entity import Summary
from src.rag.file_load import load

parser = JsonOutputParser(pydantic_object=Summary)

embeddings = HuggingFaceEmbeddings(model_name="thenlper/gte-large-zh")
index = faiss.IndexFlatL2(len(embeddings.embed_query("hello world")))
vector_store = FAISS(
    embedding_function=embeddings,
    index=index,
    docstore=InMemoryDocstore(),
    index_to_docstore_id={},
)


class StandardRAG:
    def __init__(self):
        self.retriever: Optional[VectorStoreRetriever] = None
        self.current_file_id: Optional[str] = None  # 当前加载的文件ID
        self.loaded: bool = False

    def load_file(self, file_path: str, file_id: str):
        docs = load(file_path=file_path)
        # 文档切割
        documents = RecursiveCharacterTextSplitter(
            chunk_size=1024,
            chunk_overlap=200,
            length_function=len,
            is_separator_regex=False,
        ).split_documents(documents=docs)

        uuids = [str(uuid4()) for _ in range(len(documents))]

        vector_store.add_documents(documents=documents, ids=uuids)
        self.retriever = vector_store.as_retriever(search_type="mmr", search_kwargs={"k": 3})
        self.current_file_id = file_id
        self.loaded = True

    def query(self, question: str) -> str:
        if not self.retriever:
            return "尚未上传文档，无法进行文档问答。"
        # 从 retriever 检索相关内容
        relevant_docs = self.retriever.invoke(question)
        context = "\n\n".join([doc.page_content for doc in relevant_docs])
        return f"根据文档内容回答：\n{context}"