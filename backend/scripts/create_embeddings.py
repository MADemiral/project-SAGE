"""
Generate embeddings for course data and store in ChromaDB
"""

import json
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import os


def load_courses(filepath='/app/data/tedu_courses.json'):
    """Load course data from JSON file"""
    with open(filepath, 'r', encoding='utf-8') as f:
        courses = json.load(f)
    print(f"Loaded {len(courses)} courses")
    return courses


def create_course_documents(courses):
    """Create text documents from course data for embedding"""
    documents = []
    metadatas = []
    ids = []
    
    for course in courses:
        # Create a rich text description
        doc_text = f"""
Course Code: {course['code']}
Course Name: {course['name']}
Credits: {course['credits']} | ECTS: {course['ects']}
Semester: {course['semester']}
Type: {course['type']}
Description: {course['description']}
        """.strip()
        
        documents.append(doc_text)
        metadatas.append({
            'code': course['code'],
            'name': course['name'],
            'credits': course['credits'],
            'ects': course['ects'],
            'semester': course['semester'],
            'type': course['type']
        })
        ids.append(course['code'])
    
    return documents, metadatas, ids


def store_in_chromadb(documents, metadatas, ids):
    """Store course documents in ChromaDB with embeddings"""
    
    # Connect to ChromaDB
    chroma_host = os.getenv('CHROMA_HOST', 'chromadb')
    chroma_port = os.getenv('CHROMA_PORT', '8000')
    
    print(f"Connecting to ChromaDB at {chroma_host}:{chroma_port}")
    
    client = chromadb.HttpClient(
        host=chroma_host,
        port=int(chroma_port)
    )
    
    # Create or get collection
    collection_name = "tedu_courses"
    
    try:
        # Delete existing collection if it exists
        try:
            client.delete_collection(name=collection_name)
            print(f"Deleted existing collection: {collection_name}")
        except:
            pass
        
        # Create new collection
        collection = client.create_collection(
            name=collection_name,
            metadata={"description": "TED University Computer Engineering Courses"}
        )
        print(f"Created collection: {collection_name}")
        
        # Add documents
        collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        
        print(f"Added {len(documents)} documents to ChromaDB")
        
        # Verify
        count = collection.count()
        print(f"Collection now has {count} documents")
        
        # Test query
        print("\nTesting query: 'machine learning'")
        results = collection.query(
            query_texts=["machine learning artificial intelligence"],
            n_results=3
        )
        
        print("Top 3 results:")
        for i, (doc, meta) in enumerate(zip(results['documents'][0], results['metadatas'][0])):
            print(f"{i+1}. {meta['code']}: {meta['name']}")
        
        return collection
        
    except Exception as e:
        print(f"Error: {e}")
        raise


if __name__ == "__main__":
    # Load courses
    courses = load_courses()
    
    # Create documents
    documents, metadatas, ids = create_course_documents(courses)
    
    # Store in ChromaDB
    collection = store_in_chromadb(documents, metadatas, ids)
    
    print("\n✅ Course embeddings successfully created and stored!")
