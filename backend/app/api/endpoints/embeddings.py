from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
import sys
import os

# Add scripts directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../../scripts'))

from scrape_courses import scrape_tedu_courses, save_courses_to_json
from create_embeddings import load_courses, create_course_documents, store_in_chromadb

router = APIRouter()


class EmbeddingResponse(BaseModel):
    status: str
    message: str
    courses_count: int = 0


class SearchRequest(BaseModel):
    query: str
    n_results: int = 5


class SearchResponse(BaseModel):
    results: list


async def scrape_and_embed_task():
    """Background task to scrape courses and create embeddings"""
    try:
        # Scrape courses
        courses = scrape_tedu_courses()
        
        # Save to JSON
        save_courses_to_json(courses, '/app/data/tedu_courses.json')
        
        # Create embeddings
        documents, metadatas, ids = create_course_documents(courses)
        store_in_chromadb(documents, metadatas, ids)
        
        print(f"✅ Successfully scraped and embedded {len(courses)} courses")
    except Exception as e:
        print(f"❌ Error in background task: {e}")
        raise


@router.post("/embeddings/create", response_model=EmbeddingResponse)
async def create_embeddings(background_tasks: BackgroundTasks):
    """
    Scrape TEDU course pages and create embeddings
    This is a long-running operation that runs in the background
    """
    try:
        # Add task to background
        background_tasks.add_task(scrape_and_embed_task)
        
        return EmbeddingResponse(
            status="started",
            message="Course scraping and embedding process started in background. Check logs for progress."
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/embeddings/create-sync", response_model=EmbeddingResponse)
async def create_embeddings_sync():
    """
    Scrape TEDU course pages and create embeddings (synchronous version)
    Use with caution - this will block until complete
    """
    try:
        # Scrape courses
        courses = scrape_tedu_courses()
        
        if not courses:
            return EmbeddingResponse(
                status="error",
                message="No courses found. The website may use JavaScript to load content.",
                courses_count=0
            )
        
        # Save to JSON
        save_courses_to_json(courses, '/app/data/tedu_courses.json')
        
        # Create embeddings
        documents, metadatas, ids = create_course_documents(courses)
        store_in_chromadb(documents, metadatas, ids)
        
        return EmbeddingResponse(
            status="success",
            message=f"Successfully scraped and embedded {len(courses)} courses",
            courses_count=len(courses)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/courses/search", response_model=SearchResponse)
async def search_courses(request: SearchRequest):
    """
    Search for courses using semantic search
    """
    try:
        import chromadb
        
        # Connect to ChromaDB
        client = chromadb.HttpClient(
            host=os.getenv('CHROMA_HOST', 'chromadb'),
            port=int(os.getenv('CHROMA_PORT', '8000'))
        )
        
        # Get collection
        collection = client.get_collection(name="tedu_courses")
        
        # Query
        results = collection.query(
            query_texts=[request.query],
            n_results=request.n_results
        )
        
        # Format results
        formatted_results = []
        if results['documents'] and len(results['documents']) > 0:
            for doc, meta, distance in zip(
                results['documents'][0],
                results['metadatas'][0],
                results['distances'][0]
            ):
                formatted_results.append({
                    'code': meta.get('code', ''),
                    'name': meta.get('name', ''),
                    'credits': meta.get('credits', ''),
                    'ects': meta.get('ects', ''),
                    'type': meta.get('type', ''),
                    'content': doc,
                    'relevance_score': 1 - distance  # Convert distance to similarity score
                })
        
        return SearchResponse(results=formatted_results)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/courses/stats")
async def get_course_stats():
    """
    Get statistics about the course database
    """
    try:
        import chromadb
        
        client = chromadb.HttpClient(
            host=os.getenv('CHROMA_HOST', 'chromadb'),
            port=int(os.getenv('CHROMA_PORT', '8000'))
        )
        
        try:
            collection = client.get_collection(name="tedu_courses")
            count = collection.count()
            
            return {
                "status": "ready",
                "total_courses": count,
                "collection_name": "tedu_courses"
            }
        except:
            return {
                "status": "not_initialized",
                "total_courses": 0,
                "message": "Course embeddings not yet created. Use POST /embeddings/create to initialize."
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
