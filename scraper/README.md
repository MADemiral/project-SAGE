# TEDU Course Scraper

Test scraper for TED University courses page.

## Setup

```bash
cd /home/alpdemial/Desktop/final/scraper
pip install -r requirements.txt
```

## Run

```bash
python app.py
```

This will:
1. Open Chrome browser (visible, not headless)
2. Navigate to https://cmpe.tedu.edu.tr/en/courses-offered
3. Analyze the page structure
4. Find all course links
5. Scrape details from the first 3 courses (as test)
6. Save results to `tedu_courses.json`
7. Wait for you to press Enter before closing

## What it does

- Prints page analysis (title, links found, sections)
- Shows course links found
- Extracts course information (code, name, credits, ECTS, etc.)
- Saves page source to `page_source.html` if no links found
- Prints the first 2000 characters of page content for debugging

## Output

- `tedu_courses.json` - Scraped course data
- `page_source.html` - Full page HTML (if no courses found)
