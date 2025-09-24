import os
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_redis import RedisConfig, RedisVectorStore
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.tools import StructuredTool
from app.models.schemas import ToolOutput
from langchain_community.vectorstores.redis.base import check_index_exists
from app.services.redis_helpers import redis_client

load_dotenv()
DIRECTORY_PATH = "app/resources/files"

#Vector store configurations
INDEX_NAME = "rights2roof"
embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
config = RedisConfig(
    index_name=INDEX_NAME,
    redis_client=redis_client,
    embedding=embeddings
)

#Create vector store and the retreiver
vector_store = RedisVectorStore(embeddings, config=config)
retriever = vector_store.as_retriever(search_type="similarity", search_kwargs={"k": 5})

#Function to populate the vector store from PDF files
def create_vector_store():
    if(not check_index_exists(redis_client, INDEX_NAME)):
        for filename in os.listdir(DIRECTORY_PATH):
            if filename.endswith(".pdf"):
                file_path = os.path.join(DIRECTORY_PATH, filename)
                loader = PyPDFLoader(file_path)
                pages = loader.load_and_split()
                vector_store.add_documents(documents=pages)
    else:
        print("Vector store already exists. Skipping creation.")

#Get context from vector store based on the query
def get_context(query: str) -> ToolOutput:
    context = retriever.invoke(query)
    return ToolOutput(
        tool="vector_store_tool",
        input=query,
        output=context,
        step="Provide relevant context from vector store based on user's query"
    )

# Define the tool for use in agents
vector_store_tool = StructuredTool.from_function(
    func=get_context,
    name="vector_store_tool",
    description="Returns the relevant context from the vector store based on the user's query. Useful for retrieving information about rental housing laws and regulations."
)

if __name__ == "__main__":
    create_vector_store()