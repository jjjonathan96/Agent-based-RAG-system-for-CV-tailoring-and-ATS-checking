# Agent-based-RAG-system-for-CV-tailoring-and-ATS-checking

## System Architecture

### Input:

* General CV (structured format)
* Job Description (JD)
* Optional: Full Work Experience (PDF)

### Processing (RAG Pipeline with Agents):

* Retrieval: Use embeddings to fetch the most relevant CV sections for the JD.
* Generation: LLM tailors the CV to match the JD while maintaining a natural tone.
* ATS Optimization: Checks for keyword matching, formatting, and scoring.
* Editing & Download: User can review, edit, and download the tailored CV.

### Output:
* A tailored CV
* ATS compliance score & feedback
* Optional: Cover letter generation


## RAG-Based CV Tailoring & ATS Workflow

### 1. Data Ingestion

* Extract text from the General CV, Full Work Experience (PDF), and JD
* Convert structured CV data into a vector database (FAISS, ChromaDB)

### 2. RAG-Powered Tailoring

* Retriever: Finds the most relevant sections from past experience.
* LLM Agent (LangChain): Uses the retrieved sections to generate a tailored CV that aligns with the JD.

### 3. ATS Compliance & Scoring

* Keyword Matching: Ensure essential JD keywords are present.
* Formatting Check: Validate CV against ATS-friendly guidelines (PDF/Word compatibility, length).
* Readability & Natural Language: Ensure human-like fluency.

### 4. User Review & PDF Download

* Editable UI (via Streamlit or React) for final tweaks.
* Export final CV as PDF (with OpenAI’s pdf-generation or Python pdfkit).


## Tech Stack

* LLM (LLAMA, FALCON, )
* LangChain (for Agent + RAG)
* FAISS / (for Retrieval)
* Streamlit / (for UI)
* Python (Backend Processing)
* PyMuPDF / PDFKit (for ATS-friendly PDF conversion)


pip install PyPDF2 langchain faiss-cpu sentence-transformers llama-cpp-python
