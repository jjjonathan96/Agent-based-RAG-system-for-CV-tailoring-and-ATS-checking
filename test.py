from PyPDF2 import PdfReader
from langchain.vectorstores import FAISS
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import CharacterTextSplitter
from langchain.llms import LlamaCpp
from langchain.chains import RetrievalQA


def extract_text_from_pdf(pdf_path):
    reader = PdfReader(pdf_path)
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def create_vectorstore(text):
    splitter = CharacterTextSplitter(chunk_size=500, chunk_overlap=100)
    embedder = HuggingFaceEmbeddings()
    docs = splitter.create_documents([text])
    return FAISS.from_documents(docs, embedder)


def tailor_cv(cv_vectorstore, job_description, model_path):
    llm = LlamaCpp(
        model_path=model_path,
        n_ctx=2048,
        n_threads=4,
        temperature=0.7
    )
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=cv_vectorstore.as_retriever(),
        return_source_documents=False
    )
    return qa_chain.run(f"Tailor this CV to match the following job: {job_description}")


if __name__ == "__main__":
    # Input file paths and job description
    general_cv_path = "your_general_cv.pdf"
    full_cv_path = "your_full_cv.pdf"
    model_path = "path/to/your/model.gguf"

    job_description = """
    We're hiring a Data Scientist with experience in LLMs, RAG, and MLOps. 
    The ideal candidate should have a strong foundation in NLP, LangChain, and vector databases like FAISS.
    """

    # Extract text
    full_cv_text = extract_text_from_pdf(full_cv_path)
    general_cv_text = extract_text_from_pdf(general_cv_path)

    # Create vector store
    vectorstore = create_vectorstore(full_cv_text)

    # Run RAG pipeline
    tailored_cv = tailor_cv(vectorstore, job_description, model_path)

    # Output result
    print("\n==== Tailored CV ====\n")
    print(tailored_cv)
