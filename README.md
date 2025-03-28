# Research Assistant Agent

An AI-powered tool designed to streamline academic research through automated content generation, paper summarization, and intelligent recommendations.

## Features

### 🚀 Automated Report Generation
- Transforms research topics into structured, detailed reports
- Generates comprehensive overviews with key insights

### 📄 Paper Summarization
- Converts complex research papers into concise summaries
- Extracts critical findings and methodologies

### 🔍 Smart Recommendations
- Suggests related topics and relevant research papers
- Provides verified source links for deeper exploration

### 💬 Interactive Paper Chat
- Enables dynamic Q&A with uploaded papers
- Delivers context-aware answers in real-time

## Technology Stack

- **Core Language**: Python
- **NLP Framework**: LangChain
- **AI API**: Gemini Pro
- **Web Interface**: Flask, HTML, CSS
- **Support Libraries**: NLTK, PyPDF2, python-dotenv

## Setup Instructions

1. Clone repository:
   ```bash
   git clone https://github.com/fahimai001/Research-Assistant-Agent.git
   cd Research-Assistant-Agent

2. Install dependencies:
    `pip install -r requirements.txt`

3. Set up environment variables:
    * Create .env file
    * Add your Gemini API key:
    `GEMINI_API_KEY=your_api_key_here`

4. Run the application:
    `python app.py`