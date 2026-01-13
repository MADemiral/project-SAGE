"""
IMAP Email Service - Simple email reading without OAuth
Works with any email provider that supports IMAP
"""
import imaplib
import email
from email.header import decode_header
from typing import List, Dict, Any
from datetime import datetime, timedelta
import json
from groq import Groq
import os


class IMAPEmailService:
    """Simple IMAP-based email service"""
    
    # Gmail IMAP Settings
    IMAP_SERVER = "imap.gmail.com"
    IMAP_PORT = 993
    
    def __init__(self):
        self.connection = None
        self.email_address = None
        self.is_connected = False
    
    def connect(self, email_address: str, password: str) -> bool:
        """
        Connect to email server via IMAP
        """
        try:
            # Disconnect any existing connection
            if self.connection:
                try:
                    self.connection.logout()
                except:
                    pass
            
            # Connect to IMAP server with timeout
            print(f"Attempting IMAP connection to {self.IMAP_SERVER}:{self.IMAP_PORT}")
            self.connection = imaplib.IMAP4_SSL(self.IMAP_SERVER, self.IMAP_PORT)
            
            # Set a longer timeout (default is too short)
            self.connection.sock.settimeout(60)
            
            print(f"SSL connection established, attempting login for {email_address}")
            
            # Login
            self.connection.login(email_address, password)
            print(f"✓ Login successful for {email_address}")
            
            self.email_address = email_address
            self.is_connected = True
            
            return True
        except imaplib.IMAP4.error as e:
            error_msg = str(e)
            print(f"✗ IMAP4.error: {error_msg}")
            if 'authentication failed' in error_msg.lower() or 'login failed' in error_msg.lower():
                raise Exception(f"Authentication failed. Please check:\n1. Email address is correct\n2. Using App Password (not regular password)\n3. IMAP is enabled in Gmail settings\nError: {error_msg}")
            else:
                raise Exception(f"IMAP error: {error_msg}")
        except Exception as e:
            error_msg = str(e)
            print(f"✗ Exception during IMAP connection: {error_msg}")
            if "EOF" in error_msg:
                raise Exception(f"Connection closed by server. Please check:\n1. Your App Password is correct and not expired\n2. IMAP access is enabled in Gmail\n3. No firewall blocking IMAP (port 993)")
            raise Exception(f"IMAP connection failed: {error_msg}")
    
    def disconnect(self):
        """Close IMAP connection"""
        if self.connection:
            try:
                self.connection.close()
                self.connection.logout()
            except:
                pass
            self.is_connected = False
    
    def fetch_emails(self, days: int = 30, max_results: int = 50) -> List[Dict[str, Any]]:
        """
        Fetch emails from inbox
        """
        if not self.is_connected:
            raise Exception("Not connected. Please login first.")
        
        try:
            # Reconnect if connection is stale
            try:
                self.connection.noop()  # Test connection
            except:
                print("⚠️ Connection stale, reconnecting...")
                raise Exception("Connection expired. Please login again.")
            
            # Select inbox - make sure we're reading from INBOX only
            status, messages = self.connection.select("INBOX")
            print(f"📬 Selected INBOX: {status}, {messages[0].decode()} messages total")
            
            # Calculate date for search
            since_date = (datetime.now() - timedelta(days=days)).strftime("%d-%b-%Y")
            print(f"🔍 Searching for emails since {since_date}")
            
            # Search for emails since date in INBOX
            status, messages = self.connection.search(None, f'SINCE {since_date}')
            
            if status != "OK":
                raise Exception("Failed to search emails")
            
            # Get email IDs
            email_ids = messages[0].split()
            print(f"📧 Found {len(email_ids)} emails in INBOX since {since_date}")
            email_ids = email_ids[-max_results:]  # Get last N emails
            print(f"📤 Fetching last {len(email_ids)} emails")
            
            emails = []
            
            for email_id in email_ids:
                try:
                    # Fetch email
                    status, msg_data = self.connection.fetch(email_id, "(RFC822)")
                    
                    if status != "OK":
                        continue
                    
                    # Parse email
                    raw_email = msg_data[0][1]
                    msg = email.message_from_bytes(raw_email)
                    
                    # Decode subject
                    subject = self._decode_header(msg.get("Subject", ""))
                    
                    # Get from address
                    from_header = msg.get("From", "")
                    
                    # Get date
                    date_str = msg.get("Date", "")
                    
                    # Get body
                    body = self._get_email_body(msg)
                    
                    email_data = {
                        "id": email_id.decode(),
                        "subject": subject,
                        "from": from_header,
                        "date": date_str,
                        "body": body[:1000],  # First 1000 chars
                        "full_body": body
                    }
                    
                    print(f"  📨 {subject[:50]}... from {from_header[:30]}")
                    emails.append(email_data)
                    
                except Exception as e:
                    print(f"Error parsing email {email_id}: {e}")
                    continue
            
            print(f"✅ Successfully fetched {len(emails)} emails from INBOX")
            return emails
            
        except Exception as e:
            error_msg = str(e)
            if "EOF" in error_msg or "socket" in error_msg.lower():
                raise Exception("Connection lost. Please login again with your Gmail credentials.")
            raise Exception(f"Failed to fetch emails: {error_msg}")
    
    def _decode_header(self, header):
        """Decode email header"""
        if not header:
            return ""
        
        decoded = decode_header(header)
        result = ""
        
        for part, encoding in decoded:
            if isinstance(part, bytes):
                result += part.decode(encoding or "utf-8", errors="ignore")
            else:
                result += part
        
        return result
    
    def _get_email_body(self, msg):
        """Extract email body"""
        body = ""
        
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))
                
                if content_type == "text/plain" and "attachment" not in content_disposition:
                    try:
                        body = part.get_payload(decode=True).decode("utf-8", errors="ignore")
                        break
                    except:
                        pass
        else:
            try:
                body = msg.get_payload(decode=True).decode("utf-8", errors="ignore")
            except:
                body = str(msg.get_payload())
        
        return body
    
    def extract_events_with_llm(self, emails: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Use Groq LLM to extract calendar events from emails
        Processes in batches to avoid token limits
        Includes retry logic for rate limiting
        """
        groq_api_key = os.getenv("GROQ_API_KEY")
        if not groq_api_key:
            raise Exception("GROQ_API_KEY not set")
        
        client = Groq(api_key=groq_api_key)
        
        # Use smaller, more token-efficient model
        model = "llama-3.1-8b-instant"  # Much more efficient, still capable
        
        # Prepare emails for LLM
        email_texts = []
        for e in emails:
            # Use full_body instead of truncated body for better extraction
            body_text = e.get('full_body', e.get('body', ''))
            email_texts.append(f"Subject: {e['subject']}\nFrom: {e['from']}\nDate: {e['date']}\nBody: {body_text[:800]}")  # Reduced from 1500 to 800 chars
        
        print(f"📧 Processing {len(email_texts)} emails in batches")
        
        system_prompt = """You are an AI assistant specialized in extracting calendar events from student emails.

CRITICAL: You MUST respond with ONLY valid JSON array format. No other text, no explanations, just the JSON array.

Focus on extracting these types of events:
- Academic Events: Classes, lectures, exams, assignments, project deadlines, office hours, academic meetings (EXTRACT COURSE CODES like CMPE101, CS202, etc.)
- Social Events: Club meetings, social gatherings, parties, networking events, hangouts
- Student Activities: Workshops, seminars, competitions, sports events, cultural events
- Administrative: Registration deadlines, payment due dates, important announcements
- Career Events: Job fairs, interviews, career workshops, internship opportunities

RESPONSE FORMAT - Return ONLY this JSON structure, nothing else:
[
  {
    "title": "Clear event title with course code if academic",
    "description": "Detailed description",
    "event_date": "2026-01-15 14:00",
    "end_date": "2026-01-15 16:00",
    "location": "Physical location or online link",
    "event_type": "academic",
    "priority": "high",
    "source": "email",
    "organizer": "Who is organizing the event",
    "requirements": "Course code like CMPE101 if academic, or any prerequisites"
  }
]

CRITICAL TIME EXTRACTION RULES:
1. Return ONLY the JSON array, no markdown, no code blocks, no extra text
2. If no events found, return: []
3. Extract ALL relevant events from the emails
4. For ACADEMIC events, extract course codes (CMPE101, CS202, EE301, etc.) and include in requirements field
5. Use event_type: academic, social, student_activity, career, administrative, meeting, or deadline
6. Use priority: high (exams/deadlines), medium (meetings), low (social)
7. DATE AND TIME FORMAT:
   - MUST use 24-hour format: HH:MM (00:00 to 23:59)
   - Examples: "14:00" for 2 PM, "09:30" for 9:30 AM, "16:45" for 4:45 PM
   - Convert AM/PM times: "2:00 PM" becomes "14:00", "8:30 AM" becomes "08:30"
   - Full format: "YYYY-MM-DD HH:MM" like "2026-01-15 14:00"
8. TIME CONVERSION GUIDE:
   - 12:00 AM (midnight) = 00:00
   - 1:00 AM = 01:00, 2:00 AM = 02:00, ..., 11:00 AM = 11:00
   - 12:00 PM (noon) = 12:00
   - 1:00 PM = 13:00, 2:00 PM = 14:00, 3:00 PM = 15:00, 4:00 PM = 16:00
   - 5:00 PM = 17:00, 6:00 PM = 18:00, 7:00 PM = 19:00, 8:00 PM = 20:00
   - 9:00 PM = 21:00, 10:00 PM = 22:00, 11:00 PM = 23:00
9. If time not mentioned, use 09:00 for morning events or 14:00 for afternoon events
10. For end_date, if duration given, calculate: start time + duration
11. Only extract FUTURE events (after today)
12. Skip events with vague dates unless specific date given"""
        
        all_events = []
        batch_size = 5  # Reduced from 10 to 5 emails per batch to save tokens
        total_batches = (len(email_texts) + batch_size - 1) // batch_size
        
        print(f"🔄 Will process {total_batches} batches of up to {batch_size} emails each")
        
        try:
            for batch_num in range(total_batches):
                start_idx = batch_num * batch_size
                end_idx = min(start_idx + batch_size, len(email_texts))
                batch_emails = email_texts[start_idx:end_idx]
                
                combined_emails = "\n\n---\n\n".join(batch_emails)
                print(f"📦 Batch {batch_num + 1}/{total_batches}: Processing emails {start_idx + 1}-{end_idx} ({len(combined_emails)} chars)")
                
                # Retry logic for rate limiting
                max_retries = 3
                retry_count = 0
                response = None
                
                while retry_count < max_retries:
                    try:
                        response = client.chat.completions.create(
                            model=model,
                            messages=[
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": f"Extract calendar events from these emails:\n\n{combined_emails}"}
                            ],
                            temperature=0.2,
                            max_tokens=2000  # Reduced from 3000
                        )
                        break  # Success, exit retry loop
                    except Exception as api_error:
                        error_str = str(api_error)
                        if "rate_limit_exceeded" in error_str or "429" in error_str:
                            # Extract wait time from error message
                            import re
                            wait_match = re.search(r'try again in (\d+)m', error_str)
                            if wait_match:
                                wait_minutes = int(wait_match.group(1))
                                wait_seconds = wait_minutes * 60
                                print(f"  ⏳ Rate limit hit. Waiting {wait_minutes} minutes ({wait_seconds}s)...")
                                import time
                                time.sleep(min(wait_seconds, 120))  # Cap at 2 minutes max
                                retry_count += 1
                            else:
                                # If can't parse wait time, wait 60 seconds
                                print(f"  ⏳ Rate limit hit. Waiting 60 seconds...")
                                import time
                                time.sleep(60)
                                retry_count += 1
                        else:
                            # Different error, don't retry
                            raise api_error
                
                if response is None:
                    print(f"  ❌ Failed to get response after {max_retries} retries")
                    continue  # Skip this batch
                
                content = response.choices[0].message.content
                print(f"  🤖 Response received ({len(content)} chars)")
                print(f"  📄 RAW RESPONSE: {content[:500]}")  # Print first 500 chars to debug
                
                # Try to parse JSON
                batch_events = []
                try:
                    batch_events = json.loads(content)
                    print(f"  ✅ Parsed {len(batch_events)} events from batch")
                except Exception as e:
                    print(f"  ⚠️ JSON parse error: {str(e)[:100]}")
                    # Try to extract JSON from markdown code blocks
                    import re
                    json_match = re.search(r'```(?:json)?\s*(\[.*?\])\s*```', content, re.DOTALL)
                    if json_match:
                        try:
                            batch_events = json.loads(json_match.group(1))
                            print(f"  ✅ Extracted {len(batch_events)} events from markdown")
                        except Exception as markdown_error:
                            print(f"  ⚠️ Markdown JSON parse error: {str(markdown_error)[:100]}")
                    else:
                        print(f"  ⚠️ No valid JSON in batch {batch_num + 1}, trying alternative patterns...")
                        # Try to find JSON array anywhere in the response
                        array_match = re.search(r'\[[\s\S]*?\{[\s\S]*?\}[\s\S]*?\]', content)
                        if array_match:
                            try:
                                batch_events = json.loads(array_match.group(0))
                                print(f"  ✅ Extracted {len(batch_events)} events from found JSON array")
                            except Exception as array_error:
                                print(f"  ⚠️ Array JSON parse error: {str(array_error)[:100]}")
                
                all_events.extend(batch_events)
                
                # Small delay to avoid rate limiting
                if batch_num < total_batches - 1:
                    import time
                    time.sleep(0.5)
            
            print(f"🎯 Total events extracted from all batches: {len(all_events)}")
            return {
                "success": True,
                "events": all_events,
                "llm_response": f"Processed {total_batches} batches, extracted {len(all_events)} events"
            }
            
        except Exception as e:
            print(f"💥 LLM extraction exception: {str(e)}")
            raise Exception(f"LLM extraction failed: {str(e)}")


# Global instance
imap_service = IMAPEmailService()
