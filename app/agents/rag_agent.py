import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers.string import StrOutputParser
from langsmith import traceable
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
import redis
from app.tools import vector_store_tool

# load_dotenv()
# DIRECTORY_PATH = "app/resources/files"

# # r = redis.Redis(host='localhost', port=32770, decode_responses=True)
# # r.set("foo", "bar")
# # print(r.get("foo"))

# pdf_data = {}
# for filename in os.listdir(DIRECTORY_PATH):
#     if filename.endswith(".pdf"):
#         file_path = os.path.join(DIRECTORY_PATH, filename)
#         loader = PyPDFLoader(file_path)
#         pages = loader.load_and_split()
#         pdf_data[filename] = pages

# embeddings = OpenAIEmbeddings(model="text-embedding-3-large")

# text_splitter = RecursiveCharacterTextSplitter(
#     chunk_size=500,
#     chunk_overlap=100
#     ) # Implement the text splitter using RecursiveCharacterTextSplitter

# chunks = {
#     title: text_splitter.transform_documents(docs)
#     for title, docs in pdf_data.items()
# }

# vector_store = Chroma(
#     collection_name="rights2roof",
#     embedding_function=embeddings,
#     persist_directory="app/resources/vector-store"
#     )

# for title, chunk in chunks.items():
#     try:
#         vector_store.add_documents(documents=chunk)
#         print(f"added {title} to vector store")
#     except Exception as e:
#         print(f"Error adding {title}: {e}")
# print("vector store created")


llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

# You can use this as a base prompt and modify it if you feel you need to
system_prompt = """
You are a helpful RAG agent that answers questions about the the laws and regulation regarding the rental housing market in California and New York.
Your answers should be detailed and include specific references to the relevant laws and regulations.
Please ONLY use the context provided to you. Do not use any other context.
"""
print(system_prompt)
prompt_template = ChatPromptTemplate.from_messages([
    SystemMessage(content=system_prompt),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{query} {context}")
])

rag_chain = prompt_template | llm | StrOutputParser()

query = "Can a landlord in NYC evict a tenant for not paying rent during a pandemic?"
print(query)

# retriever = vector_store.as_retriever(search_kwargs={"k": 5})
# context = retriever.invoke(query)

context = vector_store_tool.retriever_tool.func(query)
response = rag_chain.invoke({"question": query, "context": context, "chat_history": []})
print(response.content)
