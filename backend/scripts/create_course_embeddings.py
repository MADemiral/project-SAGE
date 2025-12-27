#!/usr/bin/env python3
"""
Create embeddings for course metadata and store in ChromaDB and PostgreSQL
"""

import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Tuple
import numpy as np
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import psycopg2
from psycopg2.extras import Json

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

# Configuration
CHROMA_HOST = os.getenv("CHROMA_HOST", "localhost")
CHROMA_PORT = int(os.getenv("CHROMA_PORT", "8001"))
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
POSTGRES_DB = os.getenv("POSTGRES_DB", "sage_db")
POSTGRES_USER = os.getenv("POSTGRES_USER", "sage_user")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "sage_password")

# Embedding model
MODEL_NAME = "intfloat/e5-large-v2"

# Similarity threshold for duplicate detection (86%)
SIMILARITY_THRESHOLD = 0.86

def load_course_metadata(file_path: str) -> List[Dict]:
    """Load course metadata from JSON file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def create_course_text(course: Dict) -> str:
    """Create searchable text representation of a course with emphasis on course code"""
    code = course.get('code', '')
    title = course.get('course_title', course.get('name', ''))
    
    # Repeat course code multiple times to boost exact matches
    parts = [
        f"Course Code: {code}",
        f"{code}",  # Standalone code
        f"{code}",  # Repeated for emphasis
        f"Course Title: {title}",
        f"{code} - {title}",  # Code with title
        f"Department: {course.get('department', '')}",
        f"Level: {course.get('level', '')}",
        f"Credits: {course.get('credits', '')} TEDU Credits, {course.get('ects', '')} ECTS",
        f"Description: {course.get('catalog_description', '')}",
    ]
    
    # Add PDF syllabus text if available (high priority for search)
    if course.get('syllabus_pdf_text'):
        parts.append(f"Full Syllabus Content: {course['syllabus_pdf_text'][:3000]}")
    
    # Add prerequisites
    if course.get('prerequisites'):
        parts.append(f"Prerequisites: {', '.join(course['prerequisites'])}")
    
    # Add learning outcomes
    if course.get('learning_outcomes'):
        parts.append(f"Learning Outcomes: {course['learning_outcomes']}")
    
    # Add instructors (handle both singular and plural fields)
    instructors = []
    if course.get('instructor'):
        instructors.append(course['instructor'])
    if course.get('instructors'):
        for inst_list in course['instructors']:
            # Handle comma-separated instructors in a single string
            if isinstance(inst_list, str):
                instructors.extend([i.strip() for i in inst_list.split(',')])
            else:
                instructors.append(str(inst_list))
    
    # Remove duplicates while preserving order
    unique_instructors = []
    seen = set()
    for inst in instructors:
        if inst and inst not in seen:
            unique_instructors.append(inst)
            seen.add(inst)
    
    if unique_instructors:
        parts.append(f"Instructors: {', '.join(unique_instructors)}")
    
    return "\n".join(parts)

def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """Calculate cosine similarity between two vectors"""
    dot_product = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    return dot_product / (norm1 * norm2)

def is_duplicate_course(collection, course_embedding: np.ndarray, course_code: str, threshold: float = SIMILARITY_THRESHOLD) -> Tuple[bool, float, str]:
    """
    Check if a course is a duplicate based on cosine similarity.
    Only checks against courses with the SAME course code to avoid missing different courses.
    Returns: (is_duplicate, similarity_score, similar_course_code)
    """
    try:
        # Check if this exact course code already exists in the collection
        try:
            existing = collection.get(ids=[course_code])
            if existing['ids']:
                # Course code already exists - check if content is similar enough
                existing_embedding = existing['embeddings'][0] if existing.get('embeddings') else None
                
                if existing_embedding:
                    # Calculate cosine similarity with existing version
                    similarity = cosine_similarity(
                        np.array(existing_embedding),
                        course_embedding
                    )
                    
                    if similarity >= threshold:
                        return True, similarity, course_code
        except Exception:
            # Course code doesn't exist yet - not a duplicate
            pass
        
        return False, 0.0, ""
        
    except Exception as e:
        print(f"   ⚠ Error checking similarity: {e}")
        return False, 0.0, ""

def setup_chromadb(reset: bool = False):
    """Initialize ChromaDB client and collection"""
    client = chromadb.HttpClient(
        host=CHROMA_HOST,
        port=CHROMA_PORT
    )
    
    # Only delete existing collection if reset=True (first-time setup)
    if reset:
        try:
            client.delete_collection("tedu_courses")
            print("✓ Deleted existing ChromaDB collection")
        except:
            pass
    
    # Get or create collection (safer method for newer ChromaDB versions)
    collection = client.get_or_create_collection(
        name="tedu_courses",
        metadata={"hnsw:space": "cosine"}  # Use cosine similarity for better semantic search
    )
    print("✓ ChromaDB collection ready: tedu_courses (cosine distance)")
    
    return collection

def setup_postgres():
    """Setup PostgreSQL tables for courses"""
    conn = psycopg2.connect(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        database=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD
    )
    
    cursor = conn.cursor()
    
    # Create courses table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS courses (
            id SERIAL PRIMARY KEY,
            course_code VARCHAR(50) UNIQUE NOT NULL,
            course_title VARCHAR(255) NOT NULL,
            department VARCHAR(50),
            level VARCHAR(10),
            credits INTEGER,
            ects INTEGER,
            hours VARCHAR(20),
            catalog_description TEXT,
            prerequisites JSONB,
            corequisites JSONB,
            instructor VARCHAR(255),
            learning_outcomes TEXT,
            assessment_methods TEXT,
            textbooks TEXT,
            syllabus_url VARCHAR(512),
            syllabus_pdf_url VARCHAR(512),
            syllabus_pdf_text TEXT,
            offered_semesters JSONB,
            semester_data JSONB,
            metadata JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create index on course_code
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_courses_code ON courses(course_code)
    """)
    
    # Create index on department
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_courses_department ON courses(department)
    """)
    
    conn.commit()
    print("✓ PostgreSQL tables created/verified")
    
    return conn

def store_in_postgres(conn, course: Dict):
    """Store course in PostgreSQL"""
    cursor = conn.cursor()
    
    # Prepare instructors list
    instructors = []
    if course.get('instructor'):
        instructors.append(course['instructor'])
    if course.get('instructors'):
        for inst_list in course['instructors']:
            if isinstance(inst_list, str):
                instructors.extend([i.strip() for i in inst_list.split(',')])
            else:
                instructors.append(str(inst_list))
    
    # Remove duplicates
    unique_instructors = list(dict.fromkeys([i for i in instructors if i]))
    instructor_str = ', '.join(unique_instructors) if unique_instructors else None
    
    cursor.execute("""
        INSERT INTO courses (
            course_code, course_title, department, level, credits, ects, hours,
            catalog_description, prerequisites, corequisites, instructor,
            learning_outcomes, assessment_methods, textbooks, syllabus_url,
            syllabus_pdf_url, syllabus_pdf_text,
            offered_semesters, semester_data, metadata
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
        ON CONFLICT (course_code) 
        DO UPDATE SET
            course_title = EXCLUDED.course_title,
            department = EXCLUDED.department,
            catalog_description = EXCLUDED.catalog_description,
            prerequisites = EXCLUDED.prerequisites,
            instructor = EXCLUDED.instructor,
            syllabus_pdf_url = EXCLUDED.syllabus_pdf_url,
            syllabus_pdf_text = EXCLUDED.syllabus_pdf_text,
            offered_semesters = EXCLUDED.offered_semesters,
            semester_data = EXCLUDED.semester_data,
            metadata = EXCLUDED.metadata,
            updated_at = CURRENT_TIMESTAMP
    """, (
        course.get('code'),
        course.get('course_title', course.get('name')),
        course.get('department'),
        course.get('level'),
        int(course.get('credits', 0)) if course.get('credits') else None,
        int(course.get('ects', 0)) if course.get('ects') else None,
        course.get('hours'),
        course.get('catalog_description'),
        Json(course.get('prerequisites', [])),
        Json(course.get('corequisites', [])),
        instructor_str,
        course.get('learning_outcomes'),
        course.get('assessment_methods'),
        course.get('textbooks'),
        course.get('syllabus_url'),
        course.get('syllabus_pdf_url'),
        course.get('syllabus_pdf_text'),
        Json(course.get('offered_semesters', [])),
        Json(course.get('semester_data', {})),
        Json(course)  # Store full metadata
    ))
    
    conn.commit()

def process_courses(metadata_files: List[str], reset: bool = False):
    """
    Process all course metadata files
    
    Args:
        metadata_files: List of JSON file paths containing course metadata
        reset: If True, deletes existing ChromaDB collection and starts fresh.
               If False, adds only new/changed courses (incremental update)
    """
    print("\n" + "="*70)
    if reset:
        print("CREATING COURSE EMBEDDINGS (FULL RESET)")
    else:
        print("UPDATING COURSE EMBEDDINGS (INCREMENTAL)")
    print("="*70)
    
    # Initialize
    print("\n1. Loading embedding model...")
    model = SentenceTransformer(MODEL_NAME)
    print(f"✓ Loaded model: {MODEL_NAME}")
    
    print("\n2. Setting up ChromaDB...")
    collection = setup_chromadb(reset=reset)
    
    print("\n3. Setting up PostgreSQL...")
    conn = setup_postgres()
    
    print("\n4. Processing courses...")
    
    all_courses = []
    for file_path in metadata_files:
        if os.path.exists(file_path):
            print(f"\n   Loading: {file_path}")
            courses = load_course_metadata(file_path)
            all_courses.extend(courses)
            print(f"   ✓ Loaded {len(courses)} courses")
        else:
            print(f"   ✗ File not found: {file_path}")
    
    print(f"\n   Total courses to process: {len(all_courses)}")
    
    print(f"\n5. Creating embeddings and checking for duplicates...")
    print(f"   Similarity threshold: {SIMILARITY_THRESHOLD * 100}%")
    
    # Track statistics
    added_count = 0
    duplicate_count = 0
    error_count = 0
    
    # Process each course individually to check for duplicates
    for idx, course in enumerate(all_courses):
        course_code = course.get('code', f'UNKNOWN_{idx}')
        
        # Create searchable text
        course_text = create_course_text(course)
        
        # Create embedding for this course
        course_embedding = model.encode([course_text])[0]
        
        # Check if this course is a duplicate
        is_dup, similarity, similar_code = is_duplicate_course(collection, course_embedding, course_code)
        
        if is_dup:
            duplicate_count += 1
            print(f"   ⊘ Skipping {course_code}: {similarity*100:.1f}% similar to {similar_code}")
            continue
        
        # Prepare instructors list for metadata
        instructors = []
        if course.get('instructor'):
            instructors.append(course['instructor'])
        if course.get('instructors'):
            for inst_list in course['instructors']:
                if isinstance(inst_list, str):
                    instructors.extend([i.strip() for i in inst_list.split(',')])
                else:
                    instructors.append(str(inst_list))
        
        # Remove duplicates
        unique_instructors = list(dict.fromkeys([i for i in instructors if i]))
        instructor_str = ', '.join(unique_instructors) if unique_instructors else ''
        
        # Debug output for courses with multiple instructors
        if len(unique_instructors) > 1:
            print(f"   → {course_code}: Multiple instructors found: {instructor_str}")
        
        # Prepare metadata for ChromaDB
        metadata = {
            "course_code": course_code,
            "course_title": course.get('course_title', course.get('name', '')),
            "department": course.get('department', ''),
            "level": course.get('level', ''),
            "credits": str(course.get('credits', '')),
            "ects": str(course.get('ects', '')),
            "instructor": instructor_str,
            "syllabus_url": course.get('syllabus_url', ''),
            "syllabus_pdf_url": course.get('syllabus_pdf_url', ''),
        }
        
        # Add to ChromaDB
        try:
            collection.add(
                documents=[course_text],
                embeddings=[course_embedding.tolist()],
                metadatas=[metadata],
                ids=[course_code]
            )
            
            # Store in PostgreSQL
            store_in_postgres(conn, course)
            
            added_count += 1
            if (idx + 1) % 10 == 0 or idx == len(all_courses) - 1:
                print(f"   Progress: {idx + 1}/{len(all_courses)} courses checked, {added_count} added, {duplicate_count} duplicates skipped")
                
        except Exception as e:
            error_count += 1
            print(f"   ✗ Error storing {course_code}: {e}")
    
    conn.close()
    
    print("\n" + "="*70)
    print("✓ EMBEDDING CREATION COMPLETE!")
    print("="*70)
    print(f"\nSummary:")
    print(f"  - Total courses checked: {len(all_courses)}")
    print(f"  - Unique courses added: {added_count}")
    print(f"  - Duplicates skipped: {duplicate_count} (similarity ≥ {SIMILARITY_THRESHOLD * 100}%)")
    print(f"  - Errors: {error_count}")
    print(f"  - ChromaDB collection: tedu_courses")
    print(f"  - PostgreSQL table: courses")
    print(f"  - Embedding model: {MODEL_NAME}")
    print(f"  - Vector dimensions: {course_embedding.shape[0]}")
    

if __name__ == "__main__":
    # List of metadata files - check multiple possible locations
    possible_paths = [
        # Docker worker container paths
        ("/workspace/data/tedu_cmpe_courses_metadata.json",
         "/workspace/data/tedu_seng_courses_metadata.json",
         "/workspace/data/tedu_me_courses_metadata.json",
         "/workspace/data/tedu_ee_courses_metadata.json"),
        # Backend container paths
        ("/app/data/tedu_cmpe_courses_metadata.json",
         "/app/data/tedu_seng_courses_metadata.json",
         "/app/data/tedu_me_courses_metadata.json",
         "/app/data/tedu_ee_courses_metadata.json"),
        # Local paths for testing
        ("/home/alpdemial/Desktop/final/data/tedu_cmpe_courses_metadata.json",
         "/home/alpdemial/Desktop/final/data/tedu_seng_courses_metadata.json",
         "/home/alpdemial/Desktop/final/data/tedu_me_courses_metadata.json",
         "/home/alpdemial/Desktop/final/data/tedu_ee_courses_metadata.json"),
        # Scraper output directory
        ("/home/alpdemial/Desktop/final/tedu_cmpe_courses_metadata.json",
         "/home/alpdemial/Desktop/final/tedu_seng_courses_metadata.json",
         "/home/alpdemial/Desktop/final/tedu_me_courses_metadata.json",
         "/home/alpdemial/Desktop/final/tedu_ee_courses_metadata.json"),
    ]
    
    # Find which path exists
    metadata_files = None
    for paths in possible_paths:
        if all(os.path.exists(p) for p in paths):
            metadata_files = list(paths)
            break
        # Check if at least one exists
        existing = [p for p in paths if os.path.exists(p)]
        if existing and metadata_files is None:
            metadata_files = existing
    
    if not metadata_files:
        print("❌ No metadata files found!")
        print("Please run the scraper first: make scrape-courses")
        sys.exit(1)
    
    print(f"Found {len(metadata_files)} metadata files:")
    for f in metadata_files:
        print(f"  - {f}")
    
    # Check for --reset flag to do full reset instead of incremental update
    reset_mode = "--reset" in sys.argv or "--full" in sys.argv
    
    if reset_mode:
        print("\n⚠️  RESET MODE: Will delete existing data and create fresh embeddings")
    else:
        print("\n📊 INCREMENTAL MODE: Will only add new/changed courses (86% similarity check)")
    
    process_courses(metadata_files, reset=reset_mode)

