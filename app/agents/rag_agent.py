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
from langchain_core.documents import Document
import redis
from langchain_openai import OpenAIEmbeddings
from langchain_redis import RedisConfig, RedisVectorStore
from pydantic import BaseModel, Field
from langchain_core.output_parsers import PydanticOutputParser
from app.models.schemas import RagAgentResponse
from app.tools.vector_store_tool import get_context

load_dotenv()
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, verbose=True)
DIRECTORY_PATH = "app/resources/files"

#Base prompt for RAG agent
system_prompt = """
    You are a helpful RAG agent that answers questions about the the laws and regulation regarding the rental housing market in California and New York.
    Your answers should be detailed and include specific references to the relevant laws and regulations.
    Please ONLY use the context provided to you. Do not use any other context.
    If you don't know the answer, just say that you don't know. DO NOT try to make up an answer.
    You must provide the response in the the format: 
    {
      "query": "The user's original query here",
      "response": "Response to the user's query based on the context provided"
    }
    """

prompt_template = ChatPromptTemplate.from_messages([
    SystemMessage(content=system_prompt),
    ("human", "{plan} {query} {context}")
])

rag_agent_response = PydanticOutputParser(pydantic_object=RagAgentResponse)
rag_chain = prompt_template | llm | rag_agent_response

#llm chain to process the prompt and generate a response
@traceable
def rag_agent(plan: list, query: str):
    try:
        context = get_context(query).output
        result = rag_chain.invoke({"plan": plan, "query": query, "context": context})
        return result
    except Exception as e:
        return {"error": str(e)}

# print(rag_agent(["Step 1: Use the vector store to get relevant context based on the user's query."], "What are the tenant rights in NYC regarding rent increases?"))