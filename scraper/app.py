#!/usr/bin/env python3
"""
Selenium scraper for TED University courses
URL: https://cmpe.tedu.edu.tr/en/courses-offered
"""

import json
import time
import re
from typing import Dict, Optional, List
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options


def setup_driver():
    """Setup Chrome driver."""
    chrome_options = Options()
    # chrome_options.add_argument("--headless")  # Comment out to see the browser
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    
    # Try to use Chrome directly (assumes chromedriver is in PATH)
    try:
        driver = webdriver.Chrome(options=chrome_options)
    except Exception as e:
        print(f"Error with Chrome: {e}")
        print("Trying Firefox instead...")
        driver = webdriver.Firefox()
    
    return driver


def scrape_syllabus_detail(driver, syllabus_url: str) -> Dict:
    """Scrape detailed course information from syllabus page."""
    try:
        print(f"    Opening syllabus: {syllabus_url}")
        driver.get(syllabus_url)
        time.sleep(0.1)  # Wait for page to load
        
        detail_info = {
            "course_code": "",
            "course_title": "",
            "level": "",
            "credit_hours": "",
            "academic_year": "",
            "semester": "",
            "catalog_description": "",
            "prerequisites": "",
            "corequisites": "",
            "instructor": "",
            "learning_outcomes": "",
            "learning_activities": "",
            "assessment_methods": "",
            "textbooks": "",
            "weekly_schedule": ""
        }
        
        # Get all text from the page
        page_text = driver.find_element(By.TAG_NAME, "body").text
        
        # Extract structured information using regex
        import re
        
        # Course Code & Number
        code_match = re.search(r'Course Code & Number:\s*([^\n]+)', page_text, re.IGNORECASE)
        if code_match:
            detail_info["course_code"] = code_match.group(1).strip()
        
        # Course Title
        title_match = re.search(r'Course Title:\s*([^\n]+)', page_text, re.IGNORECASE)
        if title_match:
            detail_info["course_title"] = title_match.group(1).strip()
        
        # Level
        level_match = re.search(r'Level:\s*([^\n]+)', page_text, re.IGNORECASE)
        if level_match:
            detail_info["level"] = level_match.group(1).strip()
        
        # Credit Hours / ECTS
        credit_match = re.search(r'Credit Hours/ ECTS Credits:\s*([^\n]+)', page_text, re.IGNORECASE)
        if credit_match:
            detail_info["credit_hours"] = credit_match.group(1).strip()
        
        # Academic Year
        year_match = re.search(r'Academic Year\s*([^\n]+)', page_text, re.IGNORECASE)
        if year_match:
            detail_info["academic_year"] = year_match.group(1).strip()
        
        # Semester
        semester_match = re.search(r'Semester\s*([^\n]+)', page_text, re.IGNORECASE)
        if semester_match:
            detail_info["semester"] = semester_match.group(1).strip()
        
        # Catalog Description
        desc_match = re.search(r'Catalog Description:\s*([^\n]+(?:\n(?!Pre-requisite|Learning Outcomes|Learning Activities|Assessment)[^\n]+)*)', 
                              page_text, re.IGNORECASE)
        if desc_match:
            detail_info["catalog_description"] = desc_match.group(1).strip()
        
        # Prerequisites
        prereq_match = re.search(r'Pre-requisites?:\s*([^\n]+)', page_text, re.IGNORECASE)
        if prereq_match:
            detail_info["prerequisites"] = prereq_match.group(1).strip()
        
        # Corequisites
        coreq_match = re.search(r'Co-requisites?:\s*([^\n]+)', page_text, re.IGNORECASE)
        if coreq_match:
            detail_info["corequisites"] = coreq_match.group(1).strip()
        
        # Instructor
        instructor_match = re.search(r'Instructor:\s*([^\n]+)', page_text, re.IGNORECASE)
        if instructor_match:
            detail_info["instructor"] = instructor_match.group(1).strip()
        
        # Learning Outcomes
        outcomes_match = re.search(r'Learning Outcomes:\s*Upon succesful completion.*?(?=Learning Activities|Assessment Methods|Textbook|$)', 
                                  page_text, re.IGNORECASE | re.DOTALL)
        if outcomes_match:
            detail_info["learning_outcomes"] = outcomes_match.group(0).strip()[:1000]
        
        # Learning Activities and Teaching Methods
        activities_match = re.search(r'Learning Activities and Teaching Methods:\s*(.*?)(?=Assessment Methods|Textbook|$)', 
                                    page_text, re.IGNORECASE | re.DOTALL)
        if activities_match:
            detail_info["learning_activities"] = activities_match.group(1).strip()[:500]
        
        # Assessment Methods and Criteria
        assessment_match = re.search(r'Assessment Methods and Criteria:\s*(.*?)(?=Textbook|Weekly Schedule|$)', 
                                    page_text, re.IGNORECASE | re.DOTALL)
        if assessment_match:
            detail_info["assessment_methods"] = assessment_match.group(1).strip()[:500]
        
        # Textbooks
        textbook_match = re.search(r'(?:Textbooks?|Required Textbooks?):\s*(.*?)(?=Weekly Schedule|Assessment|$)', 
                                  page_text, re.IGNORECASE | re.DOTALL)
        if textbook_match:
            detail_info["textbooks"] = textbook_match.group(1).strip()[:500]
        
        # Weekly Schedule
        schedule_match = re.search(r'(?:Weekly Schedule|Course Outline):\s*(.*?)$', 
                                  page_text, re.IGNORECASE | re.DOTALL)
        if schedule_match:
            detail_info["weekly_schedule"] = schedule_match.group(1).strip()[:1000]
        
        print(f"    ✓ Extracted syllabus details")
        return detail_info
        
    except Exception as e:
        print(f"    ✗ Error scraping syllabus: {e}")
        import traceback
        traceback.print_exc()
        return {
            "course_code": "",
            "course_title": "",
            "level": "",
            "credit_hours": "",
            "academic_year": "",
            "semester": "",
            "catalog_description": "",
            "prerequisites": "",
            "corequisites": "",
            "instructor": "",
            "learning_outcomes": "",
            "learning_activities": "",
            "assessment_methods": "",
            "textbooks": "",
            "weekly_schedule": ""
        }


def scrape_course_detail(driver, course_url: str) -> Optional[Dict]:
    """Scrape detailed information from a course page."""
    try:
        print(f"  Scraping: {course_url}")
        driver.get(course_url)
        
        # Wait for page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        time.sleep(0.1)  # Additional wait for dynamic content
        
        course_data = {
            "url": course_link,
            "code": "",
            "name": "",
            "credits": "",
            "ects": "",
            "semester": "",
            "type": "",
            "prerequisite": "",
            "description": "",
            "syllabus": []
        }
        
        # Get the page text to extract information
        page_text = driver.find_element(By.TAG_NAME, "body").text
        
        print(f"\n--- Course Detail Page ---")
        print(f"URL: {course_link}")
        print(f"Page text preview: {page_text[:500]}...")
        
        # Try to find course info in tables or structured elements
        try:
            # Look for tables
            tables = driver.find_elements(By.TAG_NAME, "table")
            for table in tables:
                rows = table.find_elements(By.TAG_NAME, "tr")
                for row in rows:
                    cells = row.find_elements(By.TAG_NAME, "td")
                    if len(cells) >= 2:
                        key = cells[0].text.strip().lower()
                        value = cells[1].text.strip()
                        print(f"Table row: {key} = {value}")
                        
                        if 'code' in key or 'kodu' in key:
                            course_data["code"] = value
                        elif 'name' in key or 'adı' in key or 'title' in key:
                            course_data["name"] = value
                        elif 'credit' in key and 'ects' not in key:
                            course_data["credits"] = value
                        elif 'ects' in key:
                            course_data["ects"] = value
                        elif 'semester' in key or 'dönem' in key:
                            course_data["semester"] = value
                        elif 'prerequisite' in key or 'önkoşul' in key:
                            course_data["prerequisite"] = value
                        elif 'description' in key or 'açıklama' in key or 'content' in key:
                            course_data["description"] = value
        except Exception as e:
            print(f"Error extracting from tables: {e}")
        
        # Try to find syllabus/weekly schedule
        try:
            # Look for syllabus sections
            headings = driver.find_elements(By.CSS_SELECTOR, "h1, h2, h3, h4, strong, b")
            for heading in headings:
                text = heading.text.strip().lower()
                if 'syllabus' in text or 'weekly' in text or 'haftalık' in text or 'plan' in text:
                    # Get the next siblings or parent container
                    parent = heading.find_element(By.XPATH, "./..")
                    syllabus_text = parent.text
                    course_data["syllabus"].append(syllabus_text)
                    print(f"Found syllabus section: {syllabus_text[:200]}...")
        except Exception as e:
            print(f"Error extracting syllabus: {e}")
        
        return course_data
        
    except Exception as e:
        print(f"Error scraping course detail: {e}")
        return None


def scrape_courses():
    """Main scraping function."""
    driver = None
    all_courses = []
    
    try:
        print("Setting up Chrome driver...")
        driver = setup_driver()
        
        url = "https://cmpe.tedu.edu.tr/en/courses-offered"
        print(f"\nNavigating to: {url}")
        driver.get(url)
        
        # Wait for page to load
        time.sleep(0.1)
        
        print("\n=== PAGE ANALYSIS ===")
        print(f"Page title: {driver.title}")
        
        # Look for semester/year dropdown
        print("\n=== LOOKING FOR SEMESTER DROPDOWN ===")
        try:
            # Find the select element (dropdown)
            selects = driver.find_elements(By.TAG_NAME, "select")
            print(f"Found {len(selects)} dropdown(s)")
            
            if selects:
                # Get the first select element (semester selector)
                semester_select = selects[0]
                
                # Get all options
                from selenium.webdriver.support.ui import Select
                select_obj = Select(semester_select)
                options = select_obj.options
                
                print(f"\nAvailable semesters: {len(options)}")
                for i, option in enumerate(options[:5]):  # Show first 5
                    print(f"  {i}: {option.text} (value: {option.get_attribute('value')})")
                
                # Select Fall 2025 (current semester)
                print("\nSelecting 'Fall 2025'...")
                select_obj.select_by_visible_text("Fall 2025")
                
                # Wait for courses to load - look for content to appear
                print("Waiting for courses to load...")
                time.sleep(0.1)
                
                # Print the page text to see what actually loaded
                print("\n=== PAGE CONTENT AFTER SELECTION ===")
                body_text = driver.find_element(By.TAG_NAME, "body").text
                print("First 3000 characters of page:")
                print(body_text[:3000])
                print("\n" + "="*60)
                
                # Now look for course information
                print("\n=== ANALYZING LOADED COURSES ===")
                
                # Parse courses from the text content
                import re
                body_text = driver.find_element(By.TAG_NAME, "body").text
                
                # Split by "Code:" to get individual course blocks
                course_blocks = body_text.split("Code:")[1:]  # Skip first element (header)
                print(f"Found {len(course_blocks)} course section entries")
                
                # Dictionary to store unique courses (without section numbers)
                unique_courses = {}
                section_instructors = {}  # Track instructors per section
                
                # Find all "View Syllabus" links
                syllabus_links_elements = driver.find_elements(By.PARTIAL_LINK_TEXT, "View Syllabus")
                syllabus_links = [link.get_attribute("href") for link in syllabus_links_elements if link.get_attribute("href")]
                print(f"Found {len(syllabus_links)} syllabus links")
                
                # Create a mapping of course blocks to syllabus links
                for idx, block in enumerate(course_blocks):
                    lines = block.strip().split('\n')
                    if len(lines) < 2:
                        continue
                    
                    # First line has: code - name, (lab+tutorial+lecture) credits / ECTS
                    first_line = lines[0].strip()
                    
                    # Parse with regex
                    # Pattern: CMPE 113_01 - Fundamentals of Programming I, (2+0+2) 3 Credits / 5 ECTS
                    match = re.match(r'([A-Z]+\s*\d+)_(\d+)\s*-\s*([^,]+),\s*\(([^)]+)\)\s*(\d+)\s*Credits\s*/\s*(\d+)\s*ECTS', first_line)
                    
                    if match:
                        base_code = match.group(1).strip()  # e.g., "CMPE 113" (without section)
                        section_num = match.group(2)  # e.g., "01"
                        name = match.group(3).strip()
                        hours = match.group(4)  # e.g., "2+0+2"
                        credits = match.group(5)
                        ects = match.group(6)
                        
                        # Extract staff
                        staff = ""
                        for line in lines[1:]:
                            if line.startswith("Staff:"):
                                continue
                            elif line.startswith("Syllabus:"):
                                continue
                            elif line.strip() and not line.startswith("View Syllabus"):
                                if not staff:
                                    staff = line.strip()
                        
                        # If this is the first section of this course, create the entry
                        if base_code not in unique_courses:
                            unique_courses[base_code] = {
                                "code": base_code,
                                "name": name,
                                "hours": hours,
                                "credits": credits,
                                "ects": ects,
                                "semester": "Fall 2025",
                                "sections": [],
                                "instructors": [],
                                "syllabus_url": syllabus_links[idx] if idx < len(syllabus_links) else "",
                                # Syllabus details (to be filled later)
                                "course_code": "",
                                "course_title": "",
                                "level": "",
                                "credit_hours": "",
                                "academic_year": "",
                                "catalog_description": "",
                                "prerequisites": "",
                                "corequisites": "",
                                "learning_outcomes": "",
                                "learning_activities": "",
                                "assessment_methods": "",
                                "textbooks": "",
                                "weekly_schedule": ""
                            }
                        
                        # Add section info
                        unique_courses[base_code]["sections"].append(section_num)
                        if staff and staff not in unique_courses[base_code]["instructors"]:
                            unique_courses[base_code]["instructors"].append(staff)
                
                print(f"\nFound {len(unique_courses)} unique courses (combined sections)")
                
                # Now scrape syllabus for each unique course
                print("\n=== SCRAPING SYLLABUS DETAILS ===")
                for idx, (code, course_data) in enumerate(unique_courses.items(), 1):
                    print(f"[{idx}/{len(unique_courses)}] {code} - {course_data['name']}")
                    
                    if course_data["syllabus_url"]:
                        # Scrape the syllabus page
                        syllabus_detail = scrape_syllabus_detail(driver, course_data["syllabus_url"])
                        
                        # Update course with syllabus details
                        course_data.update(syllabus_detail)
                        
                        # Small delay between requests
                        time.sleep(0.1)
                    else:
                        print(f"    ⚠ No syllabus URL found")
                    
                    # Convert instructors list to string
                    course_data["instructors"] = ", ".join(course_data["instructors"])
                    course_data["sections"] = ", ".join(course_data["sections"])
                
                # Convert dictionary to list
                all_courses = list(unique_courses.values())
                print(f"\n✓ Successfully processed {len(all_courses)} unique courses")
                
                # Also look for links to course detail pages
                print("\n=== LOOKING FOR COURSE DETAIL LINKS ===")
                all_links = driver.find_elements(By.TAG_NAME, "a")
                course_detail_links = []
                
                for link in all_links:
                    try:
                        href = link.get_attribute("href")
                        text = link.text.strip()
                        
                        # Look for course codes in link text (e.g., CMPE 101)
                        if text and href and len(text) > 3:
                            import re
                            if re.match(r'^[A-Z]{2,4}\s*\d{3}', text):
                                print(f"  Found course link: {text} -> {href}")
                                course_detail_links.append({
                                    'code': text,
                                    'url': href
                                })
                    except:
                        continue
                
                print(f"\nFound {len(course_detail_links)} course detail links")
                
                # If we found detail links, scrape first 3
                if course_detail_links:
                    print("\n=== SCRAPING COURSE DETAILS ===")
                    for i, link_info in enumerate(course_detail_links[:3], 1):
                        print(f"\n[{i}/3] Scraping: {link_info['code']}")
                        detail_data = scrape_course_detail(driver, link_info['url'])
                        if detail_data:
                            # Update existing course or add new
                            existing = next((c for c in all_courses if c['code'] == link_info['code']), None)
                            if existing:
                                existing.update(detail_data)
                            else:
                                all_courses.append(detail_data)
                        time.sleep(0.1)
                        
        except Exception as e:
            print(f"Error with dropdown: {e}")
            import traceback
            traceback.print_exc()
        
        # Save page source for analysis
        print("\nSaving page source for analysis...")
        with open("page_source.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        print("Page source saved to page_source.html")
        
        return all_courses
        
    except Exception as e:
        print(f"\nError during scraping: {e}")
        import traceback
        traceback.print_exc()
        return all_courses
        
    finally:
        if driver:
            print("\n=== CLOSING BROWSER ===")
            # Auto-close after 0.1 seconds
            time.sleep(0.1)
            driver.quit()


def main():
    """Main function."""
    print("="*60)
    print("TED University Course Scraper")
    print("="*60)
    
    courses = scrape_courses()
    
    # Save results
    output_file = "tedu_courses.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(courses, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ Saved {len(courses)} courses to {output_file}")
    
    # Print summary
    print("\n" + "="*60)
    print(f"Total courses scraped: {len(courses)}")
    if courses:
        print("\nFirst course:")
        print(json.dumps(courses[0], indent=2, ensure_ascii=False))
    print("="*60)


if __name__ == "__main__":
    main()
