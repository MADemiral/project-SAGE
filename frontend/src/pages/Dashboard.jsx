import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { 
  Send, 
  BookOpen, 
  Users as UsersIcon, 
  Calendar as CalendarIcon,
  Plus,
  MessageSquare,
  Menu,
  X,
  Trash2,
  Bot,
  User as UserIcon,
  LogOut,
  Settings,
  Save,
  Moon,
  Sun,
  Shield,
  ChevronLeft,
  ChevronRight
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import { useNavigate } from 'react-router-dom';
import { conversationService } from '../services/conversations';
import CalendarPage from './CalendarPage';

const assistants = [
  {
    id: 'academic',
    name: 'Academic Assistant',
    icon: BookOpen,
    color: 'bg-blue-600',
    gradient: 'from-blue-500 to-blue-600',
    description: 'Course selection, syllabus, and academic planning'
  },
  {
    id: 'social',
    name: 'Social Assistant',
    icon: UsersIcon,
    color: 'bg-purple-600',
    gradient: 'from-purple-500 to-purple-600',
    description: 'Clubs, events, and campus activities'
  },
  {
    id: 'calendar',
    name: 'Calendar Assistant',
    icon: CalendarIcon,
    color: 'bg-green-600',
    gradient: 'from-green-500 to-green-600',
    description: 'Email scanning, event extraction, and calendar sync'
  }
];

export default function Dashboard() {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const { isDark, toggleTheme } = useTheme();
  const [activeAssistant, setActiveAssistant] = useState('academic');
  const [conversations, setConversations] = useState({});
  const [activeConversationId, setActiveConversationId] = useState(null);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [loadingConversations, setLoadingConversations] = useState(true);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [showUserModal, setShowUserModal] = useState(false);
  const [userFormData, setUserFormData] = useState({
    full_name: user?.full_name || '',
    email: user?.email || ''
  });
  
  // Calendar state
  const [showCalendarPopup, setShowCalendarPopup] = useState(false);
  const [calendarEvents, setCalendarEvents] = useState([]);
  const [currentDate, setCurrentDate] = useState(new Date());
  const [selectedEvent, setSelectedEvent] = useState(null);
  
  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);

  // Load conversations from API on mount
  useEffect(() => {
    loadConversations();
  }, []);

  // Load calendar events
  useEffect(() => {
    const loadCalendarEvents = async () => {
      if (user) {
        try {
          const response = await fetch(`http://localhost:8000/api/v1/calendar/imap/events/${user.id}`);
          if (response.ok) {
            const data = await response.json();
            setCalendarEvents(data.events || []);
          }
        } catch (error) {
          console.error('Failed to load calendar events:', error);
        }
      }
    };
    loadCalendarEvents();
  }, [user]);

  // Calendar helper functions
  const getDaysInMonth = (date) => {
    const year = date.getFullYear();
    const month = date.getMonth();
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const daysInMonth = lastDay.getDate();
    const startingDayOfWeek = firstDay.getDay();
    
    return { daysInMonth, startingDayOfWeek };
  };

  const getEventsForDate = (date) => {
    const dateStr = date.toISOString().split('T')[0];
    return calendarEvents.filter(event => {
      const eventDate = new Date(event.event_date).toISOString().split('T')[0];
      return eventDate === dateStr;
    });
  };

  const previousMonth = () => {
    setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() - 1));
  };

  const nextMonth = () => {
    setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() + 1));
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

  const loadConversations = async () => {
    try {
      setLoadingConversations(true);
      const data = await conversationService.getConversations();
      
      // Delete empty "New conversation" chats
      const emptyConversations = data.filter(
        conv => conv.title === 'New conversation' && (!conv.messages || conv.messages.length === 0)
      );
      
      for (const emptyConv of emptyConversations) {
        try {
          await conversationService.deleteConversation(emptyConv.id);
        } catch (error) {
          console.error('Error deleting empty conversation:', error);
        }
      }
      
      // Filter out deleted conversations
      const activeConversations = data.filter(
        conv => !(conv.title === 'New conversation' && (!conv.messages || conv.messages.length === 0))
      );
      
      // Group conversations by assistant type
      const grouped = {
        academic: [],
        social: [],
        calendar: []
      };
      
      activeConversations.forEach(conv => {
        if (grouped[conv.assistant_type]) {
          grouped[conv.assistant_type].push({
            id: conv.id,
            title: conv.title,
            messages: conv.messages?.map(msg => ({
              ...msg,
              timestamp: new Date(msg.created_at || msg.timestamp)
            })) || [],
            created_at: new Date(conv.created_at)
          });
        }
      });

      // Create default conversation if none exists for an assistant
      for (const type of ['academic', 'social', 'calendar']) {
        if (grouped[type].length === 0) {
          const newConv = await conversationService.createConversation(type);
          grouped[type].push({
            id: newConv.id,
            title: newConv.title,
            messages: [],
            created_at: new Date(newConv.created_at)
          });
        }
      }

      setConversations(grouped);
      // Set active conversation to the first one of the active assistant
      if (grouped[activeAssistant]?.length > 0) {
        setActiveConversationId(grouped[activeAssistant][0].id);
      }
    } catch (error) {
      console.error('Error loading conversations:', error);
    } finally {
      setLoadingConversations(false);
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [activeConversationId, activeAssistant]);

  const currentAssistant = assistants.find(a => a.id === activeAssistant);
  const currentConversations = conversations[activeAssistant] || [];
  const currentConversation = currentConversations.find(c => c.id === activeConversationId);
  const messages = currentConversation?.messages || [];

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userMessageContent = input.trim();
    setInput('');
    setIsLoading(true);

    try {
      // Add user message to database - backend will automatically generate AI response
      const responseMessage = await conversationService.addMessage(activeConversationId, 'user', userMessageContent);

      // Update local state with user message
      const userMessage = {
        id: Date.now(),
        role: 'user',
        content: userMessageContent,
        timestamp: new Date()
      };

      setConversations(prev => ({
        ...prev,
        [activeAssistant]: prev[activeAssistant].map(conv =>
          conv.id === activeConversationId
            ? { ...conv, messages: [...conv.messages, userMessage] }
            : conv
        )
      }));

      // If backend returned an AI response (for academic or social assistant), use it
      if (responseMessage && responseMessage.role === 'assistant') {
        const aiMessage = {
          id: responseMessage.id,
          role: 'assistant',
          content: responseMessage.content,
          timestamp: new Date(responseMessage.created_at)
        };

        setConversations(prev => ({
          ...prev,
          [activeAssistant]: prev[activeAssistant].map(conv =>
            conv.id === activeConversationId
              ? { 
                  ...conv, 
                  messages: [...conv.messages, aiMessage],
                  title: conv.messages.length === 0 ? userMessageContent.slice(0, 30) + (userMessageContent.length > 30 ? '...' : '') : conv.title
                }
              : conv
          )
        }));
      } else if (activeAssistant === 'calendar') {
        // For calendar assistant, use mock response (not yet implemented with backend)
        const aiContent = getAIResponse(activeAssistant, userMessageContent);
        
        // Add AI message to database
        const aiResponseMessage = await conversationService.addMessage(activeConversationId, 'assistant', aiContent);

        // Update local state with AI message
        const aiMessage = {
          id: aiResponseMessage.id,
          role: 'assistant',
          content: aiContent,
          timestamp: new Date(aiResponseMessage.created_at)
        };

        setConversations(prev => ({
          ...prev,
          [activeAssistant]: prev[activeAssistant].map(conv =>
            conv.id === activeConversationId
              ? { 
                  ...conv, 
                  messages: [...conv.messages, aiMessage],
                  title: conv.messages.length === 0 ? userMessageContent.slice(0, 30) + (userMessageContent.length > 30 ? '...' : '') : conv.title
                }
              : conv
          )
        }));
      }

      setIsLoading(false);
    } catch (error) {
      console.error('Error sending message:', error);
      setIsLoading(false);
    }
  };

  const getAIResponse = (assistant, query) => {
    const lowerQuery = query.toLowerCase();
    
    if (assistant === 'calendar') {
      // Email scanning simulation
      if (lowerQuery.includes('scan') || lowerQuery.includes('email') || lowerQuery.includes('mail')) {
        return `🔍 Scanning your university email for events and deadlines...\n\nFound 4 upcoming events:\n\n📝 **Midterm Exam - Data Structures**\n   Date: November 15, 2025, 10:00 AM\n   Location: Engineering Building, Room 301\n   Duration: 2 hours\n\n📚 **Assignment Deadline - Machine Learning Project**\n   Due: November 20, 2025, 11:59 PM\n   Submit to: Canvas LMS\n\n🧪 **Lab Session - Chemistry 201**\n   Date: November 12, 2025, 2:00 PM\n   Location: Science Lab 4\n   Duration: 3 hours\n\n📖 **Quiz - Calculus II**\n   Date: November 18, 2025, 9:00 AM\n   Location: Mathematics Building, Room 205\n   Duration: 1 hour\n\n✅ Would you like to:\n1. Add all events to your calendar\n2. Edit specific events before adding\n3. Remove some events\n\nJust let me know which events you'd like to add!`;
      }
      
      // Confirmation responses
      if (lowerQuery.includes('add all') || lowerQuery.includes('confirm') || lowerQuery.includes('yes')) {
        return `✅ Perfect! I've added all 4 events to your Google Calendar:\n\n✓ Midterm Exam - Data Structures (Nov 15)\n✓ Assignment Deadline - ML Project (Nov 20)\n✓ Lab Session - Chemistry 201 (Nov 12)\n✓ Quiz - Calculus II (Nov 18)\n\n🔔 You'll receive notifications:\n- 1 day before each event\n- 1 hour before each event\n\nYour calendar is now synced! You can view these events in Google Calendar or ask me about your upcoming schedule anytime.`;
      }
      
      // General calendar help
      return `I can help manage your academic schedule! Here's what I can do:\n\n📧 **Scan Emails**: I'll scan your university email to find:\n   • Exam dates\n   • Assignment deadlines\n   • Lab sessions\n   • Quiz schedules\n   • Campus events\n\n📅 **Calendar Management**: \n   • Add events to Google Calendar\n   • Edit event details\n   • Set custom reminders\n   • View upcoming schedule\n\n💡 Try saying: "Scan my emails" or "Check my calendar"`;
    }
    
    if (assistant === 'academic') {
      return `I understand you're asking about "${query}". As your Academic Assistant, I have access to TED University's course database and can provide detailed information about courses, prerequisites, and academic requirements.\n\nIn the full implementation with RAG (Retrieval-Augmented Generation), I'll search through syllabus documents and provide accurate, context-aware responses based on official university materials.`;
    }
    
    if (assistant === 'social') {
      return `Thanks for your question about "${query}"! I can help you discover social opportunities at TED University.\n\nWith the complete system, I'll have real-time access to club information, event calendars, and student activities. I can help you find groups that match your interests and connect you with campus resources.`;
    }
    
    return 'I can help you with that!';
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const createNewConversation = async () => {
    try {
      const newConv = await conversationService.createConversation(activeAssistant);
      const conversation = {
        id: newConv.id,
        title: newConv.title,
        messages: [],
        created_at: new Date(newConv.created_at)
      };
      
      setConversations(prev => ({
        ...prev,
        [activeAssistant]: [conversation, ...prev[activeAssistant]]
      }));
      setActiveConversationId(newConv.id);
    } catch (error) {
      console.error('Error creating conversation:', error);
    }
  };

  const deleteConversation = async (convId) => {
    try {
      await conversationService.deleteConversation(convId);
      
      setConversations(prev => {
        const filtered = prev[activeAssistant].filter(c => c.id !== convId);
        return { ...prev, [activeAssistant]: filtered };
      });
      
      // Set active to first conversation or create new one
      const remaining = conversations[activeAssistant].filter(c => c.id !== convId);
      if (remaining.length > 0) {
        setActiveConversationId(remaining[0].id);
      } else {
        createNewConversation();
      }
    } catch (error) {
      console.error('Error deleting conversation:', error);
    }
  };

  return (
    <div className={`flex h-screen ${isDark ? 'bg-gray-950' : 'bg-white'}`}>
      {/* Sidebar */}
      <AnimatePresence>
        {sidebarOpen && (
          <motion.div
            initial={{ x: -300 }}
            animate={{ x: 0 }}
            exit={{ x: -300 }}
            className={`w-80 ${isDark ? 'bg-gray-900 border-gray-800' : 'bg-gray-50 border-gray-200'} flex flex-col border-r`}
          >
            {/* Sidebar Header */}
            <div className={`p-4 border-b ${isDark ? 'border-gray-800' : 'border-gray-200'}`}>
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <img src="/SAGE_logo.jpg" alt="SAGE" className="w-8 h-8 rounded-lg" />
                  <div>
                    <h2 className={`font-semibold text-sm ${isDark ? 'text-white' : 'text-gray-900'}`}>SAGE</h2>
                    <p className="text-gray-400 text-xs">AI Guide</p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={toggleTheme}
                    className={`p-2 rounded-lg ${isDark ? 'hover:bg-gray-800 text-gray-400' : 'hover:bg-gray-200 text-gray-600'}`}
                    title={isDark ? 'Light mode' : 'Dark mode'}
                  >
                    {isDark ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
                  </button>
                  <button
                    onClick={() => setSidebarOpen(false)}
                    className={`lg:hidden p-1 ${isDark ? 'text-gray-400 hover:text-white' : 'text-gray-600 hover:text-gray-900'}`}
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>
              </div>

              {/* New Chat Button - Only show for Academic and Social assistants */}
              {activeAssistant !== 'calendar' && (
                <button
                  onClick={createNewConversation}
                  className={`w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg border transition-colors ${
                    isDark 
                      ? 'border-gray-700 hover:bg-gray-800 text-gray-300' 
                      : 'border-gray-300 hover:bg-gray-100 text-gray-700'
                  }`}
                >
                  <Plus className="w-4 h-4" />
                  <span className="font-medium">New Chat</span>
                </button>
              )}
            </div>

            {/* Assistant Tabs */}
            <div className={`flex border-b ${isDark ? 'border-gray-800' : 'border-gray-200'}`}>
              {assistants.map((assistant) => (
                <button
                  key={assistant.id}
                  onClick={() => {
                    setActiveAssistant(assistant.id);
                    const firstConv = conversations[assistant.id]?.[0];
                    if (firstConv) setActiveConversationId(firstConv.id);
                  }}
                  className={`flex-1 flex flex-col items-center gap-1 py-3 border-b-2 transition-colors ${
                    activeAssistant === assistant.id
                      ? `${assistant.color} text-white border-${assistant.color.split('-')[1]}-600`
                      : isDark 
                        ? 'border-transparent text-gray-400 hover:text-gray-300' 
                        : 'border-transparent text-gray-500 hover:text-gray-700'
                  }`}
                >
                  <assistant.icon className="w-4 h-4" />
                  <span className="text-xs font-medium">{assistant.name.split(' ')[0]}</span>
                </button>
              ))}
            </div>

            {/* Conversations List - Only show for Academic and Social assistants */}
            {activeAssistant !== 'calendar' ? (
              <div className="flex-1 overflow-y-auto">
                {loadingConversations ? (
                  <div className="flex items-center justify-center p-8">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                  </div>
                ) : (
                  <div className="p-2 space-y-1">
                    {currentConversations.map((conv) => (
                      <div
                        key={conv.id}
                        className={`group flex items-center gap-2 px-3 py-2.5 rounded-lg cursor-pointer transition-colors ${
                          activeConversationId === conv.id
                            ? isDark 
                              ? 'bg-gray-800 text-white' 
                              : 'bg-gray-200 text-gray-900'
                            : isDark
                              ? 'hover:bg-gray-800 text-gray-300'
                              : 'hover:bg-gray-100 text-gray-700'
                        }`}
                        onClick={() => setActiveConversationId(conv.id)}
                      >
                        <MessageSquare className="w-4 h-4 flex-shrink-0" />
                        <span className="flex-1 text-sm truncate">{conv.title}</span>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            deleteConversation(conv.id);
                          }}
                          className={`opacity-0 group-hover:opacity-100 p-1 rounded ${
                            isDark ? 'hover:bg-gray-700' : 'hover:bg-gray-300'
                          }`}
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ) : (
              /* Calendar Assistant - Show helpful info instead of conversations */
              <div className="flex-1 flex items-center justify-center p-6">
                <div className="text-center">
                  <CalendarIcon className={`w-12 h-12 mx-auto mb-3 ${isDark ? 'text-gray-600' : 'text-gray-400'}`} />
                  <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                    Calendar & Email Manager
                  </p>
                  <p className={`text-xs mt-1 ${isDark ? 'text-gray-500' : 'text-gray-500'}`}>
                    Sign in with Gmail to manage your calendar
                  </p>
                </div>
              </div>
            )}

            {/* User Section */}
            <div className={`p-4 border-t ${isDark ? 'border-gray-800' : 'border-gray-200'}`}>
              <div className="flex items-center gap-3 mb-3">
                <div className={`w-10 h-10 rounded-full ${isDark ? 'bg-gray-800' : 'bg-gray-200'} flex items-center justify-center`}>
                  <UserIcon className={`w-5 h-5 ${isDark ? 'text-gray-400' : 'text-gray-600'}`} />
                </div>
                <div className="flex-1 min-w-0">
                  <p className={`text-sm font-medium truncate ${isDark ? 'text-white' : 'text-gray-900'}`}>
                    {user?.full_name || 'User'}
                  </p>
                  <p className="text-xs text-gray-400 truncate">{user?.email}</p>
                </div>
              </div>
              <div className="flex gap-2">
                {user?.is_superuser && (
                  <button
                    onClick={() => navigate('/users')}
                    className={`flex-1 flex items-center justify-center gap-2 px-3 py-2 rounded-lg transition-colors ${
                      isDark
                        ? 'bg-purple-600 hover:bg-purple-700 text-white'
                        : 'bg-purple-500 hover:bg-purple-600 text-white'
                    }`}
                  >
                    <Shield className="w-4 h-4" />
                    <span className="text-sm">Admin</span>
                  </button>
                )}
                <button
                  onClick={() => setShowUserModal(true)}
                  className={`flex-1 flex items-center justify-center gap-2 px-3 py-2 rounded-lg transition-colors ${
                    isDark
                      ? 'bg-gray-800 hover:bg-gray-700 text-gray-300'
                      : 'bg-gray-200 hover:bg-gray-300 text-gray-700'
                  }`}
                >
                  <Settings className="w-4 h-4" />
                </button>
                <button
                  onClick={logout}
                  className={`flex-1 flex items-center justify-center gap-2 px-3 py-2 rounded-lg transition-colors ${
                    isDark
                      ? 'bg-gray-800 hover:bg-gray-700 text-red-400'
                      : 'bg-gray-200 hover:bg-gray-300 text-red-600'
                  }`}
                >
                  <LogOut className="w-4 h-4" />
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Conditional Rendering: Calendar Page or Chat Interface */}
        {activeAssistant === 'calendar' ? (
          /* Calendar Assistant - Show CalendarPage Component */
          <div className="flex-1 overflow-hidden">
            <CalendarPage />
          </div>
        ) : (
          /* Academic & Social Assistants - Show Chat Interface */
          <>
            {/* Header */}
            <div className={`border-b ${isDark ? 'border-gray-800 bg-gray-900' : 'border-gray-200 bg-white'} px-4 py-4`}>
              <div className="flex items-center gap-3">
                {!sidebarOpen && (
                  <button
                    onClick={() => setSidebarOpen(true)}
                    className={`p-2 rounded-lg ${isDark ? 'hover:bg-gray-800 text-gray-400' : 'hover:bg-gray-100 text-gray-600'}`}
                  >
                    <Menu className="w-5 h-5" />
                  </button>
                )}
                <div className={`w-10 h-10 rounded-full bg-gradient-to-r ${currentAssistant.gradient} flex items-center justify-center`}>
                  <currentAssistant.icon className="w-5 h-5 text-white" />
                </div>
                <div className="flex-1">
                  <h1 className={`text-lg font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>
                    {currentAssistant.name}
                  </h1>
                  <p className="text-sm text-gray-400">{currentAssistant.description}</p>
                </div>
                
                {/* Calendar Icon Button */}
                <button
                  onClick={() => setShowCalendarPopup(true)}
                  className={`relative p-2 rounded-lg ${isDark ? 'hover:bg-gray-800 text-gray-400 hover:text-white' : 'hover:bg-gray-100 text-gray-600 hover:text-gray-900'} transition-colors`}
                  title="Quick Calendar"
                >
                  <CalendarIcon className="w-6 h-6" />
                  {calendarEvents.length > 0 && (
                    <span className="absolute -top-1 -right-1 bg-primary-600 text-white text-xs font-bold rounded-full w-5 h-5 flex items-center justify-center">
                      {calendarEvents.length > 9 ? '9+' : calendarEvents.length}
                    </span>
                  )}
                </button>
              </div>
            </div>

            {/* Messages Area */}
            <div className={`flex-1 overflow-y-auto ${isDark ? 'bg-gray-950' : 'bg-white'}`}>
          {messages.length === 0 ? (
            /* Welcome Screen */
            <div className="h-full flex flex-col items-center justify-center p-8">
              <div className={`w-16 h-16 rounded-full bg-gradient-to-r ${currentAssistant.gradient} flex items-center justify-center mb-4`}>
                <currentAssistant.icon className="w-8 h-8 text-white" />
              </div>
              <h2 className={`text-2xl font-bold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
                {currentAssistant.name}
              </h2>
              <p className="text-gray-400 text-center max-w-md mb-8">
                {currentAssistant.description}
              </p>
            </div>
          ) : (
            /* Messages */
            <div className="max-w-4xl mx-auto px-4 py-6 space-y-6">
              {messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex gap-4 ${message.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}
                >
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                    message.role === 'user'
                      ? isDark ? 'bg-gray-700' : 'bg-gray-900'
                      : `bg-gradient-to-r ${currentAssistant.gradient}`
                  }`}>
                    {message.role === 'user' ? (
                      <UserIcon className="w-5 h-5 text-white" />
                    ) : (
                      <Bot className="w-5 h-5 text-white" />
                    )}
                  </div>
                  <div className="flex-1 space-y-2">
                    <div className="flex items-center gap-2">
                      <span className={`text-sm font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>
                        {message.role === 'user' ? 'You' : currentAssistant.name}
                      </span>
                      <span className="text-xs text-gray-400">
                        {message.timestamp.toLocaleTimeString()}
                      </span>
                    </div>
                    <div className={`prose prose-sm max-w-none ${isDark ? 'prose-invert' : ''}`}>
                      {message.role === 'assistant' ? (
                        <ReactMarkdown 
                          remarkPlugins={[remarkGfm]}
                          className={`leading-relaxed ${isDark ? 'text-gray-300' : 'text-gray-800'}`}
                          components={{
                            // Style headers
                            h1: ({node, ...props}) => <h1 className={`text-2xl font-bold mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`} {...props} />,
                            h2: ({node, ...props}) => <h2 className={`text-xl font-bold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`} {...props} />,
                            h3: ({node, ...props}) => <h3 className={`text-lg font-semibold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`} {...props} />,
                            // Style lists
                            ul: ({node, ...props}) => <ul className="list-disc pl-5 space-y-1 mb-3" {...props} />,
                            ol: ({node, ...props}) => <ol className="list-decimal pl-5 space-y-1 mb-3" {...props} />,
                            li: ({node, ...props}) => <li className={`${isDark ? 'text-gray-300' : 'text-gray-800'}`} {...props} />,
                            // Style paragraphs
                            p: ({node, ...props}) => <p className="mb-3 leading-relaxed" {...props} />,
                            // Style strong/bold
                            strong: ({node, ...props}) => <strong className={`font-bold ${isDark ? 'text-white' : 'text-gray-900'}`} {...props} />,
                            // Style code
                            code: ({node, inline, ...props}) => 
                              inline ? 
                                <code className={`px-1.5 py-0.5 rounded text-sm font-mono ${isDark ? 'bg-gray-800 text-blue-400' : 'bg-gray-100 text-blue-600'}`} {...props} /> :
                                <code className={`block p-3 rounded-lg text-sm font-mono ${isDark ? 'bg-gray-800 text-gray-300' : 'bg-gray-100 text-gray-800'}`} {...props} />,
                            // Style links
                            a: ({node, ...props}) => <a className="text-blue-500 hover:underline" target="_blank" rel="noopener noreferrer" {...props} />
                          }}
                        >
                          {message.content}
                        </ReactMarkdown>
                      ) : (
                        <p className={`whitespace-pre-wrap leading-relaxed ${isDark ? 'text-gray-300' : 'text-gray-800'}`}>
                          {message.content}
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              ))}

              {isLoading && (
                <div className="flex gap-4">
                  <div className={`w-8 h-8 rounded-full bg-gradient-to-r ${currentAssistant.gradient} flex items-center justify-center`}>
                    <Bot className="w-5 h-5 text-white" />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2 text-sm text-gray-500">
                      <div className="flex gap-1">
                        <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></span>
                        <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></span>
                        <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></span>
                      </div>
                      <span>Thinking...</span>
                    </div>
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>
          )}
            </div>

            {/* Input Area */}
            <div className={`border-t ${isDark ? 'border-gray-800 bg-gray-900' : 'border-gray-200 bg-white'} p-4`}>
          <div className="max-w-4xl mx-auto">
            <div className="flex gap-3 items-end">
              <div className="flex-1 relative">
                <textarea
                  ref={textareaRef}
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder={`Message ${currentAssistant.name}...`}
                  rows="1"
                  className={`w-full px-4 py-3 pr-12 border rounded-2xl focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none max-h-40 ${
                    isDark 
                      ? 'bg-gray-800 border-gray-700 text-white placeholder-gray-400' 
                      : 'bg-white border-gray-300 text-gray-900 placeholder-gray-500'
                  }`}
                  style={{ minHeight: '52px' }}
                />
              </div>
              <button
                onClick={handleSend}
                disabled={!input.trim() || isLoading}
                className={`p-3 rounded-xl transition-all ${
                  input.trim() && !isLoading
                    ? `${currentAssistant.color} hover:opacity-90 text-white`
                    : isDark 
                      ? 'bg-gray-800 text-gray-600 cursor-not-allowed' 
                      : 'bg-gray-200 text-gray-400 cursor-not-allowed'
                }`}
              >
                <Send className="w-5 h-5" />
              </button>
            </div>
            <p className="text-xs text-gray-500 text-center mt-2">
              SAGE can make mistakes. Check important information.
            </p>
          </div>
            </div>
          </>
        )}
      </div>

      {/* User Profile Modal */}
      {showUserModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <motion.div
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            className={`rounded-2xl shadow-2xl max-w-md w-full p-6 ${isDark ? 'bg-gray-900' : 'bg-white'}`}
          >
            <div className="flex items-center justify-between mb-6">
              <h2 className={`text-2xl font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>Edit Profile</h2>
              <button
                onClick={() => setShowUserModal(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="w-6 h-6" />
              </button>
            </div>
            <form onSubmit={(e) => {
              e.preventDefault();
              // TODO: API call to update user
              setShowUserModal(false);
            }} className="space-y-4">
              <div>
                <label className={`block text-sm font-medium mb-2 ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>Full Name</label>
                <input
                  type="text"
                  value={userFormData.full_name}
                  onChange={(e) => setUserFormData({ ...userFormData, full_name: e.target.value })}
                  className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                    isDark 
                      ? 'bg-gray-800 border-gray-700 text-white' 
                      : 'bg-white border-gray-300 text-gray-900'
                  }`}
                  placeholder="John Doe"
                />
              </div>
              <div>
                <label className={`block text-sm font-medium mb-2 ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>Email</label>
                <input
                  type="email"
                  value={userFormData.email}
                  onChange={(e) => setUserFormData({ ...userFormData, email: e.target.value })}
                  className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                    isDark 
                      ? 'bg-gray-800 border-gray-700 text-white' 
                      : 'bg-white border-gray-300 text-gray-900'
                  }`}
                  placeholder="student@tedu.edu.tr"
                />
              </div>
              <div className="flex gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => setShowUserModal(false)}
                  className={`flex-1 px-4 py-2 border rounded-lg ${
                    isDark
                      ? 'border-gray-700 text-gray-300 hover:bg-gray-800'
                      : 'border-gray-300 text-gray-700 hover:bg-gray-50'
                  }`}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="flex-1 px-4 py-2 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg hover:shadow-lg"
                >
                  <div className="flex items-center justify-center gap-2">
                    <Save className="w-4 h-4" />
                    Save Changes
                  </div>
                </button>
              </div>
            </form>
          </motion.div>
        </div>
      )}

      {/* Calendar Popup */}
      {showCalendarPopup && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4" onClick={() => setShowCalendarPopup(false)}>
          <div className="bg-dark-800 border-2 border-primary-500/50 rounded-xl max-w-6xl w-full max-h-[90vh] overflow-y-auto shadow-2xl" onClick={(e) => e.stopPropagation()}>
            {/* Header */}
            <div className="sticky top-0 bg-gradient-to-r from-primary-600 to-purple-600 p-6 rounded-t-xl z-10">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <CalendarIcon className="w-8 h-8 text-white" />
                  <div>
                    <h2 className="text-2xl font-bold text-white">Calendar View</h2>
                    <p className="text-white/80 text-sm">{calendarEvents.length} event{calendarEvents.length !== 1 ? 's' : ''} total</p>
                  </div>
                </div>
                <button
                  onClick={() => setShowCalendarPopup(false)}
                  className="text-white hover:bg-white/20 rounded-lg p-2 transition-colors"
                >
                  <X className="w-6 h-6" />
                </button>
              </div>

              {/* Calendar Navigation */}
              <div className="flex items-center justify-between mt-4">
                <div className="flex items-center gap-4">
                  <h3 className="text-xl font-bold text-white">{currentDate.toLocaleDateString('en-US', { month: 'long', year: 'numeric' })}</h3>
                  <button
                    onClick={() => setCurrentDate(new Date())}
                    className="px-3 py-1 bg-white/20 hover:bg-white/30 rounded-lg text-sm font-medium transition-colors text-white"
                  >
                    Today
                  </button>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={previousMonth}
                    className="p-2 hover:bg-white/20 rounded-lg transition-colors text-white"
                  >
                    <ChevronLeft className="w-5 h-5" />
                  </button>
                  <button
                    onClick={nextMonth}
                    className="p-2 hover:bg-white/20 rounded-lg transition-colors text-white"
                  >
                    <ChevronRight className="w-5 h-5" />
                  </button>
                </div>
              </div>
            </div>

            {/* Calendar Grid */}
            <div className="p-6">
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
                    const today = new Date();
                    
                    // Previous month's trailing days
                    const prevMonth = new Date(currentDate.getFullYear(), currentDate.getMonth(), 0);
                    const prevMonthDays = prevMonth.getDate();
                    for (let i = startingDayOfWeek - 1; i >= 0; i--) {
                      const day = prevMonthDays - i;
                      days.push(
                        <div key={`prev-${day}`} className="min-h-[120px] p-3 bg-dark-900/30 border-r border-b border-dark-700/50">
                          <div className="text-sm text-dark-600 mb-2">{day}</div>
                        </div>
                      );
                    }
                    
                    // Current month days
                    for (let day = 1; day <= daysInMonth; day++) {
                      const date = new Date(currentDate.getFullYear(), currentDate.getMonth(), day);
                      const dayEvents = getEventsForDate(date);
                      const isToday = date.toDateString() === today.toDateString();
                      
                      days.push(
                        <div
                          key={day}
                          className={`min-h-[120px] p-3 border-r border-b border-dark-700 ${
                            isToday ? 'bg-primary-900/20' : 'bg-dark-900/50'
                          } hover:bg-dark-800/50 transition-colors`}
                        >
                          <div className={`text-sm font-semibold mb-2 ${
                            isToday ? 'text-primary-400' : 'text-white'
                          }`}>
                            {day}
                          </div>
                          <div className="space-y-1">
                            {dayEvents.slice(0, 3).map((event, idx) => (
                              <div
                                key={idx}
                                onClick={() => {
                                  setSelectedEvent(event);
                                  setShowCalendarPopup(false);
                                }}
                                className={`text-xs px-2 py-1 rounded truncate ${getEventTypeColor(event.event_type)} text-white cursor-pointer hover:opacity-80 transition-opacity`}
                                title={`${event.title} - ${new Date(event.event_date).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })}`}
                              >
                                <div className="font-medium">{new Date(event.event_date).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })}</div>
                                <div className="truncate">{event.title}</div>
                              </div>
                            ))}
                            {dayEvents.length > 3 && (
                              <div 
                                className="text-[10px] text-primary-400 pl-1 cursor-pointer hover:text-primary-300"
                                onClick={() => {
                                  setSelectedEvent({ 
                                    title: `All Events (${date.toLocaleDateString()})`,
                                    description: 'Multiple events on this day',
                                    allDayEvents: dayEvents
                                  });
                                  setShowCalendarPopup(false);
                                }}
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
                    const remainingCells = 35 - totalCells;
                    for (let i = 1; i <= remainingCells; i++) {
                      days.push(
                        <div key={`next-${i}`} className="min-h-[120px] p-3 bg-dark-900/30 border-r border-b border-dark-700/50">
                          <div className="text-sm text-dark-600 mb-2">{i}</div>
                        </div>
                      );
                    }
                    
                    return days;
                  })()}
                </div>
              </div>

              {/* Event Legend */}
              <div className="mt-6 p-4 bg-dark-900/50 border border-dark-700 rounded-lg">
                <h4 className="text-sm font-semibold mb-3 text-white">Event Types</h4>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                  {[
                    { type: 'academic', label: 'Academic' },
                    { type: 'social', label: 'Social' },
                    { type: 'student_activity', label: 'Student Activity' },
                    { type: 'career', label: 'Career' },
                    { type: 'other', label: 'Other' }
                  ].map(({ type, label }) => (
                    <div key={type} className="flex items-center gap-2">
                      <div className={`w-3 h-3 rounded ${getEventTypeColor(type)}`} />
                      <span className="text-sm text-dark-300">{label}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Event Detail Modal */}
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
          </div>
        </div>
      )}
    </div>
  );
}
