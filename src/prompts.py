# from langchain_core.prompts import ChatPromptTemplate

# def create_prompt_templates():
#     """Create prompt templates for research tasks"""
#     report_prompt = ChatPromptTemplate.from_template(
#         """
#         You are an AI research assistant. Create a comprehensive, detailed report on the following topic:
        
#         Topic: {topic}
        
#         Your report should include:
#         1. Introduction to the topic
#         2. Key concepts and definitions
#         3. Historical context and development
#         4. Current state and applications
#         5. Future directions and potential developments
#         6. Conclusion
        
#         Format your report with clear markdown headings and subheadings. Use proper markdown formatting for emphasis, lists, and other elements.
#         Make sure to provide in-depth analysis.
#         """
#     )

#     recommendation_prompt = ChatPromptTemplate.from_template(
#         """
#         Based on the topic: {topic}
        
#         Generate 5 relevant related topics that the user might be interested in researching next.
#         For each recommendation, provide:
#         1. The topic name
#         2. A brief 1-2 sentence description of why it's relevant
#         3. A relevant resource URL that would contain valuable information about this topic
        
#         Your response must be formatted as a valid JSON object that matches this structure:
#         {
#             "recommendations": [
#                 {
#                     "topic": "Topic Name",
#                     "description": "Brief description of relevance",
#                     "resource_url": "https://example.com/relevant-page"
#                 },
#                 ...
#             ]
#         }
        
#         Use reputable sources for your resource URLs. While you can't verify if the exact URLs exist,
#         make them realistic and likely to contain quality information.
#         """
#     )

#     paper_summary_prompt = ChatPromptTemplate.from_template(
#         """
#         You are an AI research assistant. Create a concise but comprehensive summary of the following research paper:
        
#         Paper content: {paper_content}
        
#         Your summary should include:
#         1. **Main Objective:** What the paper aims to achieve.
#         2. **Methodology:** Detailed explanation of the methods and techniques used.
#         3. **Key Findings and Results:** The primary outcomes of the research.
#         4. **Conclusions and Implications:** The broader impact and significance of the work.
#         5. **Limitations:** Any constraints or limitations mentioned.
#         6. **Novel Contributions:** Highlight any unique or innovative aspects.
#         7. **Future Directions:** Suggestions for future research or applications derived from the paper.
#         8. **Critical Evaluation:** A brief note on the strengths and weaknesses of the research.
        
#         Format your summary with clear markdown headings for each section. Ensure that your summary is detailed enough to give a thorough understanding of the paper, yet concise and focused on the most important aspects.
#     """
#     )

#     paper_recommendation_prompt = ChatPromptTemplate.from_template(
#     """
#     Based on the following research paper:
    
#     Paper content: {paper_content}
    
#     Generate 5 relevant related research papers that the user might be interested in reading next.
#     These should be real papers that likely exist in the academic literature.
    
#     For each recommendation, provide:
#     1. The paper title (use the actual title of a real paper if you know it)
#     2. The authors (use "et al." for multiple authors after the first)
#     3. Publication year (estimate if necessary)
#     4. A brief description of why it's relevant to the original paper
#     5. A URL where the paper might be found - THIS IS CRITICAL. 
    
#     For URLs, use specific links from:
#     - Google Scholar (https://scholar.google.com/scholar?q=PAPER_TITLE)
#     - arXiv (https://arxiv.org/search/?query=PAPER_TITLE)
#     - ResearchGate (https://www.researchgate.net/search.Search.html?query=PAPER_TITLE)
#     - ACM Digital Library (https://dl.acm.org/action/doSearch?AllField=PAPER_TITLE)
#     - IEEE Xplore (https://ieeexplore.ieee.org/search/searchresult.jsp?queryText=PAPER_TITLE)
    
#     Replace PAPER_TITLE with URL-encoded paper title in these templates. Make sure EVERY recommendation has a working URL.
    
#     Your response must be formatted as a valid JSON object that matches this structure:
#     {{
#         "recommendations": [
#             {{
#                 "title": "Paper Title",
#                 "authors": "Author names",
#                 "year": "Publication year",
#                 "description": "Brief description of relevance",
#                 "paper_url": "https://example.com/paper-link"
#             }},
#             ...
#         ]
#     }}
#     """
# )
    
#     return report_prompt, recommendation_prompt, paper_summary_prompt, paper_recommendation_prompt