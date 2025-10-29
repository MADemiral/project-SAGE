# PostgreSQL Database Configuration

This directory contains the database initialization scripts and configuration files for the SAGE application.

## Files

- `init.sql`: Database initialization script that creates tables, indexes, and sample data
- `.env`: Environment variables for database configuration (create from `.env.example`)

## Database Schema

### Tables

#### documents
Stores document metadata and content
- `id`: Primary key
- `title`: Document title
- `filename`: Original filename
- `file_path`: Storage path
- `content`: Extracted text content
- `document_type`: Type classification (report, design, specification)
- `is_processed`: Processing status flag
- `vector_id`: Reference to ChromaDB vector
- `created_at`, `updated_at`: Timestamps

#### users
User authentication and management
- `id`: Primary key
- `username`, `email`: Unique identifiers
- `hashed_password`: Secure password storage
- `full_name`: Display name
- `is_active`, `is_superuser`: Permission flags
- `created_at`, `updated_at`: Timestamps

#### analysis_results
AI analysis outputs
- `id`: Primary key
- `document_id`: Foreign key to documents
- `analysis_type`: Type of analysis performed
- `result_data`: JSON analysis results
- `summary`: Text summary
- `confidence_score`: Analysis confidence
- `created_at`, `updated_at`: Timestamps

#### queries
User query history
- `id`: Primary key
- `user_id`: Foreign key to users
- `query_text`: User question
- `response_text`: AI response
- `context_documents`: Related documents (JSON)
- `created_at`: Timestamp

## Development

The database is automatically initialized when starting the Docker containers.
Sample data is inserted for the three existing reports in your project.
