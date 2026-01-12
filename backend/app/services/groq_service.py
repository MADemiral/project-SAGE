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
                temperature=0.1,
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
    
    def get_restaurant_context(self, query: str, top_k: int = 10) -> str:
        """
        Get relevant restaurant information using embeddings and semantic search
        Searches both dining_places and entertainment_places collections
        """
        try:
            all_results = []
            
            # Search dining places collection
            try:
                dining_collection = self.chroma_client.get_collection("dining_places")
                query_text = f"query: {query}"
                query_embedding = self.embedding_model.encode([query_text])[0].tolist()
                
                dining_results = dining_collection.query(
                    query_embeddings=[query_embedding],
                    n_results=top_k
                )
                
                if dining_results['ids'] and len(dining_results['ids'][0]) > 0:
                    for idx in range(len(dining_results['ids'][0])):
                        all_results.append({
                            'metadata': dining_results['metadatas'][0][idx],
                            'document': dining_results['documents'][0][idx],
                            'distance': dining_results['distances'][0][idx] if 'distances' in dining_results else None
                        })
            except Exception as e:
                print(f"Error searching dining_places: {e}")
            
            # Search entertainment places collection
            try:
                entertainment_collection = self.chroma_client.get_collection("entertainment_places")
                query_text = f"query: {query}"
                query_embedding = self.embedding_model.encode([query_text])[0].tolist()
                
                entertainment_results = entertainment_collection.query(
                    query_embeddings=[query_embedding],
                    n_results=top_k
                )
                
                if entertainment_results['ids'] and len(entertainment_results['ids'][0]) > 0:
                    for idx in range(len(entertainment_results['ids'][0])):
                        all_results.append({
                            'metadata': entertainment_results['metadatas'][0][idx],
                            'document': entertainment_results['documents'][0][idx],
                            'distance': entertainment_results['distances'][0][idx] if 'distances' in entertainment_results else None
                        })
            except Exception as e:
                print(f"Error searching entertainment_places: {e}")
            
            if not all_results:
                return ""
            
            if not all_results:
                return ""
            
            # Sort all results by distance from campus (closest first)
            sorted_results = sorted(
                all_results,
                key=lambda r: float(r['metadata'].get('distance_from_campus', 999.0))
            )
            
            # Build restaurant context
            context_parts = ["NEARBY VENUES (from database):\n"]
            
            for result in sorted_results[:top_k]:  # Limit to top_k results
                metadata = result['metadata']
                document = result['document']
                distance = result['distance']
                
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

        # English prompt (strict: DO NOT hallucinate venues)
        en_prompt = """You are the social assistant for SAGE (Student Academic Guidance and Engagement) system.
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
- **PRICE DISPLAY FOR VENUES**: 
  * Use ₺ symbols ONLY (₺ to ₺₺₺₺₺)
  * ₺ = very cheap, ₺₺ = cheap, ₺₺₺ = moderate, ₺₺₺₺ = expensive, ₺₺₺₺₺ = very expensive
  * NEVER write "price range" or text descriptions, ONLY show ₺ symbols
- **PRICE DISPLAY FOR EVENTS**: 
  * Show the actual ticket price in Turkish Lira (e.g., "400 TL", "2200 TL")
  * Use the price_info field which includes currency
- **When user specifies a category** (e.g., "suggest cafes", "any arcades"), prioritize venues matching that category

RESPONSE RULES:
- Respond in Turkish if the user asked in Turkish, otherwise respond in English
- Use friendly and social language
- **CRITICAL: ONLY recommend venues that are provided in the CONTEXT SECTIONS below**
- **NEVER make up or hallucinate venue names, addresses, distances, prices, phone numbers, or URLs**
- **If you don't have venues matching the request, respond exactly:** "I don't have any [category] venues in my database near campus. My data might be limited."
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
- **YOU MUST NOT invent or suggest venues that are not in the provided context data**

SPECIAL NOTES:
- Know venues near Kolej Campus in Ankara
- Prioritize budget-friendly (₺ to ₺₺₺) places for students
- Consider public transportation connections
- Know Ankara's popular event venues (Congresium, CSO, Jolly Joker, etc.)

CRITICAL INSTRUCTIONS - READ CAREFULLY:
1. **ONLY use venues from the "NEARBY RESTAURANTS" or "UPCOMING EVENTS" sections provided in the context**
2. **If the context is empty or doesn't contain relevant venues, respond with**: "I don't have any [category] venues in my database near campus. My data might be limited."
3. **NEVER suggest venues like "Sözen Cafe", "Campus Cafe", or any generic names not in the context**
4. **Always check the context data before making recommendations**
5. **Use exact venue names, distances, and details from the context data**
6. Event URLs in the database are real and should be shared
7. When an event has a URL (ticket_url field), ALWAYS include it in your response
8. These are official event pages for registration and ticket purchase
9. Don't hesitate to share URLs - they're provided specifically for this purpose

EXAMPLE OF CORRECT BEHAVIOR:
User: "Any cafes near campus?"
If context shows "Off Cafe - 130 meters" → Recommend Off Cafe
If context is empty → Say "I don't have any cafes in my database near campus"

EXAMPLE OF INCORRECT BEHAVIOR (DON'T DO THIS):
User: "Any cafes near campus?"
Response: "Try Sözen Cafe or Campus Cafe" ← WRONG! These are not in the database!"""

        
        tr_prompt = """SAGE (Student Academic Guidance and Engagement) sisteminin sosyal asistanısın.
Kolej Kampüsü öğrencilerine kampüs ve Ankara çevresindeki restoranlar, kafeler ve etkinlikleri keşfetmelerinde yardımcı olursun.

GÖREVLERİN:
1. Kampüs yakınındaki restoran ve kafeleri öner
2. Ankara'daki etkinlikler hakkında bilgi ver (konser, tiyatro, sergi, spor vb.)
3. Öğrenciler için bütçe dostu mekanlar öner
4. Farklı mutfaklar ve özel diyetler (vejetaryen, vegan, helal) için önerilerde bulun
5. Yürüme mesafesi ve toplu taşıma ile erişilebilir mekanları paylaş

MEKAN KATEGORİLERİ:
- **restaurant**: Restoranlar
- **cafe**: Kafeler ve kahve dükkanları
- **dessert_shop**: Tatlıcılar, dondurmacılar
- **cafeteria**: Kantinler, yemekhaneler
- **dining_drinking**: Genel yeme-içme mekanları
- **arcade**: Oyun salonları, eğlence merkezleri
- **art_gallery**: Sanat galerileri ve kültürel alanlar

Kritik Format Kuralları:
- **MESAFE GÖSTERİMİ**: 
  * 1 km altındaki mesafeler METRE olarak gösterilsin (örn. "150 meters", "800 meters")
  * 1 km ve üzeri mesafeler 1 ondalıklı KM ile gösterilsin (örn. "1.2 km", "2.5 km")
  * MEKAN verisinde verilen kesin mesafeyi kullan
- **MEKAN FİYAT GÖSTERİMİ**:
  * Sadece ₺ sembolünü kullan (₺ ile ₺₺₺₺₺ arası)
  * ₺ = çok ucuz, ₺₺ = ucuz, ₺₺₺ = orta, ₺₺₺₺ = pahalı, ₺₺₺₺₺ = çok pahalı
  * "price range" ya da metinsel açıklama yazma, sadece ₺ sembollerini kullan
- **ETKİNLİK FİYAT GÖSTERİMİ**:
  * Bilet fiyatını Türk Lirası olarak göster (örn. "400 TL", "2200 TL")
  * Fiyat bilgisi için price_info alanını kullan
- **Kullanıcı kategori belirttiyse** (örn: "kafe öner"), o kategoriye uygun mekanları önceliklendir

YANIT KURALLARI:
- Kullanıcı Türkçe yazdıysa Türkçe, aksi halde İngilizce cevap ver
- Dostane ve sosyal bir dil kullan
- **KRİTİK: Yalnızca aşağıda verilecek BAĞLAM verilerindeki mekanları öner**
- **MEKAN İSİMLERİNİ, ADRESLERİ VE DETAYLARI UYDURMA**
- **Veritabanımda bu kategoriye ait mekan bulunmuyor.** mesajını vererek bağlam yokluğunu belirt
- Mesafe ve fiyat formatlarını yukarıdaki kurallara göre göster
- Öğrenci dostu mekanları önceliklendir
- Etkinlikler için tarih ve mekan bilgisini ver
- **Etkinlik URL'leri varsa her zaman paylaş**
- Konuşma geçmişini takip et

İÇERİK POLİTİKASI:
- Sadece sosyal aktiviteler, yemek mekanları ve yerel etkinlikler ile ilgili yardımcı ol
- Uygunsuz ya da saldırgan içeriklere cevap verme
- Sadece güvenli ve yasal etkinlikleri öner
- Alkol servisi olan mekanlarda yaş kısıtlamasını belirt (18+)
- **Etkinlik URL'leri verilebilir ve paylaşılmalıdır**
- **Bağlamda olmayan mekanları ASLA UYDURMA**

KRİTİK TALİMATLAR - DİKKATLE OKU:
1. **Bağlamda verilen "NEARBY RESTAURANTS" veya "UPCOMING EVENTS" bölümlerinden başkasını kullanma**
2. **Bağlam boşsa veya uygun mekan yoksa şu yanıtı ver:** "Veritabanımda bu kategoriye ait mekan bulunmuyor." (Türkçe)
3. **Bağlamda olmayan mekanları, mesafeleri, fiyatları, adresleri, telefonları veya URL'leri ASLA UYDURMA**
4. **Tavsiyeden önce bağlam verilerini kontrol et**
5. **Mekan isimleri, mesafeler ve diğer detaylar bağlamdaki gibi gösterilsin**
6. Etkinlik URL'leri varsa mutlaka paylaş

ÖRNEK DOĞRU DAVRANIŞ:
Kullanıcı: "Kampüs yakınında kafe var mı?"
Bağlamta "Off Cafe - 130 meters" varsa → Off Cafe'yi öner
Bağlam boşsa → "Veritabanımda bu kategoriye ait mekan bulunmuyor." Cevabı ver

ÖRNEK YANLIŞ DAVRANIŞ (YAPMA):
Kullanıcı: "Kampüs yakınında kafe var mı?"
Yanıt: "Sözen Cafe ya da Campus Cafe'yi dene" ← YANLIŞ! Bunlar veritabanında olmayabilir"""

        # Return Turkish prompt if language is 'tr', otherwise English
        return tr_prompt if language == 'tr' else en_prompt"
    
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
        
        # Enforce response language explicitly
        lang_label = "Turkish" if language == 'tr' else "English"
        lang_instruction = f"STRICTLY: Respond only in {lang_label}. Do not use other languages or translate content."
        
        # Build messages for API including the language enforcement system message
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "system", "content": lang_instruction}
        ]
        
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
                temperature=0.5,  # Slightly higher for more creative social responses
                max_tokens=2000,
                top_p=0.9,
                stream=False
            )
            
            resp = response.choices[0].message.content
            resp_lang = self.detect_language(resp)
            expected_lang = 'tr' if language == 'tr' else 'en'
            
            # If response language does not match expected, retry once with stricter instruction and low temperature
            if resp_lang != expected_lang:
                print(f"Language mismatch detected in social assistant response: expected={expected_lang}, got={resp_lang}. Retrying once with stricter language instruction.")
                retry_instruction = f"URGENT: Reply only in {lang_label}. Do NOT translate or answer in any other language."
                # Insert urgent instruction after system prompt
                messages_retry = [
                    {"role": "system", "content": system_prompt},
                    {"role": "system", "content": retry_instruction}
                ]
                if conversation_history:
                    messages_retry.extend(conversation_history[-10:])
                messages_retry.append({"role": "user", "content": enhanced_message})
                
                retry = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages_retry,
                    temperature=0.0,
                    max_tokens=2000,
                    top_p=0.9,
                    stream=False
                )
                resp = retry.choices[0].message.content
                resp_lang = self.detect_language(resp)
                
                # If still mismatch, return a clear fallback to the user
                if resp_lang != expected_lang:
                    print(f"Retry failed: expected={expected_lang}, got={resp_lang}. Returning fallback message.")
                    if language == 'tr':
                        return "Üzgünüm, yanıtı Türkçe oluşturamadım. Lütfen tekrar deneyin."
                    else:
                        return "Sorry, I couldn't produce a response in English. Please try again."
            
            return resp
        
        except Exception as e:
            error_msg = f"Error calling Groq API: {str(e)}"
            print(error_msg)
            
            if language == 'tr':
                return "Üzgünüm, şu anda yanıt oluşturamıyorum. Lütfen daha sonra tekrar deneyin."
            else:
                return "I'm sorry, I cannot generate a response at the moment. Please try again later."

