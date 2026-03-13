from dotenv import load_dotenv
import os

from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import Chroma

load_dotenv()

print("RAG system ready.")

# Load embeddings
embeddings = OpenAIEmbeddings()

# Load existing vector database
vectorstore = Chroma(
    persist_directory="vector_db",
    embedding_function=embeddings
)

# Ask user for a question
query = input("Ask a question: ")

# Retrieve relevant chunks
results = vectorstore.max_marginal_relevance_search(query, k=2)

context = ""

print("\nRetrieved Context:\n")

for doc in results:
    print(doc.page_content)
    print()
    context += doc.page_content + "\n"

# Create LLM
llm = ChatOpenAI(model="gpt-4o-mini")

prompt = f"""
Answer the question using ONLY the context below.

Context:
{context}

Question:
{query}
"""

response = llm.invoke(prompt)

print("\nAnswer:\n")
print(response.content)
