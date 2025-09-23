import os
from dotenv import load_dotenv
import redis
from langchain_openai import OpenAIEmbeddings
from langchain_redis import RedisConfig, RedisVectorStore
from langchain_community.document_loaders import PyPDFLoader
# from langchain_core.tools import StructuredTool
# from app.models.schemas import ToolOutput

load_dotenv()
DIRECTORY_PATH = "app/resources/files"

#redis client and URL setup
REDIS_URL=os.getenv("REDIS_URL", "redis://localhost:32771")
redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST","localhost"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    db=0,
    decode_responses=True
)

#Vector store configurations
embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
config = RedisConfig(
    index_name="rights2roof",
    redis_url=REDIS_URL,
    embedding=embeddings
)

#Create vector store and the retreiver
vector_store = RedisVectorStore(embeddings, config=config)
retriever = vector_store.as_retriever(search_type="similarity", search_kwargs={"k": 5})

#Function to populate the vector store from PDF files
def create_vector_store():
    for filename in os.listdir(DIRECTORY_PATH):
        if filename.endswith(".pdf"):
            file_path = os.path.join(DIRECTORY_PATH, filename)
            loader = PyPDFLoader(file_path)
            pages = loader.load_and_split()
            vector_store.add_documents(documents=pages)
            print(f"added {filename} to vector store")

#Get context from vector store based on the query
def get_context(query: str) -> ToolOutput:
    context = retriever.invoke(query)
    return ToolOutput(
        tool="vector_store_tool",
        input={"query": query},
        output={context},
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