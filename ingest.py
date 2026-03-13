from dotenv import load_dotenv
import os

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.document_loaders import PyPDFLoader

load_dotenv()

print("Starting multi-document ingestion...")

DATA_FOLDER = "data"

all_documents = []

# Load every PDF in the data folder
for file in os.listdir(DATA_FOLDER):
    if file.endswith(".pdf"):
        path = os.path.join(DATA_FOLDER, file)

        print(f"Loading {file}...")

        loader = PyPDFLoader(path)
        documents = loader.load()

        all_documents.extend(documents)

print(f"Loaded {len(all_documents)} total pages")

# Chunk documents
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=800,
    chunk_overlap=150
)

chunks = text_splitter.split_documents(all_documents)

print(f"Created {len(chunks)} chunks")

# Create embeddings
embeddings = OpenAIEmbeddings()

# Create vector DB
vectorstore = Chroma.from_documents(
    chunks,
    embedding=embeddings,
    persist_directory="vector_db"
)

vectorstore.persist()

print("Vector database created from all PDFs!")