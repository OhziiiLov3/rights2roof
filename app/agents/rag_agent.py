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
from langchain_openai import OpenAIEmbeddings
from langchain_redis import RedisConfig, RedisVectorStore
from langchain_community.document_loaders import PyPDFLoader
# from langchain_core.output_parsers import PydanticOutputParser
# from app.models.schemas import RAGAgentResponse

load_dotenv()
DIRECTORY_PATH = "app/resources/files"

REDIS_URL=os.getenv("REDIS_URL", "redis://localhost:32771")
redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST","localhost"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    db=0,
    decode_responses=True
)
embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
config = RedisConfig(
    index_name="rights2roof",
    redis_url=REDIS_URL,
    embedding=embeddings
)

#create vector store in Redis
vector_store = RedisVectorStore(embeddings, config=config)

def create_vector_store():
    for filename in os.listdir(DIRECTORY_PATH):
        if filename.endswith(".pdf"):
            file_path = os.path.join(DIRECTORY_PATH, filename)
            loader = PyPDFLoader(file_path)
            pages = loader.load_and_split()
            vector_store.add_documents(documents=pages)
            print(f"added {filename} to vector store")

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, verbose=True)
# rag_agent_response = PydanticOutputParser(pydantic_object=RAGAgentResponse)

#Base prompt for RAG agent
system_prompt = """
You are a helpful RAG agent that answers questions about the the laws and regulation regarding the rental housing market in California and New York.
Your answers should be detailed and include specific references to the relevant laws and regulations.
Please ONLY use the context provided to you. Do not use any other context.
If you don't know the answer, just say that you don't know. DO NOT try to make up an answer.
"""

prompt_template = ChatPromptTemplate.from_messages([
    SystemMessage(content=system_prompt),
    ("human", "{plan} {query} {context}")
])

rag_chain = prompt_template | llm | StrOutputParser()

query = "Can a landlord in NYC evict a tenant for not paying rent during a pandemic?"
retriever = vector_store.as_retriever(search_type="similarity", search_kwargs={"k": 5})


@traceable
def rag_agent(plan: list, query: str):
    try:
        context = retriever.invoke(query)
        result = rag_chain.invoke({"plan": plan, "query": query, "context": context})
        return result
    except Exception as e:
        return {"error": str(e)}