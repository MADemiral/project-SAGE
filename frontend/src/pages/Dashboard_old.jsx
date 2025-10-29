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
  Edit3,
  Sparkles,
  Bot,
  User as UserIcon,
  LogOut,
  Settings,
  Mail,
  Save,
  ScanLine
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';

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
    description: 'Schedule management and deadlines'
  }
];

export default function Dashboard() {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [activeAssistant, setActiveAssistant] = useState('academic');
  const [conversations, setConversations] = useState(() => {
    // Load from localStorage
    const saved = localStorage.getItem('sage_conversations');
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        // Convert timestamp strings back to Date objects
        Object.keys(parsed).forEach(key => {
          parsed[key].forEach(conv => {
            conv.messages = conv.messages.map(msg => ({
              ...msg,
              timestamp: new Date(msg.timestamp)
            }));
          });
        });
        return parsed;
      } catch (e) {
        console.error('Error loading conversations:', e);
      }
    }
    return {
      academic: [{ id: 1, title: 'New conversation', messages: [] }],
      social: [{ id: 1, title: 'New conversation', messages: [] }],
      calendar: [{ id: 1, title: 'New conversation', messages: [] }]
    };
  });
  const [activeConversationId, setActiveConversationId] = useState(1);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [showUserModal, setShowUserModal] = useState(false);
  const [userFormData, setUserFormData] = useState({
    full_name: user?.full_name || '',
    email: user?.email || ''
  });
  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);

  // Save conversations to localStorage whenever they change
  useEffect(() => {
    localStorage.setItem('sage_conversations', JSON.stringify(conversations));
  }, [conversations]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [activeConversationId, activeAssistant]);

  useEffect(() => {
    // Initialize with welcome message
    const welcomeMessages = {
      academic: `Hello! 👋 I'm your Academic Assistant. I can help you with:\n\n• Course selection and recommendations\n• Understanding syllabus and requirements\n• Academic planning and scheduling\n• Study resources and materials\n\nWhat would you like to know about your courses?`,
      social: `Hey there! 🎉 I'm your Social Assistant. I can help you:\n\n• Discover student clubs and organizations\n• Find campus events and activities\n• Connect with other students\n• Navigate campus facilities\n\nHow can I help you get involved at TED University?`,
      calendar: `Hi! 📅 I'm your Calendar Assistant. I can assist with:\n\n• Tracking exam and assignment deadlines\n• Managing your academic schedule\n• Scanning emails for important dates\n• Syncing with Google Calendar\n\nWould you like me to help organize your schedule?`
    };

    setConversations(prev => {
      const updated = { ...prev };
      Object.keys(welcomeMessages).forEach(key => {
        if (updated[key][0].messages.length === 0) {
          updated[key][0].messages = [{
            id: 1,
            role: 'assistant',
            content: welcomeMessages[key],
            timestamp: new Date()
          }];
        }
      });
      return updated;
    });
  }, []);

  const currentAssistant = assistants.find(a => a.id === activeAssistant);
  const currentConversations = conversations[activeAssistant] || [];
  const currentConversation = currentConversations.find(c => c.id === activeConversationId) || currentConversations[0];
  const messages = currentConversation?.messages || [];

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage = {
      id: Date.now(),
      role: 'user',
      content: input.trim(),
      timestamp: new Date()
    };

    // Add user message
    setConversations(prev => ({
      ...prev,
      [activeAssistant]: prev[activeAssistant].map(conv =>
        conv.id === activeConversationId
          ? {
              ...conv,
              messages: [...conv.messages, userMessage],
              title: conv.messages.length === 1 ? input.trim().slice(0, 30) + '...' : conv.title
            }
          : conv
      )
    }));

    setInput('');
    setIsLoading(true);

    // Simulate AI response
    setTimeout(() => {
      const aiResponse = {
        id: Date.now() + 1,
        role: 'assistant',
        content: getAIResponse(activeAssistant, input.trim()),
        timestamp: new Date()
      };

      setConversations(prev => ({
        ...prev,
        [activeAssistant]: prev[activeAssistant].map(conv =>
          conv.id === activeConversationId
            ? { ...conv, messages: [...conv.messages, aiResponse] }
            : conv
        )
      }));

      setIsLoading(false);
    }, 1000 + Math.random() * 1000);
  };

  const getAIResponse = (assistant, query) => {
    const responses = {
      academic: `I understand you're asking about "${query}". As your Academic Assistant, I have access to TED University's course database and can provide detailed information about courses, prerequisites, and academic requirements.\n\nIn the full implementation with RAG (Retrieval-Augmented Generation), I'll search through syllabus documents and provide accurate, context-aware responses based on official university materials.`,
      social: `Thanks for your question about "${query}"! I can help you discover social opportunities at TED University.\n\nWith the complete system, I'll have real-time access to club information, event calendars, and student activities. I can help you find groups that match your interests and connect you with campus resources.`,
      calendar: `I see you mentioned "${query}". I can help manage your academic schedule effectively.\n\nOnce fully integrated, I'll scan your university emails to automatically detect exam dates, assignment deadlines, and important events, then sync them with your Google Calendar for seamless schedule management.`
    };
    return responses[assistant] || 'I can help you with that!';
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const createNewConversation = () => {
    const newId = Date.now();
    setConversations(prev => ({
      ...prev,
      [activeAssistant]: [
        { id: newId, title: 'New conversation', messages: [] },
        ...prev[activeAssistant]
      ]
    }));
    setActiveConversationId(newId);
  };

  const deleteConversation = (convId) => {
    setConversations(prev => {
      const filtered = prev[activeAssistant].filter(c => c.id !== convId);
      if (filtered.length === 0) {
        filtered.push({ id: Date.now(), title: 'New conversation', messages: [] });
      }
      return { ...prev, [activeAssistant]: filtered };
    });
    if (activeConversationId === convId) {
      setActiveConversationId(conversations[activeAssistant][0]?.id || Date.now());
    }
  };

  return (
    <div className="flex h-screen bg-white">
      {/* Sidebar */}
      <AnimatePresence>
        {sidebarOpen && (
          <motion.div
            initial={{ x: -300 }}
            animate={{ x: 0 }}
            exit={{ x: -300 }}
            className="w-80 bg-gray-900 flex flex-col border-r border-gray-800"
          >
            {/* Sidebar Header */}
            <div className="p-4 border-b border-gray-800">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <img src="/SAGE_logo.jpg" alt="SAGE" className="w-8 h-8 rounded-lg" />
                  <div>
                    <h2 className="text-white font-semibold text-sm">SAGE</h2>
                    <p className="text-gray-400 text-xs">AI Guide</p>
                  </div>
                </div>
                <button
                  onClick={() => setSidebarOpen(false)}
                  className="lg:hidden text-gray-400 hover:text-white p-1"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* New Chat Button */}
              <button
                onClick={createNewConversation}
                className="w-full flex items-center gap-2 px-4 py-2.5 bg-gray-800 hover:bg-gray-700 text-white rounded-lg transition-colors"
              >
                <Plus className="w-4 h-4" />
                <span className="text-sm font-medium">New Chat</span>
              </button>
            </div>

            {/* Assistant Selector */}
            <div className="p-3 border-b border-gray-800">
              <p className="text-xs text-gray-400 mb-2 px-2">SELECT ASSISTANT</p>
              <div className="space-y-1">
                {assistants.map((assistant) => {
                  const Icon = assistant.icon;
                  const isActive = activeAssistant === assistant.id;
                  return (
                    <button
                      key={assistant.id}
                      onClick={() => {
                        setActiveAssistant(assistant.id);
                        setActiveConversationId(conversations[assistant.id][0]?.id);
                      }}
                      className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all ${
                        isActive
                          ? `${assistant.color} text-white`
                          : 'text-gray-300 hover:bg-gray-800'
                      }`}
                    >
                      <Icon className="w-5 h-5" />
                      <div className="text-left flex-1">
                        <div className="text-sm font-medium">{assistant.name.replace(' Assistant', '')}</div>
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Conversations List */}
            <div className="flex-1 overflow-y-auto p-3">
              <p className="text-xs text-gray-400 mb-2 px-2">CONVERSATIONS</p>
              <div className="space-y-1">
                {currentConversations.map((conv) => (
                  <div
                    key={conv.id}
                    className={`group flex items-center gap-2 px-3 py-2 rounded-lg cursor-pointer transition-colors ${
                      activeConversationId === conv.id
                        ? 'bg-gray-800 text-white'
                        : 'text-gray-300 hover:bg-gray-800'
                    }`}
                    onClick={() => setActiveConversationId(conv.id)}
                  >
                    <MessageSquare className="w-4 h-4 flex-shrink-0" />
                    <span className="flex-1 text-sm truncate">{conv.title}</span>
                    {currentConversations.length > 1 && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          deleteConversation(conv.id);
                        }}
                        className="opacity-0 group-hover:opacity-100 text-gray-400 hover:text-red-400 transition-opacity"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* User Info */}
            <div className="p-4 border-t border-gray-800">
              <div className="flex items-center gap-3 mb-3">
                <div className={`w-8 h-8 rounded-full bg-gradient-to-r ${currentAssistant.gradient} flex items-center justify-center`}>
                  <UserIcon className="w-4 h-4 text-white" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-white truncate">{user?.full_name || user?.username}</p>
                  <p className="text-xs text-gray-400 truncate">{user?.email}</p>
                </div>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => setShowUserModal(true)}
                  className="flex-1 flex items-center justify-center gap-2 px-3 py-2 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-lg transition-colors text-sm"
                >
                  <Settings className="w-4 h-4" />
                  <span>Profile</span>
                </button>
                <button
                  onClick={() => {
                    logout();
                    navigate('/login');
                  }}
                  className="flex-1 flex items-center justify-center gap-2 px-3 py-2 bg-red-600/20 hover:bg-red-600/30 text-red-400 rounded-lg transition-colors text-sm"
                >
                  <LogOut className="w-4 h-4" />
                  <span>Logout</span>
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Top Bar */}
        <div className="h-14 border-b border-gray-200 flex items-center justify-between px-4 bg-white">
          <div className="flex items-center gap-3">
            {!sidebarOpen && (
              <button
                onClick={() => setSidebarOpen(true)}
                className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <Menu className="w-5 h-5 text-gray-600" />
              </button>
            )}
            <div className="flex items-center gap-2">
              <currentAssistant.icon className={`w-5 h-5 ${currentAssistant.color.replace('bg-', 'text-')}`} />
              <h1 className="font-semibold text-gray-900">{currentAssistant.name}</h1>
            </div>
          </div>
        </div>

        {/* Messages Area */}
        <div className="flex-1 overflow-y-auto">
          {messages.length === 0 ? (
            /* Empty State */
            <div className="h-full flex items-center justify-center p-8">
              <div className="text-center max-w-2xl">
                <div className={`w-16 h-16 rounded-2xl bg-gradient-to-r ${currentAssistant.gradient} flex items-center justify-center mx-auto mb-4`}>
                  <currentAssistant.icon className="w-8 h-8 text-white" />
                </div>
                <h2 className="text-2xl font-bold text-gray-900 mb-2">{currentAssistant.name}</h2>
                <p className="text-gray-600 mb-6">{currentAssistant.description}</p>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-left">
                  {['How can I help you today?', 'Ask me anything!', 'Start a conversation', 'I\'m here to assist'].map((prompt, i) => (
                    <button
                      key={i}
                      onClick={() => setInput(prompt)}
                      className="p-4 border border-gray-200 rounded-xl hover:border-gray-300 hover:bg-gray-50 transition-all text-sm text-gray-700"
                    >
                      "{prompt}"
                    </button>
                  ))}
                </div>
              </div>
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
                      ? 'bg-gray-900'
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
                      <span className="text-sm font-semibold text-gray-900">
                        {message.role === 'user' ? 'You' : currentAssistant.name}
                      </span>
                      <span className="text-xs text-gray-400">
                        {message.timestamp.toLocaleTimeString()}
                      </span>
                    </div>
                    <div className="prose prose-sm max-w-none">
                      <p className="text-gray-800 whitespace-pre-wrap leading-relaxed">
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
        <div className="border-t border-gray-200 bg-white p-4">
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
                  className="w-full px-4 py-3 pr-12 border border-gray-300 rounded-2xl focus:outline-none focus:border-gray-400 resize-none max-h-40"
                  style={{ minHeight: '52px' }}
                />
              </div>
              <button
                onClick={handleSend}
                disabled={!input.trim() || isLoading}
                className={`p-3 rounded-xl transition-all ${
                  input.trim() && !isLoading
                    ? `${currentAssistant.color} hover:opacity-90 text-white`
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
            className="bg-white rounded-2xl shadow-2xl max-w-md w-full p-6"
          >
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold text-gray-900">Edit Profile</h2>
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
                <label className="block text-sm font-medium text-gray-700 mb-2">Full Name</label>
                <input
                  type="text"
                  value={userFormData.full_name}
                  onChange={(e) => setUserFormData({ ...userFormData, full_name: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="John Doe"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Email</label>
                <input
                  type="email"
                  value={userFormData.email}
                  onChange={(e) => setUserFormData({ ...userFormData, email: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="student@tedu.edu.tr"
                />
              </div>
              <div className="flex gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => setShowUserModal(false)}
                  className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
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
