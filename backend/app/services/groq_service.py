"""
Groq API Service for Academic and Social Assistants with RAG
Supports Turkish and English responses based on user query language
Uses E5 embeddings for semantic search of documents, courses, restaurants, and events
"""

import os
from typing import List, Dict, Optional
from groq import Groq
from langdetect import detect, LangDetectException
import psycopg2
from psycopg2.extras import RealDictCursor
from sentence_transformers import SentenceTransformer
import chromadb
import numpy as np

class GroqAcademicService:
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY not found in environment variables")
        
        self.client = Groq(api_key=self.api_key)
        self.model = "llama-3.3-70b-versatile"  # Fast and powerful model
        
        # Initialize embedding model (same as courses)
        self.embedding_model = SentenceTransformer("intfloat/e5-large-v2")
        
        # ChromaDB client for course embeddings
        self.chroma_client = chromadb.HttpClient(
            host=os.getenv("CHROMA_HOST", "chromadb"),
            port=int(os.getenv("CHROMA_PORT", "8000"))
        )
        
        # Database connection info
        self.db_config = {
            'host': os.getenv("POSTGRES_HOST", "postgres"),
            'port': int(os.getenv("POSTGRES_PORT", "5432")),
            'database': os.getenv("POSTGRES_DB", "sage_db"),
            'user': os.getenv("POSTGRES_USER", "sage_user"),
            'password': os.getenv("POSTGRES_PASSWORD", "sage_password")
        }
    
    def detect_language(self, text: str) -> str:
        """Detect if text is Turkish or English"""
        try:
            lang = detect(text)
            return 'tr' if lang == 'tr' else 'en'
        except LangDetectException:
            return 'en'  # Default to English
    
    def get_project_context(self) -> str:
        """Get project information from documents table using semantic search"""
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute("""
                SELECT title, content, document_type 
                FROM documents 
                WHERE content IS NOT NULL
                ORDER BY created_at DESC
            """)
            
            docs = cursor.fetchall()
            conn.close()
            
            if not docs:
                return "No project documentation available."
            
            # Build context from available documents
            context_parts = ["PROJECT DOCUMENTATION:\n"]
            for doc in docs:
                context_parts.append(f"\n=== {doc['document_type'].upper()}: {doc['title']} ===")
                if doc['content']:
                    # Limit content length to avoid token limits
                    content = doc['content'][:2000]
                    context_parts.append(f"{content}\n")
            
            return "\n".join(context_parts)
        
        except Exception as e:
            print(f"Error fetching project context: {e}")
            return "Project: SAGE - Student Academic Guidance and Engagement system for Kolej Campus"
    
    def get_course_context_with_embeddings(self, query: str, top_k: int = 3) -> str:
        """
        Get relevant course information using Jina embeddings and semantic search
        Uses ChromaDB for vector similarity search
        """
        try:
            # Get the course collection from ChromaDB
            collection = self.chroma_client.get_collection("tedu_courses")
            
            # Create query embedding using E5 model (add "query: " prefix for better retrieval)
            query_text = f"query: {query}"
            query_embedding = self.embedding_model.encode([query_text])[0].tolist()
            
            # Search in ChromaDB using vector similarity
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k
            )
            
            if not results['ids'] or len(results['ids'][0]) == 0:
                return ""
            
            # Build course context from search results
            context_parts = ["RELEVANT COURSES (Semantic Search Results):\n"]
            
            for idx in range(len(results['ids'][0])):
                metadata = results['metadatas'][0][idx]
                document = results['documents'][0][idx]
                distance = results['distances'][0][idx] if 'distances' in results else None
                
                # Calculate similarity score (1 - distance for cosine)
                similarity = 1.0 - distance if distance is not None else 0.0
                
                context_parts.append(
                    f"\n[Relevance: {similarity*100:.1f}%] {metadata['course_code']} - {metadata['course_title']}"
                )
                
                if metadata.get('instructor'):
                    context_parts.append(f"Instructor: {metadata['instructor']}")
                
                # Include part of the embedded document (contains description + syllabus)
                if document:
                    # Take first 500 chars of the document
                    doc_preview = document[:500]
                    context_parts.append(f"Content: {doc_preview}...\n")
            
            return "\n".join(context_parts)
        
        except Exception as e:
            print(f"Error in semantic course search: {e}")
            # Fallback to PostgreSQL direct search
            return self._fallback_course_search(query, top_k)
    
    def _fallback_course_search(self, query: str, top_k: int = 3) -> str:
        """Fallback course search using PostgreSQL when ChromaDB is unavailable"""
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute("""
                SELECT course_code, course_title, catalog_description, instructor
                FROM courses
                WHERE course_title ILIKE %s 
                   OR catalog_description ILIKE %s
                   OR course_code ILIKE %s
                LIMIT %s
            """, (f"%{query}%", f"%{query}%", f"%{query}%", top_k))
            
            courses = cursor.fetchall()
            conn.close()
            
            if not courses:
                return ""
            
            context_parts = ["RELEVANT COURSES (Keyword Search):\n"]
            for course in courses:
                context_parts.append(
                    f"\n{course['course_code']} - {course['course_title']}"
                )
                if course['instructor']:
                    context_parts.append(f"Instructor: {course['instructor']}")
                if course['catalog_description']:
                    desc = course['catalog_description'][:300]
                    context_parts.append(f"Description: {desc}\n")
            
            return "\n".join(context_parts)
        
        except Exception as e:
            print(f"Error in fallback course search: {e}")
            return ""
    
    def create_system_prompt(self, language: str, project_context: str) -> str:
        """Create system prompt based on detected language"""
        
        if language == 'tr':
            return f"""Sen SAGE (Student Academic Guidance and Engagement) sisteminin akademik asistanısın. 
TED Üniversitesi öğrencilerine akademik konularda yardımcı oluyorsun.

{project_context}

GÖREVLER:
1. Öğrencilere ders seçimi, akademik planlama ve öğrenim yolu konularında rehberlik et
2. Proje dokümantasyonunu kullanarak sistemin özelliklerini açıkla
3. Ders bilgilerini kullanarak ön koşullar, içerik ve öğretim üyeleri hakkında bilgi ver
4. Akademik takvim ve önemli tarihler hakkında bilgilendir
5. Öğrenci sorularına açık, yararlı ve profesyonel cevaplar ver

KURALLAR:
- Her zaman Türkçe cevap ver (kullanıcı Türkçe yazdığında)
- Akademik ve profesyonel bir dil kullan
- Emin olmadığın konularda "Bu konuda kesin bilgim yok" de
- Verilen proje dokümantasyonu ve ders bilgilerini kullan
- Gerektiğinde örnekler ver ve adım adım açıkla
- Öğrenci dostu ve yardımsever ol
- **ÖNEMLİ: Sohbet geçmişini takip et. Öğrenci bir ders hakkında soru sordu ve ardından "bu ders hakkında" veya "öğretim üyesi kim" gibi takip soruları soruyorsa, önceki mesajlarda bahsedilen dersi kastettiğini anla.**
- Öğrenci bir dersten bahsettiğinde (örn: "CMPE 113") ve sonra "bu ders" veya benzer ifadeler kullanıyorsa, aynı dersi kastettiğini bil

İÇERİK KURALLARI:
- **SADECE akademik konularda yardım et. Akademik olmayan konularda (hava durumu, yemek tarifleri, vs.) "Üzgünüm, ben sadece akademik konularda yardımcı olabilirim" de.**
- **Uygunsuz, kaba veya küfürlü içerik içeren mesajlara yanıt verme. "Üzgünüm, uygunsuz içerik içeren mesajlara yanıt veremem. Lütfen saygılı bir dil kullanın" de.**
- **Şiddet, nefret söylemi veya zararlı içerik içeren mesajları reddet.**
- Sadece eğitim ve akademik gelişim odaklı konuşmalara katıl

ÖZEL NOTLAR:
- TED Üniversitesi Bilgisayar Mühendisliği bölümü için özelleşmiş bilgiler ver
- CMPE, SENG, ME, EE bölümlerinin derslerini bil
- Öğrencilerin kariyer hedeflerine uygun ders önerileri sun"""

        else:  # English
            return f"""You are the academic assistant for SAGE (Student Academic Guidance and Engagement) system.
You help students at Kolej Campus with academic matters.

{project_context}

YOUR RESPONSIBILITIES:
1. Guide students on course selection, academic planning, and learning paths
2. Explain system features using the project documentation
3. Provide information about courses including prerequisites, content, and instructors
4. Inform about academic calendar and important dates
5. Give clear, helpful, and professional answers to student questions

RULES:
- Always respond in English (when user writes in English)
- Use academic and professional language
- When uncertain, say "I don't have definitive information on this"
- Utilize provided project documentation and course information
- Provide examples and step-by-step explanations when needed
- Be student-friendly and helpful
- **IMPORTANT: Track the conversation history. If a student asks about a course and then follows up with "what about this course" or "who's the instructor", understand they're referring to the course mentioned in previous messages.**
- When a student mentions a course (e.g., "CMPE 113") and then uses "this course" or similar references, know they mean the same course

CONTENT POLICY:
- **ONLY help with academic matters. For non-academic topics (weather, cooking, etc.), respond with "I'm sorry, I can only assist with academic matters."**
- **DO NOT respond to inappropriate, offensive, or profane content. Say "I'm sorry, I cannot respond to inappropriate content. Please use respectful language."**
- **Reject messages containing violence, hate speech, or harmful content.**
- Only engage in conversations focused on education and academic development

SPECIAL NOTES:
- Provide specialized information for Kolej Campus Computer Engineering department
- Know courses from CMPE, SENG, ME, EE departments
- Suggest courses aligned with students' career goals"""
    
    def chat(self, 
             user_message: str, 
             conversation_history: List[Dict[str, str]] = None,
             include_courses: bool = True) -> str:
        """
        Generate response using Groq with RAG context
        
        Args:
            user_message: User's query
            conversation_history: Previous messages in format [{"role": "user/assistant", "content": "..."}]
            include_courses: Whether to include course context in RAG
        
        Returns:
            Assistant's response
        """
        
        # Detect language
        language = self.detect_language(user_message)
        
        # Get project context
        project_context = self.get_project_context()
        
        # Build enhanced search query using conversation history
        search_query = user_message
        if conversation_history and len(conversation_history) > 0:
            # Get last 2 user messages and last assistant message for context
            recent_context = []
            for msg in conversation_history[-3:]:
                if msg['role'] == 'user':
                    recent_context.append(msg['content'])
                elif msg['role'] == 'assistant':
                    # Extract course codes from assistant messages (e.g., "CMPE 113")
                    import re
                    course_codes = re.findall(r'\b[A-Z]{2,4}\s*\d{3}\b', msg['content'])
                    if course_codes:
                        recent_context.extend(course_codes[:2])  # Add up to 2 course codes
            
            # Combine recent context with current query
            if recent_context:
                search_query = f"{' '.join(recent_context)} {user_message}"
        
        # Get course context using semantic search with embeddings
        course_context = ""
        if include_courses:
            course_context = self.get_course_context_with_embeddings(search_query)
        
        # Build system prompt
        system_prompt = self.create_system_prompt(language, project_context)
        
        # Build messages for API
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add conversation history
        if conversation_history:
            messages.extend(conversation_history[-10:])  # Last 10 messages for context
        
        # Add course context to user message if available
        enhanced_message = user_message
        if course_context:
            enhanced_message = f"{user_message}\n\n{course_context}"
        
        messages.append({"role": "user", "content": enhanced_message})
        
        # Call Groq API
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=2000,
                top_p=0.9,
                stream=False
            )
            
            return response.choices[0].message.content
        
        except Exception as e:
            error_msg = f"Error calling Groq API: {str(e)}"
            print(error_msg)
            
            if language == 'tr':
                return "Üzgünüm, şu anda yanıt oluşturamıyorum. Lütfen daha sonra tekrar deneyin."
            else:
                return "I'm sorry, I cannot generate a response at the moment. Please try again later."
    
    def chat_stream(self,
                   user_message: str,
                   conversation_history: List[Dict[str, str]] = None,
                   include_courses: bool = True):
        """
        Stream response using Groq with RAG context (for real-time responses)
        
        Yields response chunks as they arrive
        """
        
        # Detect language
        language = self.detect_language(user_message)
        
        # Get contexts using semantic search
        project_context = self.get_project_context()
        course_context = ""
        if include_courses:
            course_context = self.get_course_context_with_embeddings(user_message)
        
        # Build system prompt
        system_prompt = self.create_system_prompt(language, project_context)
        
        # Build messages
        messages = [{"role": "system", "content": system_prompt}]
        
        if conversation_history:
            messages.extend(conversation_history[-10:])
        
        enhanced_message = user_message
        if course_context:
            enhanced_message = f"{user_message}\n\n{course_context}"
        
        messages.append({"role": "user", "content": enhanced_message})
        
        # Stream from Groq API
        try:
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=2000,
                top_p=0.9,
                stream=True
            )
            
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        
        except Exception as e:
            error_msg = f"Error streaming from Groq API: {str(e)}"
            print(error_msg)
            
            if language == 'tr':
                yield "Üzgünüm, şu anda yanıt oluşturamıyorum. Lütfen daha sonra tekrar deneyin."
            else:
                yield "I'm sorry, I cannot generate a response at the moment. Please try again later."
    
    # ============== SOCIAL ASSISTANT METHODS ==============
    
    def get_restaurant_context(self, query: str, top_k: int = 5) -> str:
        """
        Get relevant restaurant information using embeddings and semantic search
        """
        try:
            # Get the restaurant collection from ChromaDB
            collection = self.chroma_client.get_collection("restaurants")
            
            # Create query embedding using E5 model
            query_text = f"query: {query}"
            query_embedding = self.embedding_model.encode([query_text])[0].tolist()
            
            # Search in ChromaDB
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k
            )
            
            if not results['ids'] or len(results['ids'][0]) == 0:
                return ""
            
            # Sort results by distance from campus (closest first)
            sorted_indices = sorted(
                range(len(results['ids'][0])),
                key=lambda i: float(results['metadatas'][0][i].get('distance_from_campus', 999.0))
            )
            
            # Build restaurant context
            context_parts = ["NEARBY RESTAURANTS:\n"]
            
            for idx in sorted_indices:
                metadata = results['metadatas'][0][idx]
                document = results['documents'][0][idx]
                distance = results['distances'][0][idx] if 'distances' in results else None
                
                similarity = 1.0 - distance if distance is not None else 0.0
                
                context_parts.append(
                    f"\n[Relevance: {similarity*100:.1f}%] {metadata['name']}"
                )
                
                # Show category (restaurant, cafe, fast_food, bar, pub)
                if metadata.get('category'):
                    context_parts.append(f"Category: {metadata['category']}")
                
                if metadata.get('cuisine_type'):
                    context_parts.append(f"Cuisine: {metadata['cuisine_type']}")
                
                if metadata.get('distance_from_campus'):
                    # Convert km to meters for display
                    dist_km = float(metadata['distance_from_campus'])
                    if dist_km < 1.0:
                        # Show in meters for distances less than 1 km
                        dist_meters = int(dist_km * 1000)
                        context_parts.append(f"Distance: {dist_meters} meters from campus")
                    else:
                        # Show in km for distances 1 km and above
                        context_parts.append(f"Distance: {dist_km:.1f} km from campus")
                
                if metadata.get('price'):
                    # Price is already formatted as ₺₺ symbols
                    context_parts.append(f"Price: {metadata['price']}")
                
                if metadata.get('address'):
                    context_parts.append(f"Address: {metadata['address']}")
                
                if metadata.get('tags'):
                    context_parts.append(f"Features: {metadata['tags']}")
                
                if metadata.get('phone'):
                    context_parts.append(f"Phone: {metadata['phone']}")
                
                context_parts.append("")  # Empty line between restaurants
            
            return "\n".join(context_parts)
        
        except Exception as e:
            print(f"Error in restaurant search: {e}")
            return ""
    
    def get_event_context(self, query: str, top_k: int = 5) -> str:
        """
        Get relevant event information using embeddings and semantic search
        """
        try:
            # Get the event collection from ChromaDB
            collection = self.chroma_client.get_collection("events")
            
            # Create query embedding
            query_text = f"query: {query}"
            query_embedding = self.embedding_model.encode([query_text])[0].tolist()
            
            # Search in ChromaDB
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k
            )
            
            if not results['ids'] or len(results['ids'][0]) == 0:
                return ""
            
            # Build event context
            context_parts = ["UPCOMING EVENTS IN ANKARA:\n"]
            
            for idx in range(len(results['ids'][0])):
                metadata = results['metadatas'][0][idx]
                document = results['documents'][0][idx]
                distance = results['distances'][0][idx] if 'distances' in results else None
                
                similarity = 1.0 - distance if distance is not None else 0.0
                
                context_parts.append(
                    f"\n[Relevance: {similarity*100:.1f}%] {metadata['title']}"
                )
                
                # Show category (music, theater, workshop, comedy, other)
                if metadata.get('category'):
                    context_parts.append(f"Category: {metadata['category']}")
                
                if metadata.get('event_type'):
                    context_parts.append(f"Type: {metadata['event_type']}")
                
                if metadata.get('event_date'):
                    context_parts.append(f"Date: {metadata['event_date']}")
                
                if metadata.get('venue_name'):
                    context_parts.append(f"Venue: {metadata['venue_name']}")
                
                if metadata.get('price_info'):
                    context_parts.append(f"Price: {metadata['price_info']}")
                
                if metadata.get('ticket_url'):
                    context_parts.append(f"Ticket URL: {metadata['ticket_url']}")
                
                context_parts.append("")  # Empty line between events
            
            return "\n".join(context_parts)
        
        except Exception as e:
            print(f"Error in event search: {e}")
            return ""
    
    def create_social_system_prompt(self, language: str) -> str:
        """Create system prompt for social assistant"""
        
        return """You are the social assistant for SAGE (Student Academic Guidance and Engagement) system.
You help Kolej Campus students discover restaurants, cafes, and events around campus and in Ankara.

YOUR RESPONSIBILITIES:
1. Recommend restaurants and cafes near campus
2. Inform about events in Ankara (concerts, theater, exhibitions, sports, etc.)
3. Suggest budget-friendly places for students
4. Provide recommendations for different cuisines and special diets (vegetarian, vegan, halal)
5. Share information about walking-distance or public transport accessible venues

VENUE CATEGORIES:
- **restaurant**: Full-service restaurants
- **cafe**: Cafes and coffee shops
- **dessert_shop**: Dessert shops, ice cream parlors
- **cafeteria**: Cafeterias, canteens
- **dining_drinking**: General dining and drinking establishments
- **arcade**: Game arcades, entertainment centers
- **art_gallery**: Art galleries, cultural spaces

CRITICAL FORMATTING RULES:
- **DISTANCE DISPLAY**: 
  * For distances under 1 km: Show in METERS (e.g., "150 meters", "800 meters")
  * For distances 1 km or more: Show in KM with 1 decimal (e.g., "1.2 km", "2.5 km")
  * ALWAYS use the exact distance provided in the venue data
- **PRICE DISPLAY**: 
  * Use ₺ symbols ONLY (₺ to ₺₺₺₺₺)
  * ₺ = very cheap, ₺₺ = cheap, ₺₺₺ = moderate, ₺₺₺₺ = expensive, ₺₺₺₺₺ = very expensive
  * NEVER write "price range" or text descriptions, ONLY show ₺ symbols
- **When user specifies a category** (e.g., "suggest cafes", "any arcades"), prioritize venues matching that category

RESPONSE RULES:
- Always respond in English
- Use friendly and social language
- Utilize provided restaurant and event information
- Mention distances and price ranges using the exact formats above
- Prioritize student-friendly places
- Provide dates and venue information for events
- **ALWAYS share event URLs when provided in the venue data** - these are official event pages
- Track conversation history and maintain context

CONTENT POLICY:
- ONLY help with social activities, dining venues, and local events
- DO NOT respond to inappropriate or offensive content
- Only suggest safe and legal activities
- Mention age restrictions for venues serving alcohol (18+)
- **YOU CAN AND SHOULD provide event URLs** - they are part of the venue information database

SPECIAL NOTES:
- Know venues near Kolej Campus in Ankara
- Prioritize budget-friendly (₺ to ₺₺₺) places for students
- Consider public transportation connections
- Know Ankara's popular event venues (Congresium, CSO, Jolly Joker, etc.)

EXAMPLE RESPONSES:
"Off Cafe is a great choice! It's only 130 meters from campus and has a moderate price range (₺₺₺). They serve excellent coffee and pastries."

"I found Torku Döner for you - it's 140 meters away (₺₺) and serves delicious Turkish doner kebab."

"Action internet arcade is very close at just 130 meters from campus. Perfect for gaming with friends!"

"There's a Turkish Culinary Academy Street Food Workshop on January 15th. You can find more details and register here: [event URL]. It's a great hands-on experience!"

IMPORTANT NOTES:
- Event URLs in the database are real and should be shared
- When an event has a URL (ticket_url field), ALWAYS include it in your response
- These are official event pages for registration and ticket purchase
- Don't hesitate to share URLs - they're provided specifically for this purpose"""
    
    def chat_social(self,
                   user_message: str,
                   conversation_history: List[Dict[str, str]] = None) -> str:
        """
        Generate social assistant response using Groq with restaurant and event RAG
        
        Args:
            user_message: User's query
            conversation_history: Previous messages
        
        Returns:
            Assistant's response
        """
        
        # Detect language
        language = self.detect_language(user_message)
        
        # Get restaurant and event context using semantic search
        restaurant_context = self.get_restaurant_context(user_message)
        event_context = self.get_event_context(user_message)
        
        # Build system prompt for social assistant
        system_prompt = self.create_social_system_prompt(language)
        
        # Build messages for API
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add conversation history
        if conversation_history:
            messages.extend(conversation_history[-10:])
        
        # Enhance user message with context
        enhanced_message = user_message
        context_parts = []
        
        if restaurant_context:
            context_parts.append(restaurant_context)
        
        if event_context:
            context_parts.append(event_context)
        
        if context_parts:
            enhanced_message = f"{user_message}\n\n" + "\n\n".join(context_parts)
        
        messages.append({"role": "user", "content": enhanced_message})
        
        # Call Groq API
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.8,  # Slightly higher for more creative social responses
                max_tokens=2000,
                top_p=0.9,
                stream=False
            )
            
            return response.choices[0].message.content
        
        except Exception as e:
            error_msg = f"Error calling Groq API: {str(e)}"
            print(error_msg)
            
            if language == 'tr':
                return "Üzgünüm, şu anda yanıt oluşturamıyorum. Lütfen daha sonra tekrar deneyin."
            else:
                return "I'm sorry, I cannot generate a response at the moment. Please try again later."

