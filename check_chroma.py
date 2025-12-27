#!/usr/bin/env python3
import chromadb
import os

client = chromadb.HttpClient(
    host=os.getenv("CHROMA_HOST", "chromadb"),
    port=8000
)

collection = client.get_collection("tedu_courses")

# Get CMPE 113
results = collection.get(ids=["CMPE 113"])

if results['ids']:
    print("CMPE 113 metadata from ChromaDB:")
    print(f"  Course Code: {results['metadatas'][0]['course_code']}")
    print(f"  Instructor: {results['metadatas'][0]['instructor']}")
    print(f"\nFull metadata:")
    for key, value in results['metadatas'][0].items():
        print(f"  {key}: {value}")
else:
    print("CMPE 113 not found in ChromaDB")
