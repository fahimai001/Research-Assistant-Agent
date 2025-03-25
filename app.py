import os
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
import tempfile
from werkzeug.utils import secure_filename
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))
from flask import session



# Import functions from your existing code
from src.agent import (
    load_environment,
    initialize_model,
    create_chains,
    research_topic,
    create_prompt_templates
)

from src.rag import (
    extract_text_from_pdf,
    extract_text_from_docx,
    split_text_into_chunks,
    initialize_embeddings,
    create_vector_store,
    create_rag_chain
)

from output_schemas import define_output_schemas
from database import initialize_database, get_paper_from_database
from document_processor import process_research_paper, upload_research_paper_file

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size
app.config['DATABASE_PATH'] = os.path.abspath(os.path.join(os.getcwd(), 'data', 'research_papers.db'))

# Create required directories
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(os.path.dirname(app.config['DATABASE_PATH']), exist_ok=True)

# Set the database path as an environment variable so all modules can access it
os.environ['DATABASE_PATH'] = app.config['DATABASE_PATH']

# Initialize the research assistant components
def init_components():
    # Load API key
    api_key = load_environment()
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in environment variables or .env file")
    
    # Initialize database with the correct path
    initialize_database(app.config['DATABASE_PATH'])
    
    # Initialize model
    model = initialize_model(api_key)
    
    # Create prompt templates
    report_prompt, recommendation_prompt, paper_summary_prompt, paper_recommendation_prompt = create_prompt_templates()
    
    # Define output schemas
    TopicRecommendations, PaperRecommendations = define_output_schemas()
    
    # Create processing chains
    report_chain, recommendation_chain, paper_summary_chain, paper_recommendation_chain = create_chains(
        model, 
        report_prompt, 
        recommendation_prompt, 
        paper_summary_prompt, 
        paper_recommendation_prompt,
        TopicRecommendations,
        PaperRecommendations
    )
    
    return {
        "model": model,
        "report_chain": report_chain,
        "recommendation_chain": recommendation_chain,
        "paper_summary_chain": paper_summary_chain,
        "paper_recommendation_chain": paper_recommendation_chain
    }

# Global components
try:
    components = init_components()
except Exception as e:
    print(f"Error initializing components: {str(e)}")
    components = None

# Helper functions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'pdf', 'docx', 'doc'}

def parse_markdown_to_html(markdown_text):
    """
    Simple markdown parser for converting markdown to HTML
    """
    import re
    
    # Convert headings
    markdown_text = re.sub(r'^# (.*?)$', r'<h1>\1</h1>', markdown_text, flags=re.MULTILINE)
    markdown_text = re.sub(r'^## (.*?)$', r'<h2>\1</h2>', markdown_text, flags=re.MULTILINE)
    markdown_text = re.sub(r'^### (.*?)$', r'<h3>\1</h3>', markdown_text, flags=re.MULTILINE)
    
    # Convert links
    markdown_text = re.sub(r'\[(.*?)\]\((.*?)\)', r'<a href="\2" target="_blank">\1</a>', markdown_text)
    
    # Convert bold text
    markdown_text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', markdown_text)
    
    # Convert italic text
    markdown_text = re.sub(r'\*(.*?)\*', r'<em>\1</em>', markdown_text)
    
    # Convert paragraphs (add line breaks)
    markdown_text = re.sub(r'\n\n', r'</p><p>', markdown_text)
    
    # Wrap in paragraph tags
    markdown_text = f'<p>{markdown_text}</p>'
    
    return markdown_text

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/topic_analysis', methods=['GET', 'POST'])
def topic_analysis():
    if request.method == 'POST':
        topic = request.form.get('topic')
        if not topic:
            flash('Please enter a topic')
            return redirect(url_for('topic_analysis'))
        
        try:
            return redirect(url_for('generate_report', topic=topic))
        except Exception as e:
            flash(f'Error: {str(e)}')
            return redirect(url_for('topic_analysis'))
    
    return render_template('topic_analysis.html')

@app.route('/generate_report/<topic>')
def generate_report(topic):
    try:
        if not components:
            flash('Research Assistant components not initialized properly')
            return redirect(url_for('index'))
        
        result = research_topic(
            topic,
            components["report_chain"],
            components["recommendation_chain"],
            components["model"]
        )
        
        if not result.get("success", False):
            flash(f'Error: {result.get("error", "Unknown error")}')
            return redirect(url_for('topic_analysis'))
        
        report_content_html = parse_markdown_to_html(result.get("report_content", ""))
        
        return render_template(
            'report.html',
            topic=topic,
            report_content=report_content_html,
            has_recommendations=True
        )
    except Exception as e:
        flash(f'Error generating report: {str(e)}')
        return redirect(url_for('topic_analysis'))

@app.route('/recommendations/<topic>')
def recommendations(topic):
    try:
        if not components:
            flash('Research Assistant components not initialized properly')
            return redirect(url_for('index'))
        
        # Import here to avoid circular imports
        from recommendation_topics import generate_recommendations
        
        recommendations_content = generate_recommendations(
            topic,
            components["recommendation_chain"],
            components["model"]
        )
        
        recommendations_html = parse_markdown_to_html(recommendations_content)
        
        return render_template(
            'recommendations.html',
            topic=topic,
            recommendations_content=recommendations_html
        )
    except Exception as e:
        flash(f'Error generating recommendations: {str(e)}')
        return redirect(url_for('generate_report', topic=topic))

@app.route('/paper_analysis', methods=['GET', 'POST'])
def paper_analysis():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            return redirect(url_for('analyze_paper', filename=filename))
        else:
            flash('File type not allowed. Please upload a PDF or DOCX file')
            return redirect(request.url)
    
    return render_template('paper_analysis.html')

@app.route('/analyze_paper/<filename>')
def analyze_paper(filename):
    try:
        if not components:
            flash('Research Assistant components not initialized properly')
            return redirect(url_for('index'))
        
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        # Debug information
        print(f"Processing file: {file_path}")
        print(f"Database path: {app.config['DATABASE_PATH']}")
        
        # Upload and process the file
        upload_result = upload_research_paper_file(file_path)
        
        if not upload_result.get("success", False):
            error_msg = upload_result.get("error", "Unknown error")
            flash(f'Error uploading file: {error_msg}')
            print(f"Upload error: {error_msg}")
            return redirect(url_for('paper_analysis'))
        
        paper_id = upload_result["paper_id"]
        print(f"Paper ID assigned: {paper_id}")
        
        # Process the paper
        result = process_research_paper(
            paper_id, 
            components["paper_summary_chain"], 
            components["paper_recommendation_chain"], 
            components["model"]
        )
        
        if not result.get("success", False):
            error_msg = result.get("error", "Unknown error")
            flash(f'Error: {error_msg}')
            print(f"Processing error: {error_msg}")
            return redirect(url_for('paper_analysis'))
        
        summary_content_html = parse_markdown_to_html(result.get("summary_content", ""))
        
        return render_template(
            'paper_summary.html',
            filename=filename,
            summary_content=summary_content_html,
            paper_id=paper_id
        )
    except Exception as e:
        error_msg = str(e)
        flash(f'Error analyzing paper: {error_msg}')
        print(f"Exception during analysis: {error_msg}")
        return redirect(url_for('paper_analysis'))

@app.route('/paper_recommendations/<int:paper_id>')
def paper_recommendations(paper_id):
    try:
        if not components:
            flash('Research Assistant components not initialized properly')
            return redirect(url_for('index'))
        
        from recommendation_papers import generate_paper_recommendations
        
        # Get paper from database
        paper_data = get_paper_from_database(paper_id, app.config['DATABASE_PATH'])
        if not paper_data:
            flash('Paper not found in database')
            return redirect(url_for('paper_analysis'))
        
        content = paper_data["content"]
        filename = paper_data["filename"]
        
        # Generate recommendations
        recommendations_content = generate_paper_recommendations(
            content,
            components["paper_recommendation_chain"],
            components["model"]
        )
        
        recommendations_html = parse_markdown_to_html(recommendations_content)
        
        return render_template(
            'paper_recommendations.html',
            filename=filename,
            recommendations_content=recommendations_html
        )
    except Exception as e:
        flash(f'Error generating paper recommendations: {str(e)}')
        return redirect(url_for('paper_analysis'))

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Add a new route to check the database content (for debugging)
@app.route('/debug/database')
def debug_database():
    import sqlite3
    try:
        conn = sqlite3.connect(app.config['DATABASE_PATH'])
        cursor = conn.cursor()
        cursor.execute("SELECT id, filename, file_type, upload_date FROM papers")
        papers = cursor.fetchall()
        conn.close()
        
        return render_template(
            'debug_database.html',
            papers=papers
        )
    except Exception as e:
        return f"Error accessing database: {str(e)}"
    
# Add new route before if __name__ == '__main__':
@app.route('/paper_qa', methods=['GET', 'POST'])
def paper_qa():
    if request.method == 'POST':
        # Handle file upload
        if 'file' in request.files:
            file = request.files['file']
            if file.filename == '':
                flash('No selected file')
                return redirect(url_for('paper_qa'))
            
            if file and allowed_file(file.filename):
                # Remove previous file if exists
                if 'uploaded_file' in session:
                    old_filename = session['uploaded_file']
                    old_filepath = os.path.join(app.config['UPLOAD_FOLDER'], old_filename)
                    try:
                        os.remove(old_filepath)
                    except Exception as e:
                        pass  # Handle error silently
                
                # Save new file
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                session['uploaded_file'] = filename
                flash('File uploaded successfully')
                return redirect(url_for('paper_qa'))
            else:
                flash('Allowed file types are PDF, DOCX')
                return redirect(url_for('paper_qa'))
        
        # Handle question submission
        elif 'question' in request.form:
            if 'uploaded_file' not in session:
                flash('Please upload a paper first')
                return redirect(url_for('paper_qa'))
            
            question = request.form['question'].strip()
            if not question:
                flash('Please enter a question')
                return redirect(url_for('paper_qa'))
            
            try:
                # Get uploaded file path
                filename = session['uploaded_file']
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                
                # Process document
                file_ext = os.path.splitext(filename)[1].lower()
                if file_ext == '.pdf':
                    text_content = extract_text_from_pdf(file_path)
                elif file_ext in ['.docx', '.doc']:
                    text_content = extract_text_from_docx(file_path)
                
                # Create RAG components
                text_chunks = split_text_into_chunks(text_content)
                embeddings = initialize_embeddings(os.getenv("GEMINI_API_KEY"))
                vector_store = create_vector_store(text_chunks, embeddings)
                rag_chain = create_rag_chain(vector_store, components["model"])
                
                # Generate answer
                answer = rag_chain.invoke(question)
                answer_html = parse_markdown_to_html(answer)
                
                return render_template('paper_qa.html', 
                                    answer=answer_html,
                                    filename=filename,
                                    question=question)
            
            except Exception as e:
                flash(f'Error processing question: {str(e)}')
                return redirect(url_for('paper_qa'))
    
    # Handle new paper request
    if request.method == 'GET' and request.args.get('new') == 'true':
        if 'uploaded_file' in session:
            old_filename = session.pop('uploaded_file')
            old_filepath = os.path.join(app.config['UPLOAD_FOLDER'], old_filename)
            try:
                os.remove(old_filepath)
            except Exception as e:
                pass
        return redirect(url_for('paper_qa'))

    # GET request - show upload form or QA interface
    filename = session.get('uploaded_file')
    return render_template('paper_qa.html', filename=filename)

if __name__ == '__main__':
    app.run(debug=True)