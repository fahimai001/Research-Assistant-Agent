import os
import argparse
from typing import Dict, Any, List, Optional

from agent import (
    load_environment, 
    initialize_model, 
    create_chains, 
    research_topic, 
    display_results,
    create_prompt_templates
)
from output_schemas import define_output_schemas
from database import initialize_database
from document_processor import process_research_paper, upload_research_paper_file

def init_research_assistant():
    """Initialize the research assistant and return the necessary components"""
    print("Initializing Research Assistant...")
    
    # Load API key
    api_key = load_environment()
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in environment variables or .env file")
    
    # Initialize database
    print("- Initializing database...")
    initialize_database()
    
    # Initialize model
    print("- Initializing language model...")
    model = initialize_model(api_key)
    
    # Create prompt templates
    print("- Setting up prompt templates...")
    report_prompt, recommendation_prompt, paper_summary_prompt, paper_recommendation_prompt = create_prompt_templates()
    
    # Define output schemas
    print("- Defining output schemas...")
    TopicRecommendations, PaperRecommendations = define_output_schemas()
    
    # Create processing chains
    print("- Creating processing chains...")
    report_chain, recommendation_chain, paper_summary_chain, paper_recommendation_chain = create_chains(
        model, 
        report_prompt, 
        recommendation_prompt, 
        paper_summary_prompt, 
        paper_recommendation_prompt,
        TopicRecommendations,
        PaperRecommendations
    )
    
    print("Research Assistant initialized successfully!\n")
    
    return {
        "model": model,
        "report_chain": report_chain,
        "recommendation_chain": recommendation_chain,
        "paper_summary_chain": paper_summary_chain,
        "paper_recommendation_chain": paper_recommendation_chain
    }

def research_topic_command(topic: str, components: Dict[str, Any]):
    """Command to research a specific topic"""
    report_chain = components["report_chain"]
    recommendation_chain = components["recommendation_chain"]
    model = components["model"]
    
    result = research_topic(topic, report_chain, recommendation_chain, model)
    display_results(result, "report")
    
    return result

def process_paper_command(file_path: str, components: Dict[str, Any]):
    """Command to process a research paper"""
    paper_summary_chain = components["paper_summary_chain"]
    paper_recommendation_chain = components["paper_recommendation_chain"]
    model = components["model"]
    
    # Upload and process the file
    upload_result = upload_research_paper_file(file_path)
    if not upload_result["success"]:
        print(f"Error uploading file: {upload_result.get('error', 'Unknown error')}")
        return upload_result
    
    paper_id = upload_result["paper_id"]
    result = process_research_paper(paper_id, paper_summary_chain, paper_recommendation_chain, model)
    display_results(result, "paper_analysis")
    
    return result

def main():
    parser = argparse.ArgumentParser(description="AI Research Assistant")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Topic research command
    topic_parser = subparsers.add_parser("research", help="Research a topic")
    topic_parser.add_argument("topic", help="Topic to research")
    
    # Paper processing command
    paper_parser = subparsers.add_parser("analyze", help="Analyze a research paper")
    paper_parser.add_argument("file_path", help="Path to the PDF or DOCX file")
    
    args = parser.parse_args()
    
    try:
        # Initialize research assistant
        components = init_research_assistant()
        
        if args.command == "research":
            research_topic_command(args.topic, components)
        elif args.command == "analyze":
            process_paper_command(args.file_path, components)
        else:
            parser.print_help()
    
    except Exception as e:
        print(f"Error: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())