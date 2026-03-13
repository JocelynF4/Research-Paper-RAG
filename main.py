from dotenv import load_dotenv
import os

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import Chroma

load_dotenv()

print("API Key Loaded:", bool(os.getenv("OPENAI_API_KEY")))

# Load document
with open("data/sample.txt", "r", encoding="utf-8") as f:
    document = f.read()

# Chunk document
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=200,
    chunk_overlap=50
)

chunks = text_splitter.split_text(document)

print(f"\nCreated {len(chunks)} chunks")

# Create embeddings
embeddings = OpenAIEmbeddings()

# Create vector database
vectorstore = Chroma.from_texts(
    chunks,
    embedding=embeddings,
    persist_directory="vector_db"
)

print("\nVector DB ready")

# User question
query = "How does RAG improve LLM responses?"

# Retrieve relevant chunks
results = vectorstore.max_marginal_relevance_search(query, k=2)

print("\nRetrieved Context:\n")

context = ""

for doc in results:
    print(doc.page_content)
    print()
    context += doc.page_content + "\n"

# Create LLM
llm = ChatOpenAI(model="gpt-4o-mini")

# RAG prompt
prompt = f"""
Answer the question using ONLY the context below.

Context:
{context}

Question:
{query}
"""

# Generate answer
response = llm.invoke(prompt)

print("\nRAG Answer:\n")
print(response.content)
