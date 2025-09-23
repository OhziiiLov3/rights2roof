import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers.string import StrOutputParser
from langsmith import traceable

load_dotenv()
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, verbose=True)

# You can use this as a base prompt and modify it if you feel you need to
system_prompt = """
You are a helpful RAG agent that answers questions about the the laws and regulation regarding the rental housing market in California and New York.
Your answers should be detailed and include specific references to the relevant laws and regulations.
Please ONLY use the context provided to you. Do not use any other context.
"""
prompt_template = ChatPromptTemplate.from_messages([
    SystemMessage(content=system_prompt),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{query} {context}")
])

rag_chain = prompt_template | llm | StrOutputParser()

query = "Can a landlord in NYC evict a tenant for not paying rent during a pandemic?"
retriever = vector_store.as_retriever(search_type="similarity", search_kwargs={"k": 5})
# context = retriever.invoke(query)

# response = rag_chain.invoke({"query": query, "context": context, "chat_history": []})
# print (response)


@traceable
def rag_agent(plan: list, query: str):
    try:
        context = retriever.invoke(query)
        result = rag_chain.invoke({"query": query, "context": context})
        return result
    except Exception as e:
        return {"error": str(e)}