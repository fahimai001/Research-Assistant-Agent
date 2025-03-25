# import os
# import io
# import re
# import tempfile
# from typing import List, Optional, Dict, Any
# from datetime import datetime
# import PyPDF2
# import docx
# from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader
# from langchain.text_splitter import RecursiveCharacterTextSplitter

# from database import save_file_to_database, save_summary_to_database, get_paper_from_database

# def extract_text_from_pdf(file_path: str) -> str:
#     """Extract text content from a PDF file"""
#     try:
#         loader = PyPDFLoader(file_path)
#         documents = loader.load()
#         text_content = "\n\n".join([doc.page_content for doc in documents])
#         return text_content
#     except Exception as e:
#         print(f"Error extracting text from PDF: {str(e)}")
#         # Fallback method
#         text = ""
#         with open(file_path, "rb") as file:
#             pdf_reader = PyPDF2.PdfReader(file)
#             for page in pdf_reader.pages:
#                 text += page.extract_text() + "\n"
#         return text

# def extract_text_from_docx(file_path: str) -> str:
#     """Extract text content from a DOCX file"""
#     try:
#         loader = Docx2txtLoader(file_path)
#         documents = loader.load()
#         text_content = "\n\n".join([doc.page_content for doc in documents])
#         return text_content
#     except Exception as e:
#         print(f"Error extracting text from DOCX: {str(e)}")
#         # Fallback method
#         doc = docx.Document(file_path)
#         text = ""
#         for para in doc.paragraphs:
#             text += para.text + "\n"
#         return text

# def save_markdown_file(topic_or_filename: str, content: str, output_dir: str = "../output") -> str:
#     """Save content to a markdown file"""
#     # Create output directory if it doesn't exist
#     os.makedirs(output_dir, exist_ok=True)
    
#     # Clean filename
#     clean_name = re.sub(r'[^\w\s-]', '', topic_or_filename).strip().lower()
#     clean_name = re.sub(r'[-\s]+', '-', clean_name)
    
#     # Add timestamp to avoid overwriting
#     timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#     filename = f"{clean_name}_{timestamp}.md"
    
#     file_path = os.path.join(output_dir, filename)
    
#     with open(file_path, "w", encoding="utf-8") as file:
#         file.write(content)
    
#     return file_path

# def chunk_text(text: str, chunk_size: int = 4000, overlap: int = 200) -> List[str]:
#     """Split text into manageable chunks for processing"""
#     text_splitter = RecursiveCharacterTextSplitter(
#         chunk_size=chunk_size,
#         chunk_overlap=overlap,
#         length_function=len,
#     )
#     chunks = text_splitter.split_text(text)
#     return chunks

# def upload_research_paper_file(file_path: str) -> Dict[str, Any]:
#     """Process an uploaded research paper file and store it in the database"""
#     try:
#         filename = os.path.basename(file_path)
#         file_extension = os.path.splitext(filename)[1].lower()
        
#         if file_extension == '.pdf':
#             content = extract_text_from_pdf(file_path)
#             file_type = 'pdf'
#         elif file_extension in ['.docx', '.doc']:
#             content = extract_text_from_docx(file_path)
#             file_type = 'docx'
#         else:
#             return {
#                 "filename": filename,
#                 "success": False,
#                 "error": f"Unsupported file type: {file_extension}"
#             }
        
#         # Check if we have content
#         if not content or len(content.strip()) < 100:
#             return {
#                 "filename": filename,
#                 "success": False,
#                 "error": "Could not extract meaningful content from file"
#             }
        
#         # Save to database
#         paper_id = save_file_to_database(filename, content, file_type)
        
#         return {
#             "filename": filename,
#             "paper_id": paper_id,
#             "content": content,
#             "success": True
#         }
    
#     except Exception as e:
#         return {
#             "filename": os.path.basename(file_path) if file_path else "Unknown",
#             "success": False,
#             "error": f"Error processing file: {str(e)}"
#         }

# def process_research_paper(paper_id: int, paper_summary_chain=None, paper_recommendation_chain=None, model=None) -> Dict[str, Any]:
#     """Process a research paper by creating a summary and recommendations"""
#     try:
#         # Import here to avoid circular imports
#         from recommendation_papers import generate_paper_recommendations
        
#         # Retrieve paper from database
#         paper_data = get_paper_from_database(paper_id)
#         if not paper_data:
#             return {
#                 "paper_id": paper_id,
#                 "success": False,
#                 "error": "Paper not found in database"
#             }
        
#         filename = paper_data["filename"]
#         content = paper_data["content"]
        
#         print(f"Processing paper: {filename}")
        
#         # Check if content is too large and chunk if needed
#         if len(content) > 30000:  # If content is very large
#             print("- Paper content is large, processing in chunks...")
#             chunks = chunk_text(content)
            
#             # Process first chunk for summary (usually contains abstract, intro)
#             first_chunk = chunks[0]
#             summary_content = paper_summary_chain.invoke({"paper_content": first_chunk})
            
#             # For recommendations, use a combination of chunks if possible
#             combined_chunks = ""
#             for i, chunk in enumerate(chunks):
#                 if i > 2:  # Limit to first few chunks for recommendations
#                     break
#                 combined_chunks += chunk + "\n\n"
                
#             if len(combined_chunks) > 15000:  # If still too large
#                 combined_chunks = combined_chunks[:15000]
                
#             recommendations_content = generate_paper_recommendations(combined_chunks, paper_recommendation_chain, model)
#         else:
#             # Generate summary
#             print("- Generating paper summary...")
#             summary_content = paper_summary_chain.invoke({"paper_content": content})
            
#             # Generate recommendations
#             print("- Finding related papers...")
#             recommendations_content = generate_paper_recommendations(content, paper_recommendation_chain, model)
        
#         # Save summary to database
#         save_summary_to_database(paper_id, summary_content)
        
#         # Create full analysis
#         from agent import create_full_paper_analysis
#         full_analysis = create_full_paper_analysis(filename, summary_content, recommendations_content)
        
#         # Save to file
#         report_filename = save_markdown_file(filename, full_analysis)
        
#         return {
#             "paper_id": paper_id,
#             "filename": filename,
#             "summary_content": summary_content,
#             "recommendations_content": recommendations_content,
#             "full_analysis": full_analysis,
#             "report_filename": report_filename,
#             "success": True
#         }
    
#     except Exception as e:
#         return {
#             "paper_id": paper_id,
#             "success": False,
#             "error": f"Error processing paper: {str(e)}"
#         }