# SAGE - Smart Analysis and Generation Engine

An intelligent chatbot system for TED University that provides semantic search and analysis of course information using AI-powered embeddings and natural language processing.

## 🎯 Features

- **Semantic Course Search**: Find courses using natural language queries
- **Multi-Department Support**: CMPE, SENG, ME, EE departments
- **Automated Course Scraping**: Selenium-based web scraper for TED University course catalogs
- **Vector Embeddings**: ChromaDB for efficient similarity search with sentence-transformers
- **RESTful API**: FastAPI backend with PostgreSQL database
- **Modern Frontend**: React + Vite with Tailwind CSS
- **Containerized**: Full Docker Compose setup for easy deployment

## 🏗️ Architecture

```
SAGE/
├── backend/          # FastAPI application
│   ├── app/         # API routes and endpoints
│   └── scripts/     # Course embedding creation
├── frontend/        # React application
├── scraper/         # Selenium course scraper
├── database/        # PostgreSQL schema
├── nginx/           # Reverse proxy configuration
└── data/            # Scraped course metadata
```

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- 8GB+ RAM recommended
- 20GB+ disk space

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/MADemiral/project-SAGE.git
cd project-SAGE
```

2. **Build all services**
```bash
docker-compose build
```

3. **Start the system**
```bash
docker-compose up -d postgres chromadb backend frontend nginx
```

4. **Initialize course data** (scrape and create embeddings)
```bash
docker-compose run --rm course_worker
```

This will:
- Scrape courses from TED University (Fall 2025 & Spring 2025)
- Create vector embeddings using sentence-transformers
- Store data in ChromaDB and PostgreSQL
- Takes ~5-10 minutes on first run

### Access the Application

- **Frontend**: http://localhost
- **API Documentation**: http://localhost/api/docs
- **PgAdmin**: http://localhost:5050 (if started)

## 📊 Course Data

The system currently supports:
- **Departments**: CMPE, SENG, ME, EE
- **Semesters**: Fall 2025, Spring 2025
- **Total Courses**: ~74 unique courses
- **Embedding Model**: intfloat/e5-large-v2 (1024 dimensions)

### Course Information Includes:
- Course code and title
- Credits, ECTS, hours
- Prerequisites and corequisites
- Catalog description
- Learning outcomes
- Assessment methods
- Textbooks
- Instructor information
- Syllabus links

## 🔧 Configuration

### Environment Variables

Key environment variables (configured in `docker-compose.yml`):

**Backend:**
- `DATABASE_URL`: PostgreSQL connection
- `CHROMA_HOST`: ChromaDB hostname
- `SECRET_KEY`: JWT token secret

**Database:**
- `POSTGRES_USER`: sage_user
- `POSTGRES_PASSWORD`: sage_password
- `POSTGRES_DB`: sage_db

## 🛠️ Development

### Makefile Commands

```bash
make up                # Start all services
make up-with-courses   # Start + initialize courses
make down              # Stop all services
make logs              # View all logs
make init-courses      # Run course initialization
make clean             # Remove all containers and volumes
```

### Update Course Data

To refresh course data:
```bash
docker-compose run --rm course_worker
```

## 📡 API Endpoints

### Course Search
```bash
POST /api/v1/courses/search
{
  "query": "machine learning algorithms",
  "top_k": 5
}
```

### Get Course by Code
```bash
GET /api/v1/courses/CMPE%20211
```

### List Courses
```bash
GET /api/v1/courses?department=CMPE&limit=10
```

### System Status
```bash
GET /api/v1/courses/status
```

## 🔍 How It Works

1. **Web Scraping**: Selenium scrapes course pages from TED University
2. **Data Processing**: Extracts structured information (code, title, description, etc.)
3. **Embedding Creation**: Converts course text to 1024-dim vectors using intfloat/e5-large-v2
4. **Deduplication**: Checks 86% similarity threshold to skip duplicate courses
5. **Storage**: Saves vectors to ChromaDB, metadata to PostgreSQL
6. **Search**: User queries → embedding → ChromaDB similarity search → ranked results

## 🐳 Docker Services

| Service | Port | Description |
|---------|------|-------------|
| nginx | 80, 443 | Reverse proxy |
| frontend | 5173 | React development server |
| backend | 8000 | FastAPI application |
| postgres | 5432 | PostgreSQL database |
| chromadb | 8001 | Vector database |
| pgadmin | 5050 | Database admin (optional) |

## 📦 Tech Stack

**Backend:**
- FastAPI 0.109.0
- SQLAlchemy 2.0.25
- ChromaDB 0.4.24
- sentence-transformers 2.2.2
- PyTorch 2.0.1

**Frontend:**
- React 18
- Vite 5
- Tailwind CSS 3

**Scraping:**
- Selenium 4.15.2
- BeautifulSoup4 4.12.3
- Chrome WebDriver

**Database:**
- PostgreSQL 16
- ChromaDB (vector store)

## 🔐 Security

- JWT-based authentication
- Bcrypt password hashing
- CORS configuration
- SQL injection protection via SQLAlchemy ORM

## 📝 License

This project is part of TED University coursework.

## 👥 Contributors

- Mehmet Alperen Demiral (MADemiral)

## 🤝 Contributing

This is an academic project. For issues or suggestions, please open an issue on GitHub.

## 📞 Support

For questions or issues:
- Create an issue on GitHub
- Check API documentation at `/api/docs`
- Review logs: `make logs`
