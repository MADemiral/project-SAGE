#!/usr/bin/env python3
"""
Selenium-based scraper for TED University course information.
Scrapes courses from https://cmpe.tedu.edu.tr/en/courses-offered
"""

import json
import time
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from typing import List, Dict, Optional
import re


def setup_driver():
    """Setup Chrome driver with headless options."""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver


def extract_course_code_from_url(url: str) -> Optional[str]:
    """Extract course code from URL."""
    match = re.search(r'/([A-Z]{3,4}\s*\d{3})', url.replace('%20', ' '))
    if match:
        return match.group(1).strip()
    return None


def scrape_course_detail(driver, course_url: str) -> Optional[Dict]:
    """Scrape detailed information from a course page."""
    try:
        print(f"  Scraping: {course_url}")
        driver.get(course_url)
        
        # Wait for page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        time.sleep(2)  # Additional wait for dynamic content
        
        course_data = {
            "url": course_url,
            "code": "",
            "name": "",
            "credits": "",
            "ects": "",
            "semester": "",
            "type": "",
            "prerequisite": "",
            "corequisite": "",
            "description": "",
            "objectives": "",
            "learning_outcomes": "",
            "syllabus": ""
        }
        
        # Try to extract course code from URL first
        course_data["code"] = extract_course_code_from_url(course_url) or ""
        
        # Extract course information from various elements
        try:
            # Look for course title/header
            title_elements = driver.find_elements(By.CSS_SELECTOR, "h1, h2, h3, .page-title, .course-title")
            for elem in title_elements:
                text = elem.text.strip()
                if text and len(text) > 0:
                    # Try to extract course code and name from title
                    match = re.match(r'([A-Z]{3,4}\s*\d{3})\s*[:-]?\s*(.*)', text)
                    if match:
                        course_data["code"] = match.group(1).strip()
                        course_data["name"] = match.group(2).strip()
                        break
                    elif not course_data["name"]:
                        course_data["name"] = text
        except Exception as e:
            print(f"    Warning: Could not extract title: {e}")
        
        # Extract all text content and parse sections
        try:
            page_text = driver.find_element(By.TAG_NAME, "body").text
            
            # Extract Credits
            credits_match = re.search(r'(?:Credits?|Kredi)\s*[:\-]?\s*(\d+)', page_text, re.IGNORECASE)
            if credits_match:
                course_data["credits"] = credits_match.group(1)
            
            # Extract ECTS
            ects_match = re.search(r'ECTS\s*[:\-]?\s*(\d+)', page_text, re.IGNORECASE)
            if ects_match:
                course_data["ects"] = ects_match.group(1)
            
            # Extract Semester
            semester_match = re.search(r'(?:Semester|Dönem)\s*[:\-]?\s*(\d+)', page_text, re.IGNORECASE)
            if semester_match:
                course_data["semester"] = semester_match.group(1)
            
            # Extract Type (Compulsory/Elective)
            if re.search(r'(?:Compulsory|Zorunlu)', page_text, re.IGNORECASE):
                course_data["type"] = "Compulsory"
            elif re.search(r'(?:Elective|Seçmeli)', page_text, re.IGNORECASE):
                course_data["type"] = "Elective"
            
            # Extract Prerequisites
            prereq_match = re.search(r'(?:Prerequisite|Önkoşul)\s*[:\-]?\s*([^\n]+)', page_text, re.IGNORECASE)
            if prereq_match:
                course_data["prerequisite"] = prereq_match.group(1).strip()
            
            # Extract Corequisites
            coreq_match = re.search(r'(?:Corequisite|Birlikte Alınacak)\s*[:\-]?\s*([^\n]+)', page_text, re.IGNORECASE)
            if coreq_match:
                course_data["corequisite"] = coreq_match.group(1).strip()
            
            # Extract Description
            desc_patterns = [
                r'(?:Course Description|Description|Açıklama)\s*[:\-]?\s*((?:.*?\n){1,5})',
                r'(?:Course Content|İçerik)\s*[:\-]?\s*((?:.*?\n){1,5})'
            ]
            for pattern in desc_patterns:
                desc_match = re.search(pattern, page_text, re.IGNORECASE | re.DOTALL)
                if desc_match:
                    course_data["description"] = desc_match.group(1).strip()
                    break
            
            # Extract Objectives
            obj_match = re.search(r'(?:Course Objectives?|Objectives?|Amaç)\s*[:\-]?\s*((?:.*?\n){1,10})', 
                                page_text, re.IGNORECASE | re.DOTALL)
            if obj_match:
                course_data["objectives"] = obj_match.group(1).strip()
            
            # Extract Learning Outcomes
            outcome_match = re.search(r'(?:Learning Outcomes?|Outcomes?|Kazanım)\s*[:\-]?\s*((?:.*?\n){1,10})', 
                                     page_text, re.IGNORECASE | re.DOTALL)
            if outcome_match:
                course_data["learning_outcomes"] = outcome_match.group(1).strip()
            
            # Extract Syllabus
            syllabus_patterns = [
                r'(?:Syllabus|Weekly Schedule|Haftalık Plan)\s*[:\-]?\s*((?:.*?\n){1,20})',
                r'(?:Course Outline|İçerik Planı)\s*[:\-]?\s*((?:.*?\n){1,20})'
            ]
            for pattern in syllabus_patterns:
                syllabus_match = re.search(pattern, page_text, re.IGNORECASE | re.DOTALL)
                if syllabus_match:
                    course_data["syllabus"] = syllabus_match.group(1).strip()
                    break
                    
        except Exception as e:
            print(f"    Warning: Error extracting text content: {e}")
        
        # Try to find table data
        try:
            tables = driver.find_elements(By.TAG_NAME, "table")
            for table in tables:
                rows = table.find_elements(By.TAG_NAME, "tr")
                for row in rows:
                    cells = row.find_elements(By.TAG_NAME, "td")
                    if len(cells) >= 2:
                        key = cells[0].text.strip().lower()
                        value = cells[1].text.strip()
                        
                        if 'credit' in key and not course_data["credits"]:
                            course_data["credits"] = value
                        elif 'ects' in key and not course_data["ects"]:
                            course_data["ects"] = value
                        elif 'semester' in key and not course_data["semester"]:
                            course_data["semester"] = value
                        elif 'prerequisite' in key and not course_data["prerequisite"]:
                            course_data["prerequisite"] = value
        except Exception as e:
            print(f"    Warning: Could not extract table data: {e}")
        
        # If we still don't have a course code, try URL parsing again
        if not course_data["code"]:
            course_data["code"] = extract_course_code_from_url(course_url) or "UNKNOWN"
        
        print(f"    ✓ Scraped: {course_data['code']} - {course_data['name']}")
        return course_data
        
    except Exception as e:
        print(f"    ✗ Error scraping {course_url}: {e}")
        return None


def scrape_all_courses(base_url: str = "https://cmpe.tedu.edu.tr/en/courses-offered") -> List[Dict]:
    """Scrape all courses from the main page."""
    driver = None
    all_courses = []
    
    try:
        print("Setting up Chrome driver...")
        driver = setup_driver()
        
        print(f"\nNavigating to: {base_url}")
        driver.get(base_url)
        
        # Wait for page to load
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        time.sleep(3)  # Additional wait for JavaScript content
        
        print("Searching for course links...")
        
        # Find all links that might be courses
        all_links = driver.find_elements(By.TAG_NAME, "a")
        course_urls = set()
        
        for link in all_links:
            try:
                href = link.get_attribute("href")
                if href and "course" in href.lower():
                    # Look for course code pattern in URL or link text
                    link_text = link.text.strip()
                    if (re.search(r'[A-Z]{3,4}\s*\d{3}', href) or 
                        re.search(r'[A-Z]{3,4}\s*\d{3}', link_text)):
                        course_urls.add(href)
            except:
                continue
        
        # Also try to find course links by looking for specific patterns in the page
        try:
            # Look for divs or sections that might contain course listings
            course_containers = driver.find_elements(By.CSS_SELECTOR, 
                ".course-list, .course-item, .course, [class*='course'], [class*='ders']")
            
            for container in course_containers:
                links = container.find_elements(By.TAG_NAME, "a")
                for link in links:
                    try:
                        href = link.get_attribute("href")
                        if href:
                            course_urls.add(href)
                    except:
                        continue
        except:
            pass
        
        print(f"Found {len(course_urls)} potential course links")
        
        if len(course_urls) == 0:
            print("\n⚠️  No course links found. Saving page source for debugging...")
            with open("/app/data/page_source.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            print("Page source saved to /app/data/page_source.html")
        
        # Scrape each course
        for idx, course_url in enumerate(sorted(course_urls), 1):
            print(f"\n[{idx}/{len(course_urls)}] Processing course...")
            course_data = scrape_course_detail(driver, course_url)
            
            if course_data:
                all_courses.append(course_data)
            
            # Small delay between requests
            time.sleep(1)
        
        print(f"\n✓ Successfully scraped {len(all_courses)} courses")
        return all_courses
        
    except Exception as e:
        print(f"\n✗ Error during scraping: {e}")
        import traceback
        traceback.print_exc()
        return all_courses
        
    finally:
        if driver:
            print("\nClosing browser...")
            driver.quit()


def main():
    """Main function."""
    output_file = "/app/data/tedu_courses.json"
    
    print("="*60)
    print("TED University Course Scraper (Selenium)")
    print("="*60)
    
    # Scrape courses
    courses = scrape_all_courses()
    
    # Save to JSON
    print(f"\nSaving {len(courses)} courses to {output_file}...")
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(courses, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Saved to {output_file}")
    
    # Print summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Total courses scraped: {len(courses)}")
    if courses:
        print(f"\nSample course:")
        print(f"  Code: {courses[0].get('code', 'N/A')}")
        print(f"  Name: {courses[0].get('name', 'N/A')}")
        print(f"  Credits: {courses[0].get('credits', 'N/A')}")
        print(f"  ECTS: {courses[0].get('ects', 'N/A')}")
    print("="*60)


if __name__ == "__main__":
    main()
