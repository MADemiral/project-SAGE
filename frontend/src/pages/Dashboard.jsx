import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
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
  Shield
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import { useNavigate } from 'react-router-dom';
import { conversationService } from '../services/conversations';

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
  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);

  // Load conversations from API on mount
  useEffect(() => {
    loadConversations();
  }, []);

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
              timestamp: new Date(msg.timestamp)
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
      // Add user message to database
      await conversationService.addMessage(activeConversationId, 'user', userMessageContent);

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

      // Simulate AI response (in production, this would call your LLM)
      setTimeout(async () => {
        const aiContent = getAIResponse(activeAssistant, userMessageContent);
        
        // Add AI message to database
        await conversationService.addMessage(activeConversationId, 'assistant', aiContent);

        // Update local state with AI message
        const aiMessage = {
          id: Date.now() + 1,
          role: 'assistant',
          content: aiContent,
          timestamp: new Date()
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

        setIsLoading(false);
      }, 1000 + Math.random() * 1000);
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

              {/* New Chat Button */}
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

            {/* Conversations List */}
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
                    <div className="prose prose-sm max-w-none">
                      <p className={`whitespace-pre-wrap leading-relaxed ${isDark ? 'text-gray-300' : 'text-gray-800'}`}>
                        {message.content}
                      </p>
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
    </div>
  );
}
