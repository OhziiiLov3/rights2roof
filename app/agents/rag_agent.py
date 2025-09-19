import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from typing import List, Dict, Any
from langchain_core.output_parsers.string import StrOutputParser
from langsmith import traceable
from app.tools.vector_store_tool import create_vector_store



load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

llm = ChatOpenAI(model="gpt-4.1-mini", temperature=0, openai_api_key=OPENAI_API_KEY) # Set up the chat model here
system_message = f""" 
You are a research agent. 
Based on the users query, look into the context available to you to generate an appropriate response.
"""

rag_prompt = ChatPromptTemplate.from_messages([
    SystemMessage(content=system_message),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{query}" "{context}")
])

rag_chain = rag_prompt | llm | StrOutputParser()
vector_store = create_vector_store()

@traceable
def rag_agent(query: str, history: List[Dict[str, Any]]):
  retriever = vector_store.as_retriever(search_kwargs={"k": 5})
  try:
    context = retriever.invoke(query)
    response = rag_chain.invoke({"query": query, "context": context, "chat_history": history})
    return response
  except Exception as e:
    return {"error": str(e)}
 
print(rag_agent("Can landlord evict me in nyc without notice?", []))