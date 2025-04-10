# python3.11.4
# _*_ coding: utf-8 _*_
#
# 版权所有 (C) ${2024} - 2025 AerKa 保留所有权利  
#
# @Time    : 2025/4/9 20:13
# @Author  : AerKa
# @File    : rag_summary.py
# @IDE     : PyCharm
import faiss
from uuid import uuid4

from typing import Optional
from langchain_community.docstore.in_memory import InMemoryDocstore
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStoreRetriever
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface.embeddings import HuggingFaceEmbeddings

from src.rag.file_load import load
from src.rag.prompts import SYSTEM_PROMPT_TEMPLATE, USER_PROMPT_TEMPLATE
from src.rag.entity import Summary

model = ChatOpenAI(
    model="qwen2.5-14b-instruct",
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
    api_key="sk-65e4d0e55eb44fab8c5a05670d3d9add",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)

parser = JsonOutputParser(pydantic_object=Summary)

embeddings = HuggingFaceEmbeddings(model_name="thenlper/gte-large-zh")
index = faiss.IndexFlatL2(len(embeddings.embed_query("hello world")))
vector_store = FAISS(
    embedding_function=embeddings,
    index=index,
    docstore=InMemoryDocstore(),
    index_to_docstore_id={},
)


class SummaryRAG:
    def __init__(self):
        self.retriever: Optional[VectorStoreRetriever] = None
        self.current_file_id: Optional[str] = None  # 当前加载的文件ID
        self.loaded: bool = False

    def load_file(self, file_path: str, file_id: str):
        # 加载文档
        docs = load(file_path=file_path)
        # 文档切割
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=2000,
            chunk_overlap=200,
            length_function=len,
            is_separator_regex=False,
        ).split_documents(documents=docs)
        memory = ''
        documents = []
        # 摘要处理
        for doc in text_splitter:
            # 构建提示词
            user_prompt_template = PromptTemplate(
                input_variables=["memory", "document"],
                template=USER_PROMPT_TEMPLATE,
                partial_variables={"format_instructions": parser.get_format_instructions()}
            )
            user_prompt = user_prompt_template.invoke({
                "memory": memory,
                "document": doc.page_content
            })
            messages = [
                SystemMessage(content=SYSTEM_PROMPT_TEMPLATE),
                HumanMessage(content=user_prompt.to_string())
            ]
            # 进行摘要
            chain = model | parser
            generation = chain.invoke(messages)
            memory = generation['memory']
            # 构建Document
            documents.append(
                Document(
                    page_content=generation['summary'],
                    metadata=doc.metadata
                )
            )

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