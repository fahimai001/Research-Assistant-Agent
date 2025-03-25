import os
import io
import re
import tempfile
from typing import List, Optional, Dict, Any
from datetime import datetime
import PyPDF2
import docx
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

from database import save_file_to_database, save_summary_to_database, get_paper_from_database

def extract_text_from_pdf(file_path: str) -> str:
    try:
        loader = PyPDFLoader(file_path)
        documents = loader.load()
        text_content = "\n\n".join([doc.page_content for doc in documents])
        return text_content
    except Exception as e:
        text = ""
        with open(file_path, "rb") as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
        return text

def extract_text_from_docx(file_path: str) -> str:
    try:
        loader = Docx2txtLoader(file_path)
        documents = loader.load()
        text_content = "\n\n".join([doc.page_content for doc in documents])
        return text_content
    except Exception as e:
        doc = docx.Document(file_path)
        text = ""
        for para in doc.paragraphs:
            text += para.text + "\n"
        return text

def save_markdown_file(topic_or_filename: str, content: str, output_dir: str = "../output") -> str:
    os.makedirs(output_dir, exist_ok=True)
    clean_name = re.sub(r'[^\w\s-]', '', topic_or_filename).strip().lower()
    clean_name = re.sub(r'[-\s]+', '-', clean_name)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{clean_name}_{timestamp}.md"
    file_path = os.path.join(output_dir, filename)
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(content)
    return file_path

def chunk_text(text: str, chunk_size: int = 4000, overlap: int = 200) -> List[str]:
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=overlap,
        length_function=len,
    )
    chunks = text_splitter.split_text(text)
    return chunks

def upload_research_paper_file(file_path: str) -> Dict[str, Any]:
    try:
        filename = os.path.basename(file_path)
        file_extension = os.path.splitext(filename)[1].lower()
        if file_extension == '.pdf':
            content = extract_text_from_pdf(file_path)
            file_type = 'pdf'
        elif file_extension in ['.docx', '.doc']:
            content = extract_text_from_docx(file_path)
            file_type = 'docx'
        else:
            return {"filename": filename, "success": False, "error": f"Unsupported file type: {file_extension}"}
        if not content or len(content.strip()) < 100:
            return {"filename": filename, "success": False, "error": "Could not extract meaningful content from file"}
        paper_id = save_file_to_database(filename, content, file_type)
        return {"filename": filename, "paper_id": paper_id, "content": content, "success": True}
    except Exception as e:
        return {"filename": os.path.basename(file_path) if file_path else "Unknown", "success": False, "error": f"Error processing file: {str(e)}"}

def process_research_paper(paper_id: int, paper_summary_chain=None, paper_recommendation_chain=None, model=None) -> Dict[str, Any]:
    try:
        from recommendation_papers import generate_paper_recommendations
        paper_data = get_paper_from_database(paper_id)
        if not paper_data:
            return {"paper_id": paper_id, "success": False, "error": "Paper not found in database"}
        filename = paper_data["filename"]
        content = paper_data["content"]
        if len(content) > 30000:
            chunks = chunk_text(content)
            first_chunk = chunks[0]
            summary_content = paper_summary_chain.invoke({"paper_content": first_chunk})
            combined_chunks = ""
            for i, chunk in enumerate(chunks):
                if i > 2:
                    break
                combined_chunks += chunk + "\n\n"
            if len(combined_chunks) > 15000:
                combined_chunks = combined_chunks[:15000]
            recommendations_content = generate_paper_recommendations(combined_chunks, paper_recommendation_chain, model)
        else:
            summary_content = paper_summary_chain.invoke({"paper_content": content})
            recommendations_content = generate_paper_recommendations(content, paper_recommendation_chain, model)
        save_summary_to_database(paper_id, summary_content)
        from agent import create_full_paper_analysis
        full_analysis = create_full_paper_analysis(filename, summary_content, recommendations_content)
        report_filename = save_markdown_file(filename, full_analysis)
        return {"paper_id": paper_id, "filename": filename, "summary_content": summary_content, "recommendations_content": recommendations_content, "full_analysis": full_analysis, "report_filename": report_filename, "success": True}
    except Exception as e:
        return {"paper_id": paper_id, "success": False, "error": f"Error processing paper: {str(e)}"}
