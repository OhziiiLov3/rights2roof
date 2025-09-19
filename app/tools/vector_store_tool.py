import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_core.tools import StructuredTool
# from app.models.schemas import ToolOutput

from langchain_chroma import Chroma

def create_vector_store():
    chunks = create_text_chunks()
    # Initialize embeddings from OpenAI
    embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
    
    vector_store = Chroma(
    collection_name="rights2roof",
    embedding_function=embeddings,
    persist_directory="/resources/vectore-store"
    )
    for title, chunk_sequence in chunks.items():
        vector_store.add_documents(documents=chunk_sequence)
    
    return vector_store
    # return ToolOutput(
    #     tool="vector_store",
    #     input="",
    #     output=vector_store,
    #     step="Access the vectore_store of your knowledge base."
    # )

def create_text_chunks():
    pdf_data = load_pdfs_from_directory("app/resources/files")
    text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=100
    ) # Implement the text splitter using RecursiveCharacterTextSplitter

    #Create chunks for each document.
    chunks = {
        title: text_splitter.transform_documents(docs)
        for title, docs in pdf_data.items()
    }
    return chunks

def load_pdfs_from_directory(directory_path):
    """
    Loads all PDF files from a directory and returns a dictionary
    where keys are document titles and values are lists of pages.
    """
    pdf_documents = {}
    for filename in os.listdir(directory_path):
        if filename.endswith(".pdf"):
            file_path = os.path.join(directory_path, filename)
            try:
                loader = PyPDFLoader(file_path)
                pages = loader.load_and_split()
                pdf_documents[filename] = pages
            except Exception as e:
                print(f"Error loading {filename}: {e}")
    return pdf_documents


vector_store_tool = StructuredTool.from_function(
    func=create_vector_store,
    name="vector_store",
    description="Get the vector_store for your knowledge base.",
)







