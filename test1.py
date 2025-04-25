import streamlit as st
import os
from PyPDF2 import PdfReader
from langchain.vectorstores import FAISS
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import CharacterTextSplitter
from langchain.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA

# Set your OpenAI API key
os.environ["OPENAI_API_KEY"] = "your-api-key-here"  # or use st.secrets

st.set_page_config(page_title="CV Tailoring App", layout="centered")

st.title("🧠 CV Tailoring using RAG + OpenAI")

# Uploads
general_cv = st.file_uploader("📄 Upload General CV (PDF)", type=["pdf"])
full_cv = st.file_uploader("📚 Upload Full Experience CV (PDF)", type=["pdf"])
job_description = st.text_area("📝 Paste Job Description")

# Utility - Extract text
def extract_text_from_pdf(uploaded_file):
    if uploaded_file is not None:
        reader = PdfReader(uploaded_file)
        return "\n".join([page.extract_text() or "" for page in reader.pages])
    return ""

# Vector store creation
def create_vectorstore(text):
    splitter = CharacterTextSplitter(chunk_size=500, chunk_overlap=100)
    embedder = HuggingFaceEmbeddings()
    docs = splitter.create_documents([text])
    return FAISS.from_documents(docs, embedder)

# Tailor CV using OpenAI
def tailor_cv_with_openai(vectorstore, job_description):
    llm = ChatOpenAI(temperature=0.3, model_name="gpt-3.5-turbo")
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=vectorstore.as_retriever(),
        return_source_documents=False
    )
    query = f"""You are a professional CV writer. Using the information provided in the full experience CV, tailor a CV to match this job description:

{job_description}

Make it human-sounding and well-structured."""
    return qa_chain.run(query)

# Main Action
if st.button("🔍 Tailor My CV"):
    if full_cv and job_description:
        with st.spinner("🔧 Processing..."):
            full_text = extract_text_from_pdf(full_cv)
            vectorstore = create_vectorstore(full_text)
            tailored_output = tailor_cv_with_openai(vectorstore, job_description)

        st.subheader("📌 Tailored CV Preview")
        st.markdown(tailored_output)
        st.download_button("📥 Download Tailored CV", data=tailored_output, file_name="Tailored_CV.txt")
    else:
        st.warning("Please upload your Full CV and paste the Job Description.")
