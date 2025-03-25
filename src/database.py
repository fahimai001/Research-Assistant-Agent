import os
import sqlite3
from typing import Dict, Optional

def initialize_database(db_path: str = None):
    if db_path is None:
        db_path = os.environ.get('DATABASE_PATH', "../data/research_papers.db")
    
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    print(f"Initializing database at: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS papers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            content TEXT NOT NULL,
            file_type TEXT NOT NULL,
            upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            summary TEXT
        )
    ''')
    conn.commit()
    conn.close()

def save_file_to_database(filename: str, content: str, file_type: str, db_path: str = None):
    if db_path is None:
        db_path = os.environ.get('DATABASE_PATH', "../data/research_papers.db")
    
    print(f"Saving file to database: {filename} at {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO papers (filename, content, file_type) VALUES (?, ?, ?)",
        (filename, content, file_type)
    )
    paper_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    print(f"File saved with ID: {paper_id}")
    
    return paper_id

def save_summary_to_database(paper_id: int, summary: str, db_path: str = None):
    if db_path is None:
        db_path = os.environ.get('DATABASE_PATH', "../data/research_papers.db")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE papers SET summary = ? WHERE id = ?",
        (summary, paper_id)
    )
    conn.commit()
    conn.close()

def get_paper_from_database(paper_id: int, db_path: str = None):
    if db_path is None:
        db_path = os.environ.get('DATABASE_PATH', "../data/research_papers.db")
    
    print(f"Getting paper ID {paper_id} from database at {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT filename, content, file_type, summary FROM papers WHERE id = ?", (paper_id,))
    result = cursor.fetchone()
    conn.close()
    
    if result:
        print(f"Found paper: {result[0]}")
        
        return {
            "filename": result[0],
            "content": result[1],
            "file_type": result[2],
            "summary": result[3]
        }
    else:
        print(f"Paper ID {paper_id} not found in database")
        return None