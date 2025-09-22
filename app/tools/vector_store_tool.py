import os
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_core.tools import StructuredTool
from langchain_chroma import Chroma

load_dotenv()
DIRECTORY_PATH = "app/resources/files"

embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
vector_store = Chroma(
    collection_name="rights2roof",
    embedding_function=embeddings,
    persist_directory="app/resources/vector-store"
    )

def create_vector_store():
    pdf_data = {}
    for filename in os.listdir(DIRECTORY_PATH):
        if filename.endswith(".pdf"):
            file_path = os.path.join(DIRECTORY_PATH, filename)
            loader = PyPDFLoader(file_path)
            pages = loader.load_and_split()
            pdf_data[filename] = pages


    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=100
        ) # Implement the text splitter using RecursiveCharacterTextSplitter

    chunks = {
        title: text_splitter.transform_documents(docs)
        for title, docs in pdf_data.items()
    }

    for title, chunk in chunks.items():
        try:
            vector_store.add_documents(documents=chunk)
            print(f"added {title} to vector store")
        except Exception as e:
            print(f"Error adding {title}: {e}")


def create_store():
    create_vector_store()

retriever_tool = StructuredTool(
    name="vector_store_retriever_tool",
    func=vector_store.as_retriever(search_kwargs={"k": 5}).invoke,
    description="useful for when you need to answer questions about the knowledge base",
)