PAGE_TITLE = "Research Paper Explainer"
CAPTION = "Upload academic PDFs and ask questions — get plain-language answers"


import os
import tempfile
import streamlit as st
from dotenv import load_dotenv

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import Chroma
from langchain_community.document_loaders import PyPDFLoader

load_dotenv()

# ── Page config ──────────────────────────────────────────────
st.set_page_config(page_title=PAGE_TITLE, layout="wide")
st.title(PAGE_TITLE)
st.caption(CAPTION)

# ── Session state defaults ───────────────────────────────────
if "vectorstore" not in st.session_state:
    st.session_state.vectorstore = None
if "ingested_files" not in st.session_state:
    st.session_state.ingested_files = []

# ── Sidebar: PDF Upload & Ingest ─────────────────────────────
st.sidebar.header("📄 Upload Papers")
uploaded_files = st.sidebar.file_uploader(
    "Upload one or more academic PDFs",
    type=["pdf"],
    accept_multiple_files=True,
)

if st.sidebar.button("Ingest papers") and uploaded_files:
    with st.sidebar:
        with st.spinner("Reading and chunking PDFs..."):
            all_documents = []

            # Save uploaded files to a temp dir and load with PyPDFLoader
            with tempfile.TemporaryDirectory() as tmp_dir:
                for uploaded in uploaded_files:
                    tmp_path = os.path.join(tmp_dir, uploaded.name)
                    with open(tmp_path, "wb") as f:
                        f.write(uploaded.getbuffer())

                    loader = PyPDFLoader(tmp_path)
                    docs = loader.load()
                    all_documents.extend(docs)

            # Chunk
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=800,
                chunk_overlap=150,
            )
            chunks = splitter.split_documents(all_documents)

        with st.spinner("Creating embeddings & vector DB..."):
            embeddings = OpenAIEmbeddings()
            vectorstore = Chroma.from_documents(
                chunks,
                embedding=embeddings,
                persist_directory="vector_db",
            )
            st.session_state.vectorstore = vectorstore
            st.session_state.ingested_files = [f.name for f in uploaded_files]

        st.success(
            f"✅ Ingested **{len(uploaded_files)}** PDF(s) → "
            f"**{len(all_documents)}** pages → **{len(chunks)}** chunks"
        )

# Show currently loaded papers
if st.session_state.ingested_files:
    st.sidebar.markdown("**Loaded papers:**")
    for name in st.session_state.ingested_files:
        st.sidebar.markdown(f"- {name}")

# ── Main area: Ask a Question ────────────────────────────────
st.markdown("Ask a question about the uploaded paper(s). "
            "The app will retrieve relevant sections and explain the findings in plain language.")

question = st.text_area(
    "Your question",
    height=120,
    placeholder="e.g. What were the main findings of this study?",
)

if st.button("Get answer"):
    if st.session_state.vectorstore is None:
        st.warning("Please upload and ingest at least one PDF first (use the sidebar).")
    elif not question.strip():
        st.warning("Please type a question first.")
    else:
        with st.spinner("Searching papers & generating answer..."):
            # Retrieve relevant chunks
            results = st.session_state.vectorstore.max_marginal_relevance_search(
                question, k=4
            )
            context = "\n\n".join(doc.page_content for doc in results)

            # Build RAG prompt — plain language, no jargon
            prompt = f"""
You are a research translator. Your job is to help people understand
academic papers without any experimental or technical jargon.

Using ONLY the context below from the uploaded research paper(s),
answer the user's question.

Rules:
- Explain as if talking to a curious person with no background in the field.
- If a technical term is unavoidable, define it in parentheses.
- Highlight the key takeaway, what the researchers did (simplified),
  and why it matters in the real world.
- Use bullet points for clarity.
- If the context doesn't contain enough info, say so honestly.

Context from the paper(s):
{context}

Question:
{question}
"""
            llm = ChatOpenAI(model="gpt-4o-mini")
            response = llm.invoke(prompt)

        st.subheader("Answer")
        st.write(response.content)

        # Show retrieved chunks in an expander for transparency
        with st.expander("📚 Retrieved context from paper(s)"):
            for i, doc in enumerate(results, 1):
                st.markdown(f"**Chunk {i}:**")
                st.text(doc.page_content)
                st.markdown("---")
