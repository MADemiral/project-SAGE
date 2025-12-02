from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from pydantic import BaseModel
import chromadb
from sentence_transformers import SentenceTransformer
import psycopg2
import os

router = APIRouter()

# Configuration
CHROMA_HOST = os.getenv("CHROMA_HOST", "chromadb")
CHROMA_PORT = int(os.getenv("CHROMA_PORT", "8000"))
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "postgres")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
POSTGRES_DB = os.getenv("POSTGRES_DB", "sage_db")
POSTGRES_USER = os.getenv("POSTGRES_USER", "sage_user")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "sage_password")

# Embedding model
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
model = None
chroma_client = None
chroma_collection = None

def get_model():
    """Lazy load the embedding model"""
    global model
    if model is None:
        model = SentenceTransformer(MODEL_NAME)
    return model

def get_chroma_collection():
    """Get ChromaDB collection"""
    global chroma_client, chroma_collection
    if chroma_collection is None:
        chroma_client = chromadb.HttpClient(
            host=CHROMA_HOST,
            port=CHROMA_PORT
        )
        chroma_collection = chroma_client.get_or_create_collection(
            name="tedu_courses",
            metadata={"description": "TED University course catalog"}
        )
    return chroma_collection

def get_db_connection():
    """Get PostgreSQL connection"""
    return psycopg2.connect(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        database=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD
    )

# Schemas
class CourseSearchRequest(BaseModel):
    query: str
    top_k: int = 5
    department: Optional[str] = None

class CourseResponse(BaseModel):
    course_code: str
    course_title: str
    department: str
    level: str
    credits: str
    ects: str
    catalog_description: str
    prerequisites: List[str]
    instructor: str
    syllabus_url: str
    similarity_score: Optional[float] = None

class CourseDetailResponse(BaseModel):
    id: int
    course_code: str
    course_title: str
    department: str
    level: str
    credits: int
    ects: int
    hours: str
    catalog_description: str
    prerequisites: List[str]
    corequisites: List[str]
    instructor: str
    learning_outcomes: Optional[str]
    assessment_methods: Optional[str]
    textbooks: Optional[str]
    syllabus_url: str
    offered_semesters: List[str]
    semester_data: dict

@router.post("/search", response_model=List[CourseResponse])
async def search_courses(request: CourseSearchRequest):
    """
    Search courses using semantic similarity
    """
    try:
        # Get embedding model and ChromaDB collection
        model = get_model()
        collection = get_chroma_collection()
        
        # Create query embedding
        query_embedding = model.encode([request.query])[0].tolist()
        
        # Build where filter for department if specified
        where_filter = None
        if request.department:
            where_filter = {"department": request.department}
        
        # Search in ChromaDB
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=request.top_k,
            where=where_filter
        )
        
        # Format results
        courses = []
        for idx in range(len(results['ids'][0])):
            metadata = results['metadatas'][0][idx]
            distance = results['distances'][0][idx] if 'distances' in results else None
            
            # Convert distance to similarity score (1 - distance for cosine)
            similarity_score = 1 - distance if distance is not None else None
            
            courses.append(CourseResponse(
                course_code=metadata.get('course_code', ''),
                course_title=metadata.get('course_title', ''),
                department=metadata.get('department', ''),
                level=metadata.get('level', ''),
                credits=metadata.get('credits', ''),
                ects=metadata.get('ects', ''),
                catalog_description=results['documents'][0][idx][:500],
                prerequisites=[],  # Will be filled from DB if needed
                instructor=metadata.get('instructor', ''),
                syllabus_url=metadata.get('syllabus_url', ''),
                similarity_score=similarity_score
            ))
        
        return courses
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")

@router.get("/courses/{course_code}", response_model=CourseDetailResponse)
async def get_course_by_code(course_code: str):
    """
    Get full course details by course code
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, course_code, course_title, department, level, credits, ects, hours,
                   catalog_description, prerequisites, corequisites, instructor,
                   learning_outcomes, assessment_methods, textbooks, syllabus_url,
                   offered_semesters, semester_data
            FROM courses
            WHERE course_code = %s
        """, (course_code,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            raise HTTPException(status_code=404, detail=f"Course {course_code} not found")
        
        return CourseDetailResponse(
            id=row[0],
            course_code=row[1],
            course_title=row[2],
            department=row[3],
            level=row[4],
            credits=row[5] or 0,
            ects=row[6] or 0,
            hours=row[7] or "",
            catalog_description=row[8] or "",
            prerequisites=row[9] or [],
            corequisites=row[10] or [],
            instructor=row[11] or "",
            learning_outcomes=row[12],
            assessment_methods=row[13],
            textbooks=row[14],
            syllabus_url=row[15] or "",
            offered_semesters=row[16] or [],
            semester_data=row[17] or {}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/courses", response_model=List[CourseDetailResponse])
async def list_courses(
    department: Optional[str] = Query(None),
    level: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100)
):
    """
    List all courses with optional filters
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Build query with filters
        query = """
            SELECT id, course_code, course_title, department, level, credits, ects, hours,
                   catalog_description, prerequisites, corequisites, instructor,
                   learning_outcomes, assessment_methods, textbooks, syllabus_url,
                   offered_semesters, semester_data
            FROM courses
            WHERE 1=1
        """
        params = []
        
        if department:
            query += " AND department = %s"
            params.append(department)
        
        if level:
            query += " AND level = %s"
            params.append(level)
        
        query += " ORDER BY course_code LIMIT %s OFFSET %s"
        params.extend([limit, skip])
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        courses = []
        for row in rows:
            courses.append(CourseDetailResponse(
                id=row[0],
                course_code=row[1],
                course_title=row[2],
                department=row[3],
                level=row[4],
                credits=row[5] or 0,
                ects=row[6] or 0,
                hours=row[7] or "",
                catalog_description=row[8] or "",
                prerequisites=row[9] or [],
                corequisites=row[10] or [],
                instructor=row[11] or "",
                learning_outcomes=row[12],
                assessment_methods=row[13],
                textbooks=row[14],
                syllabus_url=row[15] or "",
                offered_semesters=row[16] or [],
                semester_data=row[17] or {}
            ))
        
        return courses
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/status")
async def embeddings_status():
    """Get status of embeddings system"""
    try:
        # Check ChromaDB
        collection = get_chroma_collection()
        chroma_count = collection.count()
        
        # Check PostgreSQL
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM courses")
        postgres_count = cursor.fetchone()[0]
        conn.close()
        
        return {
            "status": "operational",
            "chroma_collection": "tedu_courses",
            "chroma_count": chroma_count,
            "postgres_count": postgres_count,
            "embedding_model": MODEL_NAME
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
