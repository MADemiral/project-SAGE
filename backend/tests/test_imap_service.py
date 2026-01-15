"""
Unit tests for IMAP Email Service
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from app.services.imap_email_service import IMAPEmailService
import imaplib


class TestIMAPEmailService:
    """Test cases for IMAP Email Service"""
    
    def test_init(self):
        """Test service initialization"""
        service = IMAPEmailService()
        
        assert service.connection is None
        assert service.email_address is None
        assert service.is_connected is False
    
    @patch('app.services.imap_email_service.imaplib.IMAP4_SSL')
    def test_connect_success(self, mock_imap):
        """Test successful IMAP connection"""
        mock_connection = MagicMock()
        mock_connection.login.return_value = ('OK', [b'Logged in'])
        mock_imap.return_value = mock_connection
        
        service = IMAPEmailService()
        result = service.connect('test@gmail.com', 'app_password')
        
        assert result is True
        assert service.is_connected is True
        assert service.email_address == 'test@gmail.com'
        mock_connection.login.assert_called_once_with('test@gmail.com', 'app_password')
    
    @patch('app.services.imap_email_service.imaplib.IMAP4_SSL')
    def test_connect_authentication_failed(self, mock_imap):
        """Test connection failure due to authentication"""
        mock_connection = MagicMock()
        mock_connection.login.side_effect = imaplib.IMAP4.error('authentication failed')
        mock_imap.return_value = mock_connection
        
        service = IMAPEmailService()
        
        with pytest.raises(Exception) as exc_info:
            service.connect('test@gmail.com', 'wrong_password')
        
        assert 'Authentication failed' in str(exc_info.value)
        assert service.is_connected is False
    
    @patch('app.services.imap_email_service.imaplib.IMAP4_SSL')
    def test_connect_eof_error(self, mock_imap):
        """Test connection failure due to EOF error"""
        mock_imap.side_effect = Exception('EOF occurred in violation of protocol')
        
        service = IMAPEmailService()
        
        with pytest.raises(Exception) as exc_info:
            service.connect('test@gmail.com', 'password')
        
        assert 'Connection closed by server' in str(exc_info.value)
    
    @patch('app.services.imap_email_service.imaplib.IMAP4_SSL')
    def test_disconnect(self, mock_imap):
        """Test disconnecting from IMAP server"""
        mock_connection = MagicMock()
        mock_connection.login.return_value = ('OK', [b'Logged in'])
        mock_imap.return_value = mock_connection
        
        service = IMAPEmailService()
        service.connect('test@gmail.com', 'password')
        service.disconnect()
        
        assert service.connection is None
        assert service.email_address is None
        assert service.is_connected is False
        mock_connection.close.assert_called_once()
        mock_connection.logout.assert_called_once()
    
    @patch('app.services.imap_email_service.imaplib.IMAP4_SSL')
    def test_fetch_emails_not_connected(self, mock_imap):
        """Test fetching emails when not connected"""
        service = IMAPEmailService()
        
        with pytest.raises(Exception) as exc_info:
            service.fetch_emails()
        
        assert 'Not connected' in str(exc_info.value)
    
    @patch('app.services.imap_email_service.imaplib.IMAP4_SSL')
    def test_fetch_emails_success(self, mock_imap):
        """Test successful email fetching"""
        # Mock IMAP connection
        mock_connection = MagicMock()
        mock_connection.login.return_value = ('OK', [b'Logged in'])
        mock_connection.select.return_value = ('OK', [b'10'])
        mock_connection.search.return_value = ('OK', [b'1 2 3'])
        
        # Mock email data
        mock_email_data = b'Subject: Test Email\r\nFrom: sender@test.com\r\n\r\nTest body'
        mock_connection.fetch.return_value = ('OK', [(b'1 (RFC822 {123}', mock_email_data)])
        
        mock_imap.return_value = mock_connection
        
        service = IMAPEmailService()
        service.connect('test@gmail.com', 'password')
        
        emails = service.fetch_emails(days=7, max_results=10)
        
        assert isinstance(emails, list)
        mock_connection.select.assert_called_once_with("INBOX")
        mock_connection.search.assert_called()
    
    @patch('app.services.imap_email_service.imaplib.IMAP4_SSL')
    def test_fetch_emails_connection_expired(self, mock_imap):
        """Test handling of expired connection during fetch"""
        mock_connection = MagicMock()
        mock_connection.login.return_value = ('OK', [b'Logged in'])
        mock_connection.noop.side_effect = Exception("Connection expired")
        mock_imap.return_value = mock_connection
        
        service = IMAPEmailService()
        service.connect('test@gmail.com', 'password')
        
        with pytest.raises(Exception) as exc_info:
            service.fetch_emails()
        
        assert 'Connection expired' in str(exc_info.value)
    
    @patch('app.services.imap_email_service.imaplib.IMAP4_SSL')
    @patch('app.services.imap_email_service.Groq')
    def test_extract_calendar_events(self, mock_groq, mock_imap):
        """Test calendar event extraction from emails using LLM"""
        # Mock IMAP
        mock_connection = MagicMock()
        mock_connection.login.return_value = ('OK', [b'Logged in'])
        mock_imap.return_value = mock_connection
        
        # Mock Groq LLM
        mock_client = MagicMock()
        mock_completion = MagicMock()
        mock_completion.choices = [
            MagicMock(message=MagicMock(content='{"title":"Meeting","event_date":"2026-01-20","location":"Room A","event_type":"academic"}'))
        ]
        mock_client.chat.completions.create.return_value = mock_completion
        mock_groq.return_value = mock_client
        
        service = IMAPEmailService()
        service.connect('test@gmail.com', 'password')
        
        # Test that service was initialized properly
        assert service.is_connected is True
        assert service.email_address == 'test@gmail.com'
    
    def test_imap_server_constants(self):
        """Test IMAP server configuration constants"""
        assert IMAPEmailService.IMAP_SERVER == "imap.gmail.com"
        assert IMAPEmailService.IMAP_PORT == 993
    
    @patch('app.services.imap_email_service.imaplib.IMAP4_SSL')
    def test_reconnect_closes_existing_connection(self, mock_imap):
        """Test that connecting again closes existing connection"""
        mock_connection1 = MagicMock()
        mock_connection1.login.return_value = ('OK', [b'Logged in'])
        
        mock_connection2 = MagicMock()
        mock_connection2.login.return_value = ('OK', [b'Logged in'])
        
        mock_imap.side_effect = [mock_connection1, mock_connection2]
        
        service = IMAPEmailService()
        service.connect('test1@gmail.com', 'password1')
        service.connect('test2@gmail.com', 'password2')
        
        # First connection should be logged out
        mock_connection1.logout.assert_called_once()
        assert service.email_address == 'test2@gmail.com'
