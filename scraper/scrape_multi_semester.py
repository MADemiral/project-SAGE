#!/usr/bin/env python3
"""
Multi-semester course scraper for TED University
Scrapes courses from the last 6 semesters
"""

import json
import time
import re
from typing import Dict, Optional, List
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import Select
from webdriver_manager.chrome import ChromeDriverManager

# Semesters to scrape
SEMESTERS = [
    "Fall 2025",
    "Spring 2025"
]

DEPARTMENTS = {
    "cmpe": {
        "url": "https://cmpe.tedu.edu.tr/en/courses-offered",
        "output": "tedu_cmpe_courses.json",
        "name": "Computer Engineering"
    },
    "seng": {
        "url": "https://seng.tedu.edu.tr/en/courses-offered",
        "output": "tedu_seng_courses.json",
        "name": "Software Engineering"
    },
    "me": {
        "url": "https://me.tedu.edu.tr/en/courses-offered",
        "output": "tedu_me_courses.json",
        "name": "Mechanical Engineering"
    },
    "ee": {
        "url": "https://ee.tedu.edu.tr/en/courses-offered",
        "output": "tedu_ee_courses.json",
        "name": "Electrical and Electronics Engineering"
    }
}

def scrape_syllabus_detail(driver, syllabus_url: str):
    """Scrape detailed course information from syllabus page."""
    try:
        driver.get(syllabus_url)
        time.sleep(0.2)
        
        detail_info = {
            "course_code": "",
            "course_title": "",
            "level": "",
            "credit_hours": "",
            "academic_year": "",
            "catalog_description": "",
            "prerequisites": [],
            "corequisites": [],
            "instructor": "",
            "learning_outcomes": "",
            "assessment_methods": "",
            "textbooks": ""
        }
        
        page_text = driver.find_element(By.TAG_NAME, "body").text
        
        # Extract information using regex
        code_match = re.search(r'Course Code & Number:\s*([^\n]+)', page_text, re.IGNORECASE)
        if code_match:
            detail_info["course_code"] = code_match.group(1).strip()
        
        title_match = re.search(r'Course Title:\s*([^\n]+)', page_text, re.IGNORECASE)
        if title_match:
            detail_info["course_title"] = title_match.group(1).strip()
        
        level_match = re.search(r'Level:\s*([^\n]+)', page_text, re.IGNORECASE)
        if level_match:
            detail_info["level"] = level_match.group(1).strip()
        
        credit_match = re.search(r'Credit Hours/ ECTS Credits:\s*([^\n]+)', page_text, re.IGNORECASE)
        if credit_match:
            detail_info["credit_hours"] = credit_match.group(1).strip()
        
        year_match = re.search(r'Academic Year\s*([^\n]+)', page_text, re.IGNORECASE)
        if year_match:
            detail_info["academic_year"] = year_match.group(1).strip()
        
        desc_match = re.search(r'Catalog Description:\s*([^\n]+(?:\n(?!Pre-requisite|Learning Outcomes)[^\n]+)*)', page_text, re.IGNORECASE)
        if desc_match:
            detail_info["catalog_description"] = desc_match.group(1).strip()
        
        prereq_match = re.search(r'Pre-requisites?:\s*([^\n]+)', page_text, re.IGNORECASE)
        if prereq_match:
            prereq_text = prereq_match.group(1).strip()
            if prereq_text.upper() == "NONE":
                detail_info["prerequisites"] = []
            else:
                detail_info["prerequisites"] = [p.strip() for p in re.split(r'\s+OR\s+', prereq_text, flags=re.IGNORECASE)]
        
        coreq_match = re.search(r'Co-requisites?:\s*([^\n]+)', page_text, re.IGNORECASE)
        if coreq_match:
            coreq_text = coreq_match.group(1).strip()
            if coreq_text.upper() == "NONE":
                detail_info["corequisites"] = []
            else:
                detail_info["corequisites"] = [c.strip() for c in re.split(r'\s+OR\s+', coreq_text, flags=re.IGNORECASE)]
        
        instructor_match = re.search(r'Instructor:\s*([^\n]+)', page_text, re.IGNORECASE)
        if instructor_match:
            detail_info["instructor"] = instructor_match.group(1).strip()
        
        outcomes_match = re.search(r'Learning Outcomes:\s*Upon succesful completion.*?(?=Learning Activities|Assessment Methods|Textbook|$)', page_text, re.IGNORECASE | re.DOTALL)
        if outcomes_match:
            detail_info["learning_outcomes"] = outcomes_match.group(0).strip()[:1000]
        
        assessment_match = re.search(r'Assessment Methods and Criteria:\s*(.*?)(?=Textbook|Weekly Schedule|$)', page_text, re.IGNORECASE | re.DOTALL)
        if assessment_match:
            detail_info["assessment_methods"] = assessment_match.group(1).strip()[:500]
        
        textbook_match = re.search(r'(?:Textbooks?|Required Textbooks?):\s*(.*?)(?=Weekly Schedule|Assessment|$)', page_text, re.IGNORECASE | re.DOTALL)
        if textbook_match:
            detail_info["textbooks"] = textbook_match.group(1).strip()[:500]
        
        return detail_info
        
    except Exception as e:
        print(f"      ✗ Error: {e}")
        return {}

def scrape_semester(driver, semester_name, dept_url):
    """Scrape courses for a specific semester"""
    print(f"\n{'='*60}")
    print(f"SCRAPING: {semester_name}")
    print(f"{'='*60}")
    
    try:
        # Navigate back to main page to ensure fresh state
        driver.get(dept_url)
        time.sleep(0.5)
        
        # Find semester dropdown
        semester_select = driver.find_element(By.CSS_SELECTOR, "select")
        select_obj = Select(semester_select)
        
        # Select the semester
        print(f"Selecting '{semester_name}'...")
        select_obj.select_by_visible_text(semester_name)
        time.sleep(0.5)  # Wait for content to load
        
        # Parse courses from the text content
        body_text = driver.find_element(By.TAG_NAME, "body").text
        course_blocks = body_text.split("Code:")[1:]
        
        print(f"Found {len(course_blocks)} course section entries")
        
        # Dictionary to store unique courses
        unique_courses = {}
        
        # Find all syllabus links
        syllabus_links_elements = driver.find_elements(By.PARTIAL_LINK_TEXT, "View Syllabus")
        syllabus_links = [link.get_attribute("href") for link in syllabus_links_elements if link.get_attribute("href")]
        
        print(f"Found {len(syllabus_links)} syllabus links")
        
        # Parse each course block
        for idx, block in enumerate(course_blocks):
            lines = block.strip().split('\n')
            if len(lines) < 2:
                continue
            
            first_line = lines[0].strip()
            
            # Pattern: CMPE 113_01 - Course Name, (2+0+2) 3 Credits / 5 ECTS
            match = re.match(r'([A-Z]+\s*\d+)(?:_|\-)([A-Z0-9_]+)?\s*-\s*([^,]+),\s*\(([^)]+)\)\s*(\d+)\s*Credits\s*/\s*(\d+)\s*ECTS', first_line)
            
            if match:
                base_code = match.group(1).strip()
                section_num = match.group(2) if match.group(2) else "01"
                name = match.group(3).strip()
                hours = match.group(4)
                credits = match.group(5)
                ects = match.group(6)
                
                # Extract instructor
                staff = ""
                for line in lines[1:]:
                    if not line.startswith("Staff:") and not line.startswith("Syllabus:") and line.strip() and not line.startswith("View Syllabus"):
                        if not staff:
                            staff = line.strip()
                
                # Create or update course entry
                if base_code not in unique_courses:
                    syllabus_url = syllabus_links[idx] if idx < len(syllabus_links) else ""
                    
                    # Fetch detailed syllabus information
                    print(f"    [{len(unique_courses)+1}] {base_code} - {name}")
                    syllabus_details = {}
                    if syllabus_url:
                        print(f"      Fetching syllabus details...")
                        syllabus_details = scrape_syllabus_detail(driver, syllabus_url)
                        print(f"      ✓ Details extracted")
                    
                    unique_courses[base_code] = {
                        "code": base_code,
                        "name": name,
                        "hours": hours,
                        "credits": credits,
                        "ects": ects,
                        "semester": semester_name,
                        "sections": [section_num],
                        "instructors": [staff] if staff else [],
                        "syllabus_url": syllabus_url,
                        **syllabus_details  # Merge all syllabus details into the course object
                    }
                else:
                    # Add section and instructor
                    if section_num not in unique_courses[base_code]["sections"]:
                        unique_courses[base_code]["sections"].append(section_num)
                    if staff and staff not in unique_courses[base_code]["instructors"]:
                        unique_courses[base_code]["instructors"].append(staff)
        
        print(f"✓ Found {len(unique_courses)} unique courses in {semester_name}")
        return list(unique_courses.values())
        
    except Exception as e:
        print(f"✗ Error scraping {semester_name}: {str(e)}")
        return []

def scrape_department(dept_key):
    """Scrape all semesters for a department"""
    dept = DEPARTMENTS[dept_key]
    
    print(f"\n{'='*70}")
    print(f"DEPARTMENT: {dept['name']}")
    print(f"URL: {dept['url']}")
    print(f"{'='*70}")
    
    # Setup Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    # Initialize driver
    driver = webdriver.Chrome(options=chrome_options)
    driver.get(dept['url'])
    time.sleep(0.5)
    
    all_courses = []
    unique_courses_dict = {}  # Track unique courses across semesters
    
    try:
        # Navigate to the page
        driver.get(dept['url'])
        time.sleep(0.5)
        
        # Scrape each semester
        for semester in SEMESTERS:
            courses = scrape_semester(driver, semester, dept['url'])
            for course in courses:
                course["department"] = dept_key.upper()
                
                # Track unique courses
                course_code = course['code']
                if course_code not in unique_courses_dict:
                    # First time seeing this course - save full details
                    unique_courses_dict[course_code] = {
                        **course,
                        "offered_semesters": [semester],
                        "semester_data": {
                            semester: {
                                "sections": course['sections'],
                                "instructors": course['instructors']
                            }
                        }
                    }
                    # Remove the single semester field
                    del unique_courses_dict[course_code]["semester"]
                else:
                    # Course exists - just add semester info
                    if semester not in unique_courses_dict[course_code]["offered_semesters"]:
                        unique_courses_dict[course_code]["offered_semesters"].append(semester)
                    unique_courses_dict[course_code]["semester_data"][semester] = {
                        "sections": course['sections'],
                        "instructors": course['instructors']
                    }
                
            all_courses.extend(courses)
        
        # Save raw data (all courses with semesters)
        raw_output = dept['output'].replace('.json', '_raw.json')
        with open(raw_output, 'w', encoding='utf-8') as f:
            json.dump(all_courses, f, indent=2, ensure_ascii=False)
        
        # Save metadata (unique courses with semester history)
        metadata_output = dept['output'].replace('.json', '_metadata.json')
        unique_courses_list = list(unique_courses_dict.values())
        with open(metadata_output, 'w', encoding='utf-8') as f:
            json.dump(unique_courses_list, f, indent=2, ensure_ascii=False)
        
        # Also save to data directory for Docker access
        import os
        data_dir = "../data"
        if os.path.exists(data_dir):
            data_metadata = os.path.join(data_dir, metadata_output)
            with open(data_metadata, 'w', encoding='utf-8') as f:
                json.dump(unique_courses_list, f, indent=2, ensure_ascii=False)
        
        print(f"\n{'='*70}")
        print(f"✓ Saved {len(all_courses)} total course entries to {raw_output}")
        print(f"✓ Saved {len(unique_courses_list)} unique courses to {metadata_output}")
        print(f"{'='*70}")
        
    finally:
        driver.quit()
    
    return all_courses

if __name__ == "__main__":
    print("\n" + "="*70)
    print("TED UNIVERSITY MULTI-SEMESTER COURSE SCRAPER")
    print("="*70)
    
    # Scrape both departments
    for dept_key in ["cmpe", "seng", "me", "ee"]:
        try:
            scrape_department(dept_key)
        except Exception as e:
            print(f"\n✗ Error scraping {dept_key}: {str(e)}")
    
    print("\n" + "="*70)
    print("SCRAPING COMPLETE!")
    print("="*70)
