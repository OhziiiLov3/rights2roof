# RAG Agent Documentation

## Overview
The RAG (Retrieval-Augmented Generation) agent is designed to answer questions about rental housing laws and regulations in California and New York. It uses a combination of document retrieval and a language model to provide detailed, context-aware responses with references to relevant laws.

## Main Components
- **PDF Loading:** Loads and splits PDF documents from the `app/resources/files` directory using `PyPDFLoader`.
- **Text Splitting:** Uses `RecursiveCharacterTextSplitter` to break documents into manageable chunks for embedding and retrieval.
- **Embeddings:** Generates vector embeddings for document chunks using OpenAI's `text-embedding-3-large` model.
- **Vector Store:** Stores document embeddings in a persistent Chroma vector store (`app/resources/vector-store`).
- **Retriever:** Retrieves relevant document chunks based on semantic similarity to the user's query.
- **Prompt Template:** Defines the system prompt and message structure for the language model.
- **Language Model:** Uses `ChatOpenAI` (GPT-4o-mini) to generate answers based on retrieved context and user questions.

## Workflow
1. **Document Preparation:**
   - PDFs are loaded and split into pages.
   - Pages are further split into chunks.
   - Chunks are embedded and added to the vector store.
2. **Query Handling:**
   - User question is processed.
   - Retriever finds the most relevant chunks from the vector store.
   - The language model generates a response using the retrieved context and the system prompt.

## Key Functions and Classes
- `OpenAIEmbeddings`: Creates vector embeddings for text chunks.
- `ChatOpenAI`: Language model for generating answers.
- `ChatPromptTemplate`: Template for structuring prompts to the language model.

## Example Usage
```python
query = "Can a landlord in NYC evict a tenant for not paying rent during a pandemic?"
retriever = vector_store.as_retriever(search_kwargs={"k": 5})
context = retriever.invoke(query)
response = rag_chain.invoke({"question": query, "context": context, "chat_history": []})
print(response.content)
```

## Error Handling
- Exceptions during PDF loading and vector store operations are caught and printed for debugging.
- Ensure all document chunks are valid `Document` objects before adding to the vector store.

## Customization
- Update the system prompt in `rag_agent.py` to change the agent's behavior or supported jurisdictions.
- Add or remove PDF files in `app/resources/files` to update the knowledge base.

## Dependencies
- `langchain`
- `langchain_openai`
- `dotenv`

## File Location
- Main agent code: `app/agents/rag_agent.py`
- PDF resources: `app/resources/files/`
- Vector store: 'Redis'

## Contact
For questions or issues, contact the project maintainer or refer to the README.md for setup instructions.
