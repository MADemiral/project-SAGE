import React, { useState, useEffect } from 'react';
import { Calendar, Mail, RefreshCw, CheckCircle, AlertCircle, Lock, Trash2, ArrowUpDown, Check, X, Plus, ChevronLeft, ChevronRight, Edit, LogOut } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';

const CalendarPage = () => {
  const { user } = useAuth(); // Get authenticated user from context
  const { isDark } = useTheme(); // Get theme context
  const [emails, setEmails] = useState([]);
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(false);
  const [extracting, setExtracting] = useState(false);
  const [authenticated, setAuthenticated] = useState(false);
  const [error, setError] = useState('');
  const [profile, setProfile] = useState(null);
  const [extractionResult, setExtractionResult] = useState(null);
  const [sortOrder, setSortOrder] = useState('latest'); // 'latest' or 'earliest'
  const [extractedEvents, setExtractedEvents] = useState([]); // Events pending review
  const [approvedEvents, setApprovedEvents] = useState(new Set()); // Track approved event indices
  const [currentDate, setCurrentDate] = useState(new Date());
  const [viewMode, setViewMode] = useState('month'); // 'month' or 'week'
  
  // IMAP state (Gmail)
  const [showImapLogin, setShowImapLogin] = useState(false);
  const [imapEmail, setImapEmail] = useState('');
  const [imapPassword, setImapPassword] = useState('');
  
  // New states for event details and confirmation popup
  const [selectedEvent, setSelectedEvent] = useState(null); // Event clicked on calendar
  const [showConfirmPopup, setShowConfirmPopup] = useState(false); // Confirmation popup
  const [savingEvents, setSavingEvents] = useState(false); // Track save progress
  const [editingEvent, setEditingEvent] = useState(null); // Event being edited
  // Calendar is always visible on this page - no popup needed

  useEffect(() => {
    checkAuthStatus();
    if (user) {
      loadEvents(); // Only load events if user is logged in
    } else {
      // Clear events when user logs out
      setEvents([]);
      setEmails([]);
      setExtractedEvents([]);
      setApprovedEvents(new Set());
      setExtractionResult(null);
      // Also logout from IMAP if user logged out from main app
      if (authenticated) {
        handleImapLogout();
      }
    }
  }, [user]); // Re-run when user changes

  const checkAuthStatus = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/v1/calendar/imap/status');
      const data = await response.json();
      setAuthenticated(data.authenticated);
      if (data.authenticated) {
        setProfile({ email: data.email, name: data.email });
      }
    } catch (err) {
      console.error('Error checking auth status:', err);
    }
  };

  const handleFetchEmails = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await fetch('http://localhost:8000/api/v1/calendar/imap/fetch-emails', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ days: 30, max_results: 10 })  // Get last 10 emails
      });
      if (response.ok) {
        const data = await response.json();
        setEmails(data.emails || []);
      } else {
        const data = await response.json();
        setError(data.detail || 'Failed to fetch emails');
      }
    } catch (err) {
      setError('Failed to fetch emails: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  // IMAP Login Function
  const handleImapLogin = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await fetch('http://localhost:8000/api/v1/calendar/imap/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: imapEmail,
          password: imapPassword
        })
      });
      
      if (response.ok) {
        const data = await response.json();
        setAuthenticated(true);
        setProfile({ email: data.email, name: data.email });
        setShowImapLogin(false);
        setImapPassword(''); // Clear password
        setError('');
      } else {
        const data = await response.json();
        setError(data.detail || 'IMAP login failed');
      }
    } catch (err) {
      setError('IMAP login failed: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleImapLogout = async () => {
    try {
      await fetch('http://localhost:8000/api/v1/calendar/imap/logout', {
        method: 'POST'
      });
      
      // Clear all IMAP-related state
      setAuthenticated(false);
      setProfile(null);
      setEmails([]);
      setExtractedEvents([]);
      setApprovedEvents(new Set());
      setExtractionResult(null);
      setImapEmail('');
      setImapPassword('');
      setError('');
    } catch (err) {
      console.error('Logout failed:', err);
    }
  };

  const handleExtractEvents = async () => {
    if (!user) {
      setError('User not logged in');
      return;
    }
    
    setExtracting(true);
    setError('');
    setExtractionResult(null);
    setExtractedEvents([]);
    setApprovedEvents(new Set());
    
    try {
      const response = await fetch('http://localhost:8000/api/v1/calendar/imap/extract-events', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: user.id, days: 30, max_results: 10 })  // Use real user.id
      });
      if (response.ok) {
        const data = await response.json();
        setExtractionResult(data);
        
        // Set extracted events for review (not saved yet)
        if (data.extraction && data.extraction.events) {
          // Filter out expired events (only show future events)
          const now = new Date();
          const futureEvents = data.extraction.events.filter(event => {
            if (!event.event_date) return true; // Keep if no date
            const eventDate = new Date(event.event_date);
            return eventDate >= now; // Only keep future events
          });
          
          setExtractedEvents(futureEvents);
          // Auto-approve all by default
          const allIndices = new Set(futureEvents.map((_, idx) => idx));
          setApprovedEvents(allIndices);
        }
      } else {
        const data = await response.json();
        setError(data.detail || 'Failed to extract events');
      }
    } catch (err) {
      setError('Failed to extract events: ' + err.message);
    } finally {
      setExtracting(false);
    }
  };

  const toggleEventApproval = (index) => {
    const newApproved = new Set(approvedEvents);
    if (newApproved.has(index)) {
      newApproved.delete(index);
    } else {
      newApproved.add(index);
    }
    setApprovedEvents(newApproved);
  };

  const addApprovedEventsToCalendar = () => {
    const eventsToAdd = extractedEvents.filter((_, idx) => approvedEvents.has(idx));
    
    if (eventsToAdd.length === 0) {
      setError('No events selected to add');
      return;
    }
    
    // Show confirmation popup instead of immediately saving
    setShowConfirmPopup(true);
  };
  
  const confirmAndSaveEvents = async () => {
    if (!user) {
      setError('User not logged in');
      return;
    }
    
    const eventsToAdd = extractedEvents.filter((_, idx) => approvedEvents.has(idx));
    
    setSavingEvents(true);
    setError('');
    
    try {
      // Save each approved event
      for (const event of eventsToAdd) {
        const response = await fetch('http://localhost:8000/api/v1/calendar/imap/events', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            user_id: user.id,  // Use real user.id
            ...event
          })
        });
        
        if (!response.ok) {
          console.error('Failed to save event:', event.title);
        }
      }
      
      // Clear extraction results and reload events
      setExtractedEvents([]);
      setApprovedEvents(new Set());
      setExtractionResult(null);
      setShowConfirmPopup(false);
      loadEvents();
      
      setError(''); // Clear any previous errors
    } catch (err) {
      setError('Failed to add events: ' + err.message);
    } finally {
      setSavingEvents(false);
    }
  };

  const loadEvents = async () => {
    if (!user) {
      setEvents([]); // Clear events if no user
      return;
    }
    
    try {
      const response = await fetch(`http://localhost:8000/api/v1/calendar/imap/events/${user.id}`);  // Use real user.id
      if (response.ok) {
        const data = await response.json();
        setEvents(data.events || []);
      }
    } catch (err) {
      console.error('Failed to load events:', err);
    }
  };

  const confirmEvent = async (eventId) => {
    try {
      const response = await fetch(`http://localhost:8000/api/v1/calendar/events/${eventId}/confirm`, {
        method: 'PUT'
      });
      if (response.ok) {
        loadEvents();  // Refresh list
      }
    } catch (err) {
      console.error('Failed to confirm event:', err);
    }
  };

  const deleteEvent = async (eventId) => {
    try {
      const response = await fetch(`http://localhost:8000/api/v1/calendar/events/${eventId}`, {
        method: 'DELETE'
      });
      if (response.ok) {
        loadEvents();  // Refresh list
      }
    } catch (err) {
      console.error('Failed to delete event:', err);
    }
  };

  // Sort emails by date
  const getSortedEmails = () => {
    if (emails.length === 0) return [];
    
    return [...emails].sort((a, b) => {
      const dateA = new Date(a.date);
      const dateB = new Date(b.date);
      
      if (sortOrder === 'latest') {
        return dateB - dateA; // Newest first
      } else {
        return dateA - dateB; // Oldest first
      }
    });
  };

  // Calendar helper functions
  const getDaysInMonth = (date) => {
    const year = date.getFullYear();
    const month = date.getMonth();
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const daysInMonth = lastDay.getDate();
    const startingDayOfWeek = firstDay.getDay();
    
    return { daysInMonth, startingDayOfWeek, firstDay, lastDay };
  };

  const getEventsForDate = (date) => {
    return events.filter(event => {
      const eventDate = new Date(event.event_date);
      return eventDate.toDateString() === date.toDateString();
    });
  };

  const navigateMonth = (direction) => {
    const newDate = new Date(currentDate);
    newDate.setMonth(newDate.getMonth() + direction);
    setCurrentDate(newDate);
  };

  const goToToday = () => {
    setCurrentDate(new Date());
  };

  const formatMonthYear = (date) => {
    return date.toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
  };

  const isToday = (date) => {
    const today = new Date();
    return date.toDateString() === today.toDateString();
  };

  const isSameMonth = (date) => {
    return date.getMonth() === currentDate.getMonth();
  };

  const getEventTypeColor = (eventType) => {
    if (!eventType) return 'bg-blue-500';
    
    const type = eventType.toLowerCase().trim();
    const colors = {
      'academic': 'bg-blue-600',
      'social': 'bg-purple-600',
      'student_activity': 'bg-green-600',
      'student activity': 'bg-green-600',
      'career': 'bg-orange-600',
      'other': 'bg-gray-600'
    };
    
    return colors[type] || 'bg-gray-600';
  };

  return (
    <div className={`flex h-screen ${isDark ? 'bg-dark-950 text-white' : 'bg-gray-50 text-gray-900'} overflow-hidden`}>
      <div className="flex-1 flex flex-col overflow-hidden">
        <div className="flex-1 overflow-y-auto">
          <div className="max-w-7xl mx-auto p-6">
            <div className="mb-8">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-3">
                  <Calendar className="w-8 h-8 text-primary-400" />
                  <h1 className="text-3xl font-bold bg-gradient-to-r from-primary-400 to-primary-600 bg-clip-text text-transparent">Calendar & Email</h1>
                </div>
              </div>
            <p className={isDark ? 'text-dark-400' : 'text-gray-600'}>Sign in with your Gmail account to fetch and manage your calendar events</p>
          </div>
        {error && (
          <div className="mb-6 p-4 bg-red-500/10 border border-red-500/20 rounded-lg flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
            <p className="text-red-400">{error}</p>
          </div>
        )}
        {!authenticated && !showImapLogin && (
          <div className="mb-6 p-6 bg-dark-900/50 border border-dark-700 rounded-lg">
            <h3 className="text-xl font-semibold mb-4">Sign In Required</h3>
            <p className="text-dark-400 mb-4">Use your Gmail address and app-specific password to access your emails</p>
            
            <button 
              onClick={() => setShowImapLogin(true)} 
              className="px-6 py-3 bg-primary-600 hover:bg-primary-700 rounded-lg transition-colors flex items-center gap-2"
            >
              <Lock className="w-5 h-5" />
              Sign in with Gmail
            </button>
          </div>
        )}

        {/* IMAP Login Form */}
        {showImapLogin && !authenticated && (
          <div className="mb-6 p-6 bg-dark-900/50 border border-dark-700 rounded-lg">
            <h3 className="text-xl font-semibold mb-4 flex items-center gap-2">
              <Lock className="w-5 h-5" />
              Gmail Login
            </h3>
            <p className="text-dark-400 mb-4 text-sm">
              Enter your Gmail address and <strong>app-specific password</strong>. 
              <br />
              📝 <strong>Setup required:</strong> Enable IMAP in Gmail settings and create an app password at <a href="https://myaccount.google.com/apppasswords" target="_blank" rel="noopener noreferrer" className="text-primary-400 hover:underline">myaccount.google.com/apppasswords</a>
            </p>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">Gmail Address</label>
                <input
                  type="email"
                  value={imapEmail}
                  onChange={(e) => setImapEmail(e.target.value)}
                  placeholder="your.email@gmail.com"
                  className="w-full px-4 py-2 bg-dark-800 border border-dark-600 rounded-lg focus:border-primary-500 focus:outline-none"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">App Password (16 characters)</label>
                <input
                  type="password"
                  value={imapPassword}
                  onChange={(e) => setImapPassword(e.target.value)}
                  placeholder="xxxx xxxx xxxx xxxx"
                  className="w-full px-4 py-2 bg-dark-800 border border-dark-600 rounded-lg focus:border-primary-500 focus:outline-none"
                />
              </div>
              <div className="flex gap-3">
                <button
                  onClick={handleImapLogin}
                  disabled={loading || !imapEmail || !imapPassword}
                  className="px-6 py-2 bg-primary-600 hover:bg-primary-700 disabled:bg-dark-700 disabled:cursor-not-allowed rounded-lg transition-colors"
                >
                  {loading ? 'Connecting...' : 'Sign In'}
                </button>
                <button
                  onClick={() => {
                    setShowImapLogin(false);
                    setImapEmail('');
                    setImapPassword('');
                  }}
                  className="px-6 py-2 bg-dark-700 hover:bg-dark-600 rounded-lg transition-colors"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        )}
        
        {authenticated && (
          <>
            {profile && (
              <div className="mb-6 p-4 bg-green-500/10 border border-green-500/20 rounded-lg flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <CheckCircle className="w-5 h-5 text-green-400" />
                  <div>
                    <p className="text-green-400 font-medium">{profile.name}</p>
                    <p className="text-dark-400 text-sm">{profile.email}</p>
                  </div>
                </div>
                <button
                  onClick={handleImapLogout}
                  className="px-4 py-2 bg-red-600 hover:bg-red-700 rounded-lg transition-colors flex items-center gap-2"
                  title="Logout from Gmail"
                >
                  <LogOut className="w-4 h-4" />
                  Logout
                </button>
              </div>
            )}
            <div className="mb-6">
              <button onClick={handleFetchEmails} disabled={loading} className="px-6 py-3 bg-primary-600 hover:bg-primary-700 disabled:bg-dark-700 disabled:cursor-not-allowed rounded-lg transition-colors flex items-center gap-2 mr-3">
                {loading ? (
                  <>
                    <RefreshCw className="w-5 h-5 animate-spin" />Fetching...
                  </>
                ) : (
                  <>
                    <Mail className="w-5 h-5" />Fetch Emails (Last 30 Days)
                  </>
                )}
              </button>
              <button onClick={handleExtractEvents} disabled={extracting} className="px-6 py-3 bg-green-600 hover:bg-green-700 disabled:bg-dark-700 disabled:cursor-not-allowed rounded-lg transition-colors flex items-center gap-2 mt-3">
                {extracting ? (
                  <>
                    <RefreshCw className="w-5 h-5 animate-spin" />Extracting Events with AI...
                  </>
                ) : (
                  <>
                    <Calendar className="w-5 h-5" />Extract Events from Emails (AI)
                  </>
                )}
              </button>
            </div>

            {/* Extracted Events Review Section */}
            {extractedEvents.length > 0 && (
              <div className="mb-6 p-6 bg-gradient-to-br from-purple-500/10 to-blue-500/10 border border-purple-500/30 rounded-lg">
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <h3 className="text-xl font-semibold text-purple-300">📅 Found {extractedEvents.length} Event(s)</h3>
                    <p className="text-dark-400 text-sm mt-1">Review and select events to add to your calendar</p>
                  </div>
                  <button
                    onClick={addApprovedEventsToCalendar}
                    disabled={approvedEvents.size === 0 || loading}
                    className="px-6 py-3 bg-green-600 hover:bg-green-700 disabled:bg-dark-700 disabled:cursor-not-allowed rounded-lg transition-colors flex items-center gap-2 font-medium"
                  >
                    <Plus className="w-5 h-5" />
                    Add {approvedEvents.size} to Calendar
                  </button>
                </div>
                
                <div className="space-y-3">
                  {extractedEvents.map((event, index) => {
                    const isApproved = approvedEvents.has(index);
                    return (
                      <div
                        key={index}
                        className={`p-4 rounded-lg border transition-all ${
                          isApproved
                            ? 'bg-green-500/10 border-green-500/30'
                            : 'bg-red-500/10 border-red-500/30 opacity-60'
                        }`}
                      >
                        <div className="flex items-start gap-4">
                          <div className="flex flex-col gap-2 pt-1">
                            <button
                              onClick={() => toggleEventApproval(index)}
                              className={`p-2 rounded-lg transition-all ${
                                isApproved
                                  ? 'bg-green-600 hover:bg-green-700 text-white'
                                  : 'bg-dark-700 hover:bg-dark-600 text-dark-400'
                              }`}
                              title={isApproved ? 'Approved - Click to reject' : 'Rejected - Click to approve'}
                            >
                              <Check className="w-5 h-5" />
                            </button>
                            <button
                              onClick={() => toggleEventApproval(index)}
                              className={`p-2 rounded-lg transition-all ${
                                !isApproved
                                  ? 'bg-red-600 hover:bg-red-700 text-white'
                                  : 'bg-dark-700 hover:bg-dark-600 text-dark-400'
                              }`}
                              title={!isApproved ? 'Rejected - Click to approve' : 'Approved - Click to reject'}
                            >
                              <X className="w-5 h-5" />
                            </button>
                          </div>
                          
                          <div className="flex-1">
                            <div className="flex items-start justify-between gap-4 mb-2">
                              <h4 className="font-semibold text-lg">{event.title}</h4>
                              <div className="flex gap-2">
                                {event.event_type && (
                                  <span className="px-3 py-1 bg-blue-500/20 text-blue-400 rounded-full text-xs font-medium">
                                    {event.event_type}
                                  </span>
                                )}
                                {event.priority && (
                                  <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                                    event.priority === 'high' ? 'bg-red-500/20 text-red-400' :
                                    event.priority === 'medium' ? 'bg-yellow-500/20 text-yellow-400' :
                                    'bg-gray-500/20 text-gray-400'
                                  }`}>
                                    {event.priority}
                                  </span>
                                )}
                              </div>
                            </div>
                            
                            {event.description && (
                              <p className="text-dark-300 text-sm mb-3">{event.description}</p>
                            )}
                            
                            <div className="flex flex-wrap gap-3 text-sm text-dark-400">
                              {event.event_date && (
                                <span className="flex items-center gap-1">
                                  📅 {new Date(event.event_date).toLocaleString()}
                                </span>
                              )}
                              {event.location && (
                                <span className="flex items-center gap-1">
                                  📍 {event.location}
                                </span>
                              )}
                              {event.organizer && (
                                <span className="flex items-center gap-1">
                                  👤 {event.organizer}
                                </span>
                              )}
                            </div>
                            
                            {event.requirements && (
                              <div className="mt-2 p-2 bg-dark-800/50 rounded text-xs text-dark-400">
                                <strong>Requirements:</strong> {event.requirements}
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {extractionResult && extractedEvents.length === 0 && (
              <div className="mb-6 p-4 bg-blue-500/10 border border-blue-500/20 rounded-lg">
                <h3 className="font-semibold mb-2 text-blue-400">Extraction Complete!</h3>
                <p className="text-dark-300">{extractionResult.message || 'No new events found in your emails.'}</p>
              </div>
            )}

            {emails.length > 0 && (
              <div>
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-xl font-semibold">Emails ({emails.length})</h3>
                  <div className="flex items-center gap-2">
                    <ArrowUpDown className="w-4 h-4 text-dark-400" />
                    <select
                      value={sortOrder}
                      onChange={(e) => setSortOrder(e.target.value)}
                      className="px-3 py-1.5 bg-dark-800 border border-dark-600 rounded-lg text-sm focus:border-primary-500 focus:outline-none cursor-pointer"
                    >
                      <option value="latest">Latest First</option>
                      <option value="earliest">Earliest First</option>
                    </select>
                  </div>
                </div>
                <div className="space-y-3 max-h-[500px] overflow-y-auto pr-2">
                  {getSortedEmails().map((email) => (
                    <div key={email.id} className="p-4 bg-dark-900/50 border border-dark-700 rounded-lg hover:border-primary-500/30 transition-colors">
                      <div className="flex items-start justify-between gap-4 mb-2">
                        <h4 className="font-medium text-lg">{email.subject || 'No Subject'}</h4>
                        <span className="px-2 py-1 bg-primary-500/20 text-primary-400 text-xs rounded flex-shrink-0">Unread</span>
                      </div>
                      <p className="text-dark-400 text-sm mb-2">From: {email.from || 'Unknown'}</p>
                      <p className="text-dark-400 text-sm mb-2">{email.date || 'No date'}</p>
                      <p className="text-dark-300 text-sm line-clamp-3">{email.body || 'No content'}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
            {emails.length === 0 && !loading && (
              <div className="text-center py-12 text-dark-400">
                <Mail className="w-16 h-16 mx-auto mb-4 opacity-50" />
                <p>No emails fetched yet. Click "Fetch Emails" to load your inbox.</p>
              </div>
            )}
          </>
        )}

        {/* Always show calendar - displays events when available (visible whether authenticated or not) */}
        <div className="mb-6">
          {/* Calendar Header */}
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-4">
              <h3 className="text-2xl font-bold">Calendar</h3>
              <button
                onClick={goToToday}
                className="px-4 py-2 bg-primary-600 hover:bg-primary-700 rounded-lg text-sm font-medium transition-colors"
              >
                Today
              </button>
            </div>
            <div className="flex items-center gap-4">
              <button
                onClick={() => navigateMonth(-1)}
                className="p-2 hover:bg-dark-800 rounded-lg transition-colors"
              >
                <ChevronLeft className="w-5 h-5" />
              </button>
              <h4 className="text-xl font-semibold min-w-[200px] text-center">
                {formatMonthYear(currentDate)}
              </h4>
              <button
                onClick={() => navigateMonth(1)}
                className="p-2 hover:bg-dark-800 rounded-lg transition-colors"
              >
                <ChevronRight className="w-5 h-5" />
              </button>
            </div>
            <div className="text-sm text-dark-400">
              {events.length} event{events.length !== 1 ? 's' : ''}
            </div>
          </div>

          {/* Calendar Grid */}
          <div className="bg-dark-900/50 border border-dark-700 rounded-lg overflow-hidden">
            {/* Weekday Headers */}
            <div className="grid grid-cols-7 bg-dark-800 border-b border-dark-700">
              {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map(day => (
                <div key={day} className="p-3 text-center text-sm font-semibold text-dark-300 border-r border-dark-700 last:border-r-0">
                  {day}
                </div>
              ))}
            </div>

            {/* Calendar Days */}
            <div className="grid grid-cols-7">
              {(() => {
                const { daysInMonth, startingDayOfWeek } = getDaysInMonth(currentDate);
                const days = [];
                
                // Previous month's trailing days
                for (let i = 0; i < startingDayOfWeek; i++) {
                  const prevMonthDate = new Date(currentDate.getFullYear(), currentDate.getMonth(), -startingDayOfWeek + i + 1);
                  days.push(
                    <div key={`prev-${i}`} className="min-h-[120px] p-2 bg-dark-900/30 border-r border-b border-dark-700/50">
                      <div className="text-xs text-dark-600 mb-1">{prevMonthDate.getDate()}</div>
                    </div>
                  );
                }
                
                // Current month's days
                for (let day = 1; day <= daysInMonth; day++) {
                  const date = new Date(currentDate.getFullYear(), currentDate.getMonth(), day);
                  const dayEvents = getEventsForDate(date);
                  const today = isToday(date);
                  
                  days.push(
                    <div
                      key={day}
                      className={`min-h-[120px] p-2 border-r border-b border-dark-700 ${
                        today ? 'bg-primary-500/10' : 'bg-dark-900/50'
                      } hover:bg-dark-800/50 transition-colors`}
                    >
                      <div className={`text-sm font-medium mb-2 ${
                        today ? 'bg-primary-600 text-white w-7 h-7 rounded-full flex items-center justify-center' : 'text-dark-300'
                      }`}>
                        {day}
                      </div>
                      <div className="space-y-1">
                        {dayEvents.slice(0, 3).map((event, idx) => (
                          <div
                            key={idx}
                            onClick={() => setSelectedEvent(event)}
                            className={`text-xs p-1.5 rounded cursor-pointer transition-all hover:scale-105 hover:shadow-lg ${
                              event.event_type === 'academic' ? 'bg-blue-600/80 hover:bg-blue-600 text-white' :
                              event.event_type === 'social' ? 'bg-purple-600/80 hover:bg-purple-600 text-white' :
                              event.event_type === 'student_activity' ? 'bg-green-600/80 hover:bg-green-600 text-white' :
                              event.event_type === 'career' ? 'bg-orange-600/80 hover:bg-orange-600 text-white' :
                              'bg-gray-600/80 hover:bg-gray-600 text-white'
                            }`}
                          >
                            <div className="font-medium truncate">{event.title}</div>
                            {event.location && (
                              <div className="text-[10px] opacity-80 truncate">📍 {event.location}</div>
                            )}
                          </div>
                        ))}
                        {dayEvents.length > 3 && (
                          <div 
                            className="text-[10px] text-primary-400 pl-1 cursor-pointer hover:text-primary-300"
                            onClick={() => setSelectedEvent({ 
                              title: `All Events (${date.toLocaleDateString()})`,
                              description: 'Multiple events on this day',
                              allDayEvents: dayEvents
                            })}
                          >
                            +{dayEvents.length - 3} more
                          </div>
                        )}
                      </div>
                    </div>
                  );
                }
                
                // Next month's leading days
                const totalCells = days.length;
                const remainingCells = 35 - totalCells; // 5 weeks
                for (let i = 1; i <= remainingCells; i++) {
                  const nextMonthDate = new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, i);
                  days.push(
                    <div key={`next-${i}`} className="min-h-[120px] p-2 bg-dark-900/30 border-r border-b border-dark-700/50">
                      <div className="text-xs text-dark-600 mb-1">{nextMonthDate.getDate()}</div>
                    </div>
                  );
                }
                
                return days;
              })()}
            </div>
          </div>

          {/* Event Legend */}
          <div className="mt-4 flex flex-wrap gap-4 text-sm">
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 bg-blue-600 rounded"></div>
              <span className="text-dark-400">Academic</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 bg-purple-600 rounded"></div>
              <span className="text-dark-400">Social</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 bg-green-600 rounded"></div>
              <span className="text-dark-400">Student Activity</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 bg-orange-600 rounded"></div>
              <span className="text-dark-400">Career</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 bg-gray-600 rounded"></div>
              <span className="text-dark-400">Other</span>
            </div>
          </div>
        </div>
          </div>
        </div>
      </div>
      
      {/* Event Detail Popup */}
      {selectedEvent && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4" onClick={() => setSelectedEvent(null)}>
          <div className="bg-dark-800 border-2 border-primary-500/50 rounded-xl max-w-2xl w-full max-h-[80vh] overflow-y-auto shadow-2xl" onClick={(e) => e.stopPropagation()}>
            {/* Header */}
            <div className="sticky top-0 bg-gradient-to-r from-primary-600 to-purple-600 p-6 rounded-t-xl">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <h2 className="text-2xl font-bold text-white mb-2">{selectedEvent.title}</h2>
                  {selectedEvent.event_type && (
                    <span className="inline-block px-3 py-1 bg-white/20 backdrop-blur-sm text-white text-sm rounded-full">
                      {selectedEvent.event_type.replace('_', ' ').toUpperCase()}
                    </span>
                  )}
                </div>
                <button
                  onClick={() => setSelectedEvent(null)}
                  className="text-white hover:bg-white/20 rounded-lg p-2 transition-colors"
                >
                  <X className="w-6 h-6" />
                </button>
              </div>
            </div>

            {/* Content */}
            <div className="p-6 space-y-4">
              {selectedEvent.allDayEvents ? (
                // Show all events for a day
                <div className="space-y-3">
                  <h3 className="text-lg font-semibold text-white mb-4">All Events:</h3>
                  {selectedEvent.allDayEvents.map((event, idx) => (
                    <div key={idx} className="p-4 bg-dark-900/50 border border-dark-700 rounded-lg">
                      <div className="flex items-start justify-between mb-2">
                        <h4 className="font-semibold text-white">{event.title}</h4>
                        <span className={`px-2 py-1 text-xs rounded ${
                          event.event_type === 'academic' ? 'bg-blue-600/80 text-white' :
                          event.event_type === 'social' ? 'bg-purple-600/80 text-white' :
                          event.event_type === 'student_activity' ? 'bg-green-600/80 text-white' :
                          event.event_type === 'career' ? 'bg-orange-600/80 text-white' :
                          'bg-gray-600/80 text-white'
                        }`}>
                          {event.event_type || 'other'}
                        </span>
                      </div>
                      {event.description && <p className="text-dark-300 text-sm mb-2">{event.description}</p>}
                      {event.location && (
                        <p className="text-dark-400 text-sm flex items-center gap-2">
                          📍 {event.location}
                        </p>
                      )}
                      {event.event_date && (
                        <p className="text-dark-400 text-sm mt-2">
                          🕒 {new Date(event.event_date).toLocaleString()}
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                // Show single event details
                <>
                  {selectedEvent.description && (
                    <div>
                      <h3 className="text-sm font-semibold text-dark-400 mb-2">DESCRIPTION</h3>
                      <p className="text-white leading-relaxed">{selectedEvent.description}</p>
                    </div>
                  )}
                  
                  {selectedEvent.event_date && (
                    <div>
                      <h3 className="text-sm font-semibold text-dark-400 mb-2">DATE & TIME</h3>
                      <p className="text-white flex items-center gap-2">
                        🕒 {new Date(selectedEvent.event_date).toLocaleString('en-US', {
                          weekday: 'long',
                          year: 'numeric',
                          month: 'long',
                          day: 'numeric',
                          hour: '2-digit',
                          minute: '2-digit'
                        })}
                      </p>
                      {selectedEvent.end_date && (
                        <p className="text-dark-300 text-sm mt-1">
                          Until: {new Date(selectedEvent.end_date).toLocaleString('en-US', {
                            weekday: 'long',
                            year: 'numeric',
                            month: 'long',
                            day: 'numeric',
                            hour: '2-digit',
                            minute: '2-digit'
                          })}
                        </p>
                      )}
                    </div>
                  )}
                  
                  {selectedEvent.location && (
                    <div>
                      <h3 className="text-sm font-semibold text-dark-400 mb-2">LOCATION</h3>
                      <p className="text-white flex items-center gap-2">
                        📍 {selectedEvent.location}
                      </p>
                    </div>
                  )}
                  
                  {selectedEvent.organizer && (
                    <div>
                      <h3 className="text-sm font-semibold text-dark-400 mb-2">ORGANIZER</h3>
                      <p className="text-white">{selectedEvent.organizer}</p>
                    </div>
                  )}
                  
                  {selectedEvent.requirements && (
                    <div>
                      <h3 className="text-sm font-semibold text-dark-400 mb-2">REQUIREMENTS</h3>
                      <p className="text-white">{selectedEvent.requirements}</p>
                    </div>
                  )}
                  
                  {selectedEvent.priority && (
                    <div>
                      <h3 className="text-sm font-semibold text-dark-400 mb-2">PRIORITY</h3>
                      <span className={`inline-block px-3 py-1 rounded-full text-sm font-medium ${
                        selectedEvent.priority === 'high' ? 'bg-red-600/20 text-red-400' :
                        selectedEvent.priority === 'medium' ? 'bg-yellow-600/20 text-yellow-400' :
                        'bg-green-600/20 text-green-400'
                      }`}>
                        {selectedEvent.priority.toUpperCase()}
                      </span>
                    </div>
                  )}
                </>
              )}
            </div>

            {/* Action Buttons - Only show for single events from calendar, not "all day events" */}
            {!selectedEvent.allDayEvents && selectedEvent.id && (
              <div className="p-6 bg-dark-900/50 rounded-b-xl flex gap-3 border-t border-dark-700">
                <button
                  onClick={() => {
                    setEditingEvent(selectedEvent);
                    setSelectedEvent(null);
                  }}
                  className="flex-1 px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-all shadow-lg hover:shadow-xl flex items-center justify-center gap-2"
                >
                  <Edit className="w-5 h-5" />
                  Edit Event
                </button>
                <button
                  onClick={async () => {
                    if (confirm(`Are you sure you want to delete "${selectedEvent.title}"?`)) {
                      try {
                        await fetch(`http://localhost:8000/api/v1/calendar/events/${selectedEvent.id}`, {
                          method: 'DELETE'
                        });
                        setSelectedEvent(null);
                        loadEvents();
                      } catch (err) {
                        setError('Failed to delete event');
                      }
                    }
                  }}
                  className="flex-1 px-6 py-3 bg-red-600 hover:bg-red-700 text-white rounded-lg font-medium transition-all shadow-lg hover:shadow-xl flex items-center justify-center gap-2"
                >
                  <Trash2 className="w-5 h-5" />
                  Delete Event
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Confirmation Popup */}
      {showConfirmPopup && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-dark-800 border-2 border-primary-500/50 rounded-xl max-w-lg w-full shadow-2xl">
            {/* Header */}
            <div className="bg-gradient-to-r from-primary-600 to-purple-600 p-6 rounded-t-xl">
              <h2 className="text-2xl font-bold text-white flex items-center gap-3">
                <CheckCircle className="w-8 h-8" />
                Confirm Save to Calendar
              </h2>
            </div>

            {/* Content */}
            <div className="p-6 space-y-4">
              <p className="text-white text-lg">
                You are about to add <span className="font-bold text-primary-400">{approvedEvents.size}</span> event(s) to your calendar.
              </p>
              
              <div className="bg-dark-900/50 border border-dark-700 rounded-lg p-4 max-h-[300px] overflow-y-auto">
                <h3 className="text-sm font-semibold text-dark-400 mb-3">EVENTS TO BE ADDED:</h3>
                <div className="space-y-2">
                  {extractedEvents
                    .filter((_, idx) => approvedEvents.has(idx))
                    .map((event, idx) => (
                      <div key={idx} className="flex items-start gap-3 p-3 bg-dark-800 rounded-lg">
                        <CheckCircle className="w-5 h-5 text-green-400 flex-shrink-0 mt-0.5" />
                        <div className="flex-1 min-w-0">
                          <p className="font-medium text-white truncate">{event.title}</p>
                          <p className="text-sm text-dark-400 truncate">{event.event_date}</p>
                        </div>
                      </div>
                    ))}
                </div>
              </div>

              {savingEvents && (
                <div className="flex items-center justify-center gap-3 p-4 bg-primary-500/10 border border-primary-500/30 rounded-lg">
                  <RefreshCw className="w-5 h-5 text-primary-400 animate-spin" />
                  <span className="text-primary-400 font-medium">Saving events to calendar...</span>
                </div>
              )}
            </div>

            {/* Actions */}
            <div className="p-6 bg-dark-900/50 rounded-b-xl flex gap-3">
              <button
                onClick={() => setShowConfirmPopup(false)}
                disabled={savingEvents}
                className="flex-1 px-6 py-3 bg-dark-700 hover:bg-dark-600 disabled:bg-dark-800 disabled:text-dark-500 text-white rounded-lg font-medium transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={confirmAndSaveEvents}
                disabled={savingEvents}
                className="flex-1 px-6 py-3 bg-gradient-to-r from-primary-600 to-purple-600 hover:from-primary-500 hover:to-purple-500 disabled:from-dark-600 disabled:to-dark-600 text-white rounded-lg font-medium transition-all shadow-lg hover:shadow-xl disabled:shadow-none flex items-center justify-center gap-2"
              >
                {savingEvents ? (
                  <>
                    <RefreshCw className="w-5 h-5 animate-spin" />
                    Saving...
                  </>
                ) : (
                  <>
                    <Check className="w-5 h-5" />
                    Confirm & Save
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Calendar is always visible on this page - popup removed */}
    </div>
  );
};

export default CalendarPage;
