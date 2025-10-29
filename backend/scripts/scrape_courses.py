"""
Web scraper for TED University Computer Engineering course curriculum
Extracts course data for RAG implementation
"""

import requests
from bs4 import BeautifulSoup
import json
import re
import time
from typing import List, Dict
from urllib.parse import urljoin, urlparse


def scrape_tedu_courses(url: str = "https://cmpe.tedu.edu.tr/ogretim-programi") -> List[Dict]:
    """
    Scrape course information from TED University CMPE curriculum page
    Finds all course links and scrapes detailed information from each
    
    Returns:
        List of course dictionaries with metadata
    """
    print(f"Scraping main page: {url}")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
    except Exception as e:
        print(f"Error fetching main page: {e}")
        return []
    
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Find all links that might be course pages
    course_links = set()
    
    # Look for links containing course codes (e.g., CMPE, MATH, PHYS)
    all_links = soup.find_all('a', href=True)
    
    for link in all_links:
        href = link.get('href')
        text = link.get_text(strip=True)
        
        # Check if link text contains course code pattern (e.g., "CMPE 101", "MATH 101")
        if re.search(r'[A-Z]{3,4}\s*\d{3}', text):
            full_url = urljoin(url, href)
            # Only include links from the same domain
            if 'tedu.edu.tr' in urlparse(full_url).netloc:
                course_links.add(full_url)
                print(f"Found course link: {text} -> {full_url}")
    
    print(f"\nFound {len(course_links)} course page links")
    
    # Scrape each course page
    courses = []
    for i, course_url in enumerate(course_links, 1):
        print(f"\nScraping course {i}/{len(course_links)}: {course_url}")
        try:
            course_data = scrape_course_detail(course_url, headers)
            if course_data:
                courses.append(course_data)
            time.sleep(0.5)  # Be polite, don't overwhelm the server
        except Exception as e:
            print(f"Error scraping {course_url}: {e}")
            continue
    
    print(f"\nSuccessfully scraped {len(courses)} courses")
    return courses


def scrape_course_detail(course_url: str, headers: dict) -> Dict:
    """
    Scrape detailed information for a specific course
    
    Args:
        course_url: URL of the course detail page
        headers: HTTP headers for the request
        
    Returns:
        Dictionary with course information
    """
    try:
        response = requests.get(course_url, headers=headers, timeout=10)
        response.raise_for_status()
    except Exception as e:
        print(f"  Error fetching course page: {e}")
        return None
    
    soup = BeautifulSoup(response.content, 'html.parser')
    
    course_data = {
        'code': '',
        'name': '',
        'credits': '',
        'ects': '',
        'semester': '',
        'type': '',
        'description': '',
        'prerequisites': '',
        'objectives': '',
        'outcomes': '',
        'syllabus': '',
        'instructor': '',
        'url': course_url
    }
    
    # Extract course code and name from page title or heading
    title = soup.find('h1') or soup.find('h2') or soup.find('title')
    if title:
        title_text = title.get_text(strip=True)
        # Try to extract code and name (e.g., "CMPE 101 - Introduction to Computer Engineering")
        match = re.search(r'([A-Z]{3,4}\s*\d{3})\s*[-:]\s*(.+)', title_text)
        if match:
            course_data['code'] = match.group(1).strip()
            course_data['name'] = match.group(2).strip()
        else:
            # Try just the code
            code_match = re.search(r'[A-Z]{3,4}\s*\d{3}', title_text)
            if code_match:
                course_data['code'] = code_match.group(0).strip()
                course_data['name'] = title_text.replace(course_data['code'], '').strip(' -:')
    
    # Extract all text content and look for specific sections
    page_text = soup.get_text()
    
    # Look for description (Açıklama, Description, Course Description)
    desc_match = re.search(r'(?:Course\s+)?Description[:\s]+(.+?)(?:\n\n|\r\n\r\n|Prerequisites|Objectives)', page_text, re.IGNORECASE | re.DOTALL)
    if not desc_match:
        desc_match = re.search(r'Açıklama[:\s]+(.+?)(?:\n\n|\r\n\r\n|Önkoşul|Hedef)', page_text, re.IGNORECASE | re.DOTALL)
    if desc_match:
        course_data['description'] = desc_match.group(1).strip()[:1000]  # Limit to 1000 chars
    
    # Look for prerequisites (Önkoşullar, Prerequisites)
    prereq_match = re.search(r'(?:Prerequisites?|Önkoşullar?)[:\s]+(.+?)(?:\n\n|\r\n\r\n|Course\s+Objectives)', page_text, re.IGNORECASE | re.DOTALL)
    if prereq_match:
        course_data['prerequisites'] = prereq_match.group(1).strip()[:500]
    
    # Look for objectives (Hedefler, Objectives, Course Objectives)
    obj_match = re.search(r'(?:Course\s+)?Objectives?[:\s]+(.+?)(?:\n\n|\r\n\r\n|Learning\s+Outcomes|Syllabus)', page_text, re.IGNORECASE | re.DOTALL)
    if not obj_match:
        obj_match = re.search(r'Hedefler[:\s]+(.+?)(?:\n\n|\r\n\r\n|Kazanım|İçerik)', page_text, re.IGNORECASE | re.DOTALL)
    if obj_match:
        course_data['objectives'] = obj_match.group(1).strip()[:1000]
    
    # Look for learning outcomes (Kazanımlar, Learning Outcomes)
    outcome_match = re.search(r'(?:Learning\s+)?Outcomes?[:\s]+(.+?)(?:\n\n|\r\n\r\n|Syllabus|Course\s+Content)', page_text, re.IGNORECASE | re.DOTALL)
    if not outcome_match:
        outcome_match = re.search(r'Kazanımlar[:\s]+(.+?)(?:\n\n|\r\n\r\n|İçerik)', page_text, re.IGNORECASE | re.DOTALL)
    if outcome_match:
        course_data['outcomes'] = outcome_match.group(1).strip()[:1000]
    
    # Look for syllabus/content (İçerik, Syllabus, Course Content)
    syllabus_match = re.search(r'(?:Course\s+)?(?:Content|Syllabus)[:\s]+(.+?)(?:\n\n\n|\r\n\r\n\r\n|Textbook|References)', page_text, re.IGNORECASE | re.DOTALL)
    if not syllabus_match:
        syllabus_match = re.search(r'İçerik[:\s]+(.+?)(?:\n\n\n|\r\n\r\n\r\n|Kaynaklar)', page_text, re.IGNORECASE | re.DOTALL)
    if syllabus_match:
        course_data['syllabus'] = syllabus_match.group(1).strip()[:2000]
    
    # Look for credits/ECTS in structured data or tables
    tables = soup.find_all('table')
    for table in tables:
        table_text = table.get_text()
        credit_match = re.search(r'(?:Kredi|Credit)[:\s]+(\d+)', table_text, re.IGNORECASE)
        if credit_match:
            course_data['credits'] = credit_match.group(1)
        ects_match = re.search(r'ECTS[:\s]+(\d+)', table_text, re.IGNORECASE)
        if ects_match:
            course_data['ects'] = ects_match.group(1)
    
    # If we couldn't extract code or name, return None
    if not course_data['code']:
        print(f"  Could not extract course code from page")
        return None
    
    print(f"  ✓ Scraped: {course_data['code']} - {course_data['name']}")
    return course_data


def scrape_course_details(course_url: str) -> Dict:
    """
    Scrape detailed information for a specific course
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    response = requests.get(course_url, headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    details = {
        'description': '',
        'prerequisites': [],
        'objectives': [],
        'outcomes': [],
        'syllabus': ''
    }
    
    # Extract course description
    desc = soup.find('div', class_=re.compile(r'description|aciklama'))
    if desc:
        details['description'] = desc.get_text(strip=True)
    
    return details


def save_courses_to_json(courses: List[Dict], filename: str = 'tedu_courses.json'):
    """Save scraped courses to JSON file"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(courses, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(courses)} courses to {filename}")


if __name__ == "__main__":
    # Scrape courses
    courses = scrape_tedu_courses()
    
    # Save to JSON
    save_courses_to_json(courses, '/app/data/tedu_courses.json')
    
    # Print sample
    if courses:
        print("\nSample course:")
        print(json.dumps(courses[0], ensure_ascii=False, indent=2))
