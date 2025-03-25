import urllib.parse
import requests
import re
import random
import time
from bs4 import BeautifulSoup
from typing import List, Dict, Any

def search_web(query, num_results=5):
    """Search the web for related topics with improved reliability"""
    try:
        # Format query for search engines
        search_query = urllib.parse.quote_plus(query)
        
        # List of search URLs to try (with more reliable options)
        search_urls = [
            f"https://www.google.com/search?q={search_query}",
            f"https://en.wikipedia.org/wiki/Special:Search?search={search_query}&go=Go",
            f"https://scholar.google.com/scholar?q={search_query}",
            f"https://www.semanticscholar.org/search?q={search_query}",
            f"https://core.ac.uk/search?q={search_query}"
        ]
        
        # Randomize a bit to avoid predictable patterns
        if random.random() < 0.5:
            search_urls[0], search_urls[1] = search_urls[1], search_urls[0]
        
        results = []
        
        # Set user agent to avoid being blocked (rotate between options)
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0'
        ]
        
        headers = {
            'User-Agent': random.choice(user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
        }
        
        # Try each search engine until we get enough results
        for search_url in search_urls:
            if len(results) >= num_results:
                break
                
            try:
                # Add a small random delay before request
                time.sleep(random.uniform(0.5, 1.5))
                
                response = requests.get(search_url, headers=headers, timeout=15)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Extract links and titles (implementation varies by search engine)
                    if 'google.com/search' in search_url:
                        # For Google
                        search_results = soup.select('div.g')
                        for result in search_results:
                            title_element = result.select_one('h3')
                            link_element = result.select_one('a')
                            
                            if title_element and link_element and 'href' in link_element.attrs:
                                title = title_element.get_text()
                                link = link_element['href']
                                
                                # Remove Google redirects
                                if link.startswith('/url?q='):
                                    link = link.split('/url?q=')[1].split('&')[0]
                                
                                if link.startswith('http') and not any(x['url'] == link for x in results):
                                    # Filter out some common problematic links
                                    if not any(x in link.lower() for x in ['youtube.com', 'facebook.com', 'twitter.com']):
                                        results.append({
                                            'title': title,
                                            'url': link
                                        })
                                    
                                if len(results) >= num_results:
                                    break
                    
                    elif 'wikipedia.org' in search_url:
                        # For Wikipedia
                        search_results = soup.select('ul.mw-search-results li')
                        for result in search_results:
                            title_element = result.select_one('a')
                            if title_element and 'href' in title_element.attrs:
                                title = title_element.get_text()
                                link = 'https://en.wikipedia.org' + title_element['href']
                                
                                if not any(x['url'] == link for x in results):
                                    results.append({
                                        'title': title,
                                        'url': link
                                    })
                                    
                                if len(results) >= num_results:
                                    break
                    
                    elif 'scholar.google.com' in search_url:
                        # For Google Scholar
                        search_results = soup.select('.gs_ri')
                        for result in search_results:
                            title_element = result.select_one('.gs_rt a')
                            if title_element and 'href' in title_element.attrs:
                                title = title_element.get_text()
                                link = title_element['href']
                                
                                if not link.startswith('http'):
                                    link = 'https://scholar.google.com' + link
                                
                                if not any(x['url'] == link for x in results):
                                    results.append({
                                        'title': title,
                                        'url': link
                                    })
                                    
                                if len(results) >= num_results:
                                    break
                                    
                    elif 'semanticscholar.org' in search_url:
                        # For Semantic Scholar
                        search_results = soup.select('.result-page .result-card')
                        for result in search_results:
                            title_element = result.select_one('.cl-paper-title')
                            link_element = result.select_one('a.flex-1')
                            
                            if title_element and link_element and 'href' in link_element.attrs:
                                title = title_element.get_text()
                                link = 'https://www.semanticscholar.org' + link_element['href']
                                
                                if not any(x['url'] == link for x in results):
                                    results.append({
                                        'title': title,
                                        'url': link
                                    })
                                    
                                if len(results) >= num_results:
                                    break
                                    
                    elif 'core.ac.uk' in search_url:
                        # For CORE.ac.uk
                        search_results = soup.select('.search-result')
                        for result in search_results:
                            title_element = result.select_one('.title a')
                            
                            if title_element and 'href' in title_element.attrs:
                                title = title_element.get_text()
                                link = 'https://core.ac.uk' + title_element['href']
                                
                                if not any(x['url'] == link for x in results):
                                    results.append({
                                        'title': title,
                                        'url': link
                                    })
                                    
                                if len(results) >= num_results:
                                    break
            
            except Exception as e:
                print(f"Error searching {search_url}: {str(e)}")
                continue
        
        # If we still don't have enough results, create fallback search links
        if len(results) < num_results:
            needed = num_results - len(results)
            
            # Create direct links to reliable sources
            fallback_urls = [
                f"https://en.wikipedia.org/wiki/{urllib.parse.quote(query.replace(' ', '_'))}",
                f"https://scholar.google.com/scholar?q={search_query}",
                f"https://www.semanticscholar.org/search?q={search_query}",
                f"https://arxiv.org/search/?query={search_query}&searchtype=all"
            ]
            
            for url in fallback_urls[:needed]:
                title = f"Resources about {query}"
                results.append({
                    'title': title,
                    'url': url
                })
        
        return results
    
    except Exception as e:
        print(f"Web search error: {str(e)}")
        # Create minimal fallback results that will always work
        return [
            {
                'title': f"Search results for {query}",
                'url': f"https://en.wikipedia.org/wiki/Special:Search?search={urllib.parse.quote_plus(query)}"
            },
            {
                'title': f"Academic papers on {query}",
                'url': f"https://scholar.google.com/scholar?q={urllib.parse.quote_plus(query)}"
            }
        ]