import os
import PyPDF2
import docx
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from typing import List

def extract_text_from_pdf(file_path: str) -> str:
    """Extract text content from a PDF file"""
    try:
        text = ""
        with open(file_path, "rb") as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
        return text
    except Exception as e:
        raise ValueError(f"Error extracting text from PDF: {str(e)}")

def extract_text_from_docx(file_path: str) -> str:
    """Extract text content from a DOCX file"""
    try:
        doc = docx.Document(file_path)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text
    except Exception as e:
        raise ValueError(f"Error extracting text from DOCX: {str(e)}")

def split_text_into_chunks(text: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> List[str]:
    """Split text into chunks for processing"""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    return text_splitter.split_text(text)

def initialize_embeddings(api_key: str) -> GoogleGenerativeAIEmbeddings:
    """Initialize Google Generative AI embeddings"""
    return GoogleGenerativeAIEmbeddings(
        model="models/embedding-001",
        google_api_key=api_key
    )

def create_vector_store(text_chunks: List[str], embeddings: GoogleGenerativeAIEmbeddings):
    """Create FAISS vector store from text chunks"""
    return FAISS.from_texts(text_chunks, embeddings)

def create_rag_chain(vector_store, model) -> RunnablePassthrough:
    """Create RAG chain for question answering"""
    retriever = vector_store.as_retriever(search_kwargs={"k": 3})
    
    rag_prompt = ChatPromptTemplate.from_template(
        """
        You are an AI research assistant specializing in academic papers. Your task is to provide detailed and accurate answers to questions about research papers.
        
        Relevant sections from the paper:
        {context}
        
        Question: {question}
        
        Instructions:
        1. Provide a comprehensive answer based on the content from the paper.
        2. Include specific details, explanations, and examples from the paper when relevant.
        3. If appropriate, mention figures, tables, or specific sections referenced in the text.
        4. If the question cannot be answered from the provided content, explain why and what information might be needed.
        5. Use a clear, academic style appropriate for discussing research.
        6. Structure your answer with paragraphs for readability.
        7. If you quote directly from the paper, indicate this with quotation marks.
        
        Your detailed answer:
        """
    )
    
    return (
        {"context": retriever, "question": RunnablePassthrough()}
        | rag_prompt
        | model
        | StrOutputParser()
    )

def process_document(file_path: str, api_key: str):
    """Process a document and return RAG components"""
    file_extension = os.path.splitext(file_path)[1].lower()
    
    if file_extension == '.pdf':
        text_content = extract_text_from_pdf(file_path)
    elif file_extension in ['.docx', '.doc']:
        text_content = extract_text_from_docx(file_path)
    else:
        raise ValueError("Unsupported file format")
    
    text_chunks = split_text_into_chunks(text_content)
    embeddings = initialize_embeddings(api_key)
    vector_store = create_vector_store(text_chunks, embeddings)
    
    return vector_store