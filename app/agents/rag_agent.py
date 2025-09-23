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
from pydantic import BaseModel, Field
# from langchain_core.output_parsers import PydanticOutputParser
# from app.models.schemas import RAGAgentResponse

load_dotenv()
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, verbose=True)
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

#initialize the vector store and retreiver
vector_store = RedisVectorStore(embeddings, config=config)
retriever = vector_store.as_retriever(search_type="similarity", search_kwargs={"k": 5})


#Base prompt for RAG agent
system_prompt = """
    You are a helpful RAG agent that answers questions about the the laws and regulation regarding the rental housing market in California and New York.
    Your answers should be detailed and include specific references to the relevant laws and regulations.
    Please ONLY use the context provided to you. Do not use any other context.
    If you don't know the answer, just say that you don't know. DO NOT try to make up an answer.
    """
#You must provide the response in the the format defined by the RAGAgentResponse schema. 

prompt_template = ChatPromptTemplate.from_messages([
    SystemMessage(content=system_prompt),
    ("human", "{plan} {query} {context}")
])

# rag_agent_response = PydanticOutputParser(pydantic_object=RAGAgentResponse)
# rag_chain = prompt_template | llm | rag_agent_response

#llm chain to process the prompt and generate a response
rag_chain = prompt_template | llm | StrOutputParser()

@traceable
def rag_agent(plan: list, query: str):
    try:
        context = retriever.invoke(query)
        result = rag_chain.invoke({"plan": plan, "query": query, "context": context})
        return result
    except Exception as e:
        return {"error": str(e)}

print(rag_agent(["Step 1: Use the vector store to get relevant context based on the user's query."], "What are the tenant rights in NYC regarding rent increases?"))