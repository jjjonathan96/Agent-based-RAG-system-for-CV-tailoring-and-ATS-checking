import streamlit as st
from PyPDF2 import PdfReader
from langchain.vectorstores import FAISS
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import CharacterTextSplitter

embedder = HuggingFaceEmbeddings()
splitter = CharacterTextSplitter(chunk_size=500, chunk_overlap=100)

def create_vectorstore(text):
    docs = splitter.create_documents([text])
    return FAISS.from_documents(docs, embedder)
 
def extract_text_from_pdf(uploaded_file):
    if uploaded_file is not None:
        reader = PdfReader(uploaded_file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text
    return ""


st.set_page_config(page_title="CV Tailoring App", layout="wide")

st.title("🎯 CV Tailoring with RAG")

# Sidebar options
with st.sidebar:
    st.header("Upload Your Documents")
    general_cv = st.file_uploader("📄 Upload General CV (PDF)", type=["pdf"])
    full_cv = st.file_uploader("📚 Upload Full Experience CV (PDF)", type=["pdf"])
    job_description = st.text_area("📝 Paste Job Description Here", height=300)

    general_cv_extracted = extract_text_from_pdf(general_cv)
    full_cv_extracted = extract_text_from_pdf(full_cv)

    general_cv_db = create_vectorstore(general_cv)
    
    if st.button("🔍 Tailor My CV"):
        if not job_description:
            st.warning("Please provide a job description.")
        else:
            st.session_state["process"] = True

# Main area
if st.session_state.get("process"):
    st.subheader("📌 Tailored CV Preview")
    
    # --- Example placeholders for now ---
    st.markdown("**Summary:** Tailored summary here...")
    st.markdown("**Experience:** Tailored experience here...")
    st.markdown("**Skills:** Tailored skills here...")
    
    st.download_button("📥 Download Tailored CV (PDF)", data="PDF_DATA", file_name="Tailored_CV.pdf")

    # Optional: editable form
    with st.expander("✏️ Edit Tailored CV Before Download"):
        edited_text = st.text_area("Make edits here...", value="Tailored CV content...")
        st.download_button("📥 Download Edited CV", data=edited_text, file_name="Edited_Tailored_CV.txt")

