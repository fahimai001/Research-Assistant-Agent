import os
import sqlite3
import tempfile
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
import streamlit as st
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAI
from langchain_google_genai.embeddings import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain_core.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory
from langchain.chains.summarize import load_summarize_chain
from PyPDF2 import PdfReader

# Load environment variables
load_dotenv()
GOOGLE_API_KEY = os.getenv("GEMINI_API_KEY")

# Initialize database
def init_db():
    conn = sqlite3.connect('research_papers.db')
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS papers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        content TEXT,
        summary TEXT,
        source_link TEXT
    )
    ''')
    conn.commit()
    return conn

# Function to extract text from PDF
def extract_text_from_pdf(pdf_file):
    pdf_reader = PdfReader(pdf_file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

# Function to split text into chunks
def split_text(text):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    return text_splitter.split_text(text)

# LLM initialization
def init_llm():
    return GoogleGenerativeAI(
        model="gemini-1.5-flash",
        google_api_key=GOOGLE_API_KEY,
        temperature=0.2,
        top_p=0.8,
        max_output_tokens=2048
    )

# Create embeddings
def init_embeddings():
    return GoogleGenerativeAIEmbeddings(
        google_api_key=GOOGLE_API_KEY,
        model="models/embedding-001"
    )

# Store document in vector store
def create_vector_store(docs, embeddings):
    return FAISS.from_documents(docs, embeddings)

# Generate topic summary
def generate_topic_summary(topic):
    llm = init_llm()
    prompt = PromptTemplate.from_template(
        """
        Provide a comprehensive and concise summary of the topic: {topic}.
        Focus on key aspects, recent developments, and fundamental concepts.
        The summary should be informative and well-structured.
        """
    )
    chain = prompt | llm | StrOutputParser()
    return chain.invoke({"topic": topic})

# Find related topics with sources
def find_related_topics(topic):
    llm = init_llm()
    prompt = PromptTemplate.from_template(
        """
        Identify the top 5 topics closely related to "{topic}". 
        For each topic, provide:
        1. A brief description (2-3 sentences)
        2. A relevant source URL (academic or educational website)
        
        Format the output as follows:
        [
          {{
            "topic": "Topic Name 1",
            "description": "Brief description of Topic 1",
            "source_link": "https://validacademicsource.edu/topic1"
          }},
          ...and so on for all 5 topics
        ]
        
        Make sure all source links are valid URLs to reputable academic sources.
        """
    )
    chain = prompt | llm | StrOutputParser()
    response = chain.invoke({"topic": topic})
    
    # Extract the JSON part from the response
    import json
    try:
        # Try to find and parse JSON in the response
        start_idx = response.find('[')
        end_idx = response.rfind(']') + 1
        if start_idx >= 0 and end_idx > start_idx:
            json_str = response[start_idx:end_idx]
            return json.loads(json_str)
        else:
            # If JSON is not properly formatted, try to parse the whole response
            return json.loads(response)
    except json.JSONDecodeError:
        # Fallback: generate structured format
        return generate_structured_topics(topic, llm)

def generate_structured_topics(topic, llm):
    prompt = PromptTemplate.from_template(
        """
        Generate exactly 5 topics related to "{topic}" in a strictly structured format.
        Each topic must have a name, 2-3 sentence description, and a valid academic source URL.
        Don't include any explanations or additional text.
        
        Return only this JSON array:
        [
          {{"topic": "Related Topic 1", "description": "Description 1", "source_link": "https://source1.edu"}},
          {{"topic": "Related Topic 2", "description": "Description 2", "source_link": "https://source2.edu"}},
          {{"topic": "Related Topic 3", "description": "Description 3", "source_link": "https://source3.edu"}},
          {{"topic": "Related Topic 4", "description": "Description 4", "source_link": "https://source4.edu"}},
          {{"topic": "Related Topic 5", "description": "Description 5", "source_link": "https://source5.edu"}}
        ]
        """
    )
    chain = prompt | llm | StrOutputParser()
    response = chain.invoke({"topic": topic})
    
    import json
    try:
        # Try to find JSON in the response
        start_idx = response.find('[')
        end_idx = response.rfind(']') + 1
        if start_idx >= 0 and end_idx > start_idx:
            json_str = response[start_idx:end_idx]
            return json.loads(json_str)
        else:
            # Create a default structure if parsing fails
            return [
                {"topic": f"Related to {topic} 1", "description": "Information not available", "source_link": "https://scholar.google.com"},
                {"topic": f"Related to {topic} 2", "description": "Information not available", "source_link": "https://scholar.google.com"},
                {"topic": f"Related to {topic} 3", "description": "Information not available", "source_link": "https://scholar.google.com"},
                {"topic": f"Related to {topic} 4", "description": "Information not available", "source_link": "https://scholar.google.com"},
                {"topic": f"Related to {topic} 5", "description": "Information not available", "source_link": "https://scholar.google.com"}
            ]
    except json.JSONDecodeError:
        # Create a default structure if parsing fails
        return [
            {"topic": f"Related to {topic} 1", "description": "Information not available", "source_link": "https://scholar.google.com"},
            {"topic": f"Related to {topic} 2", "description": "Information not available", "source_link": "https://scholar.google.com"},
            {"topic": f"Related to {topic} 3", "description": "Information not available", "source_link": "https://scholar.google.com"},
            {"topic": f"Related to {topic} 4", "description": "Information not available", "source_link": "https://scholar.google.com"},
            {"topic": f"Related to {topic} 5", "description": "Information not available", "source_link": "https://scholar.google.com"}
        ]

# Summarize research paper
def summarize_paper(text):
    llm = init_llm()
    prompt = PromptTemplate.from_template(
        """
        Summarize the following research paper in a comprehensive yet concise manner.
        Include:
        1. The main research question or objective
        2. Key methodologies used
        3. Major findings and results
        4. Significant conclusions and implications
        
        Research paper:
        {text}
        
        Provide a well-structured summary in about 5-7 paragraphs.
        """
    )
    chain = prompt | llm | StrOutputParser()
    # Only pass the first part of the text if it's too long
    return chain.invoke({"text": text[:10000] + "..." if len(text) > 10000 else text})

# Find related papers
def find_related_papers(text):
    llm = init_llm()
    prompt = PromptTemplate.from_template(
        """
        Based on the following research paper excerpt, identify 5 related research papers that would be valuable for further reading.
        
        Research paper excerpt:
        {text}
        
        For each related paper, provide:
        1. Title
        2. Brief description of relevance (2-3 sentences)
        3. A possible source link (academic or educational website)
        
        Format the output as follows:
        [
          {{
            "title": "Paper Title 1",
            "description": "Brief description of relevance",
            "source_link": "https://validacademicsource.edu/paper1"
          }},
          ...and so on for all 5 papers
        ]
        
        Make sure all source links are valid URLs to reputable academic sources.
        """
    )
    chain = prompt | llm | StrOutputParser()
    # Only pass the first part of the text if it's too long
    response = chain.invoke({"text": text[:5000] + "..." if len(text) > 5000 else text})
    
    # Extract the JSON part from the response
    import json
    try:
        # Try to find and parse JSON in the response
        start_idx = response.find('[')
        end_idx = response.rfind(']') + 1
        if start_idx >= 0 and end_idx > start_idx:
            json_str = response[start_idx:end_idx]
            return json.loads(json_str)
        else:
            # If JSON is not properly formatted, try to parse the whole response
            return json.loads(response)
    except json.JSONDecodeError:
        # Fallback: generate structured format for related papers
        return generate_structured_papers(text, llm)

def generate_structured_papers(text, llm):
    prompt = PromptTemplate.from_template(
        """
        Generate exactly 5 research papers related to this excerpt in a strictly structured format:
        
        {text}
        
        Each paper must have a title, 2-3 sentence description, and a valid academic source URL.
        Don't include any explanations or additional text.
        
        Return only this JSON array:
        [
          {{"title": "Related Paper 1", "description": "Description 1", "source_link": "https://source1.edu"}},
          {{"title": "Related Paper 2", "description": "Description 2", "source_link": "https://source2.edu"}},
          {{"title": "Related Paper 3", "description": "Description 3", "source_link": "https://source3.edu"}},
          {{"title": "Related Paper 4", "description": "Description 4", "source_link": "https://source4.edu"}},
          {{"title": "Related Paper 5", "description": "Description 5", "source_link": "https://source5.edu"}}
        ]
        """
    )
    chain = prompt | llm | StrOutputParser()
    # Only pass the first part of the text if it's too long
    response = chain.invoke({"text": text[:3000] + "..." if len(text) > 3000 else text})
    
    import json
    try:
        # Try to find JSON in the response
        start_idx = response.find('[')
        end_idx = response.rfind(']') + 1
        if start_idx >= 0 and end_idx > start_idx:
            json_str = response[start_idx:end_idx]
            return json.loads(json_str)
        else:
            # Create a default structure if parsing fails
            return [
                {"title": "Related Research Paper 1", "description": "Information not available", "source_link": "https://scholar.google.com"},
                {"title": "Related Research Paper 2", "description": "Information not available", "source_link": "https://scholar.google.com"},
                {"title": "Related Research Paper 3", "description": "Information not available", "source_link": "https://scholar.google.com"},
                {"title": "Related Research Paper 4", "description": "Information not available", "source_link": "https://scholar.google.com"},
                {"title": "Related Research Paper 5", "description": "Information not available", "source_link": "https://scholar.google.com"}
            ]
    except json.JSONDecodeError:
        # Create a default structure if parsing fails
        return [
            {"title": "Related Research Paper 1", "description": "Information not available", "source_link": "https://scholar.google.com"},
            {"title": "Related Research Paper 2", "description": "Information not available", "source_link": "https://scholar.google.com"},
            {"title": "Related Research Paper 3", "description": "Information not available", "source_link": "https://scholar.google.com"},
            {"title": "Related Research Paper 4", "description": "Information not available", "source_link": "https://scholar.google.com"},
            {"title": "Related Research Paper 5", "description": "Information not available", "source_link": "https://scholar.google.com"}
        ]

# Store paper in database
def store_paper(title, content, summary, source_link=""):
    conn = init_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO papers (title, content, summary, source_link) VALUES (?, ?, ?, ?)",
        (title, content, summary, source_link)
    )
    conn.commit()
    paper_id = cursor.lastrowid
    conn.close()
    return paper_id

# Get paper from database
def get_paper(paper_id):
    conn = init_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM papers WHERE id = ?", (paper_id,))
    paper = cursor.fetchone()
    conn.close()
    return paper

# Get all papers from database
def get_all_papers():
    conn = init_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, summary FROM papers")
    papers = cursor.fetchall()
    conn.close()
    return papers

# Answer questions about a paper
def answer_question(paper_content, question):
    # Split the paper into chunks
    text_chunks = split_text(paper_content)
    
    # Convert to document format
    documents = [Document(page_content=chunk) for chunk in text_chunks]
    
    # Create embeddings and vector store
    embeddings = init_embeddings()
    vector_store = create_vector_store(documents, embeddings)
    
    # Initialize the LLM
    llm = init_llm()
    
    # Create QA chain
    retriever = vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 3}
    )
    
    # Create the QA chain
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        return_source_documents=False
    )
    
    # Get answer
    response = qa_chain.invoke({"query": question})
    return response["result"]

# Streamlit UI
def main():
    st.set_page_config(page_title="Research Assistant Agent", layout="wide")
    
    st.title("Research Assistant Agent")
    st.markdown("An AI-powered tool to help with research tasks")
    
    # Initialize DB
    init_db()
    
    # Create sidebar for options
    option = st.sidebar.selectbox(
        "Choose Function",
        ["Topic Analysis", "Research Paper Summary", "Question Answering"]
    )
    
    if option == "Topic Analysis":
        st.header("Topic Analysis")
        topic = st.text_input("Enter a topic to research:")
        
        if st.button("Generate Analysis"):
            if topic:
                with st.spinner("Generating topic summary..."):
                    summary = generate_topic_summary(topic)
                    st.subheader("Topic Summary")
                    st.write(summary)
                
                with st.spinner("Finding related topics..."):
                    related_topics = find_related_topics(topic)
                    st.subheader("Related Topics")
                    
                    for i, related in enumerate(related_topics[:5], 1):
                        with st.expander(f"{i}. {related['topic']}"):
                            st.write(related['description'])
                            st.markdown(f"[Source Link]({related['source_link']})")
            else:
                st.warning("Please enter a topic.")
    
    elif option == "Research Paper Summary":
        st.header("Research Paper Summary")
        
        uploaded_file = st.file_uploader("Upload a research paper (PDF)", type="pdf")
        
        if uploaded_file is not None:
            with st.spinner("Processing document..."):
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                    tmp_file.write(uploaded_file.read())
                    tmp_file_path = tmp_file.name
                
                paper_text = extract_text_from_pdf(tmp_file_path)
                os.unlink(tmp_file_path)  # Delete the temp file
                
                if paper_text:
                    paper_title = st.text_input("Paper Title:", value=uploaded_file.name.replace('.pdf', ''))
                    
                    if st.button("Generate Summary"):
                        with st.spinner("Summarizing paper..."):
                            summary = summarize_paper(paper_text)
                            
                            # Store paper in database
                            paper_id = store_paper(paper_title, paper_text, summary)
                            
                            st.subheader("Paper Summary")
                            st.write(summary)
                        
                        with st.spinner("Finding related papers..."):
                            related_papers = find_related_papers(paper_text)
                            st.subheader("Related Papers")
                            
                            for i, paper in enumerate(related_papers[:5], 1):
                                with st.expander(f"{i}. {paper['title']}"):
                                    st.write(paper['description'])
                                    st.markdown(f"[Source Link]({paper['source_link']})")
                else:
                    st.error("Could not extract text from the PDF. Please try a different file.")
    
    elif option == "Question Answering":
        st.header("Question Answering with Research Papers")
        
        # Get list of papers from database
        papers = get_all_papers()
        
        if papers:
            paper_options = {f"{paper[0]}: {paper[1]}": paper[0] for paper in papers}
            selected_paper_title = st.selectbox("Select a paper:", list(paper_options.keys()))
            
            if selected_paper_title:
                paper_id = paper_options[selected_paper_title]
                paper = get_paper(paper_id)
                
                if paper:
                    with st.expander("Paper Summary"):
                        st.write(paper[3])  # Display the summary
                    
                    question = st.text_input("Enter your question about this paper:")
                    
                    if st.button("Get Answer") and question:
                        with st.spinner("Finding answer..."):
                            answer = answer_question(paper[2], question)  # paper[2] is the content
                            st.subheader("Answer")
                            st.write(answer)
                else:
                    st.error("Paper not found.")
        else:
            st.info("No papers found in the database. Please upload a paper using the 'Research Paper Summary' option first.")

if __name__ == "__main__":
    main()