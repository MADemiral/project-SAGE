import { useState, useEffect } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { Menu, X, FileText, BarChart3, Home, Sparkles, LogOut, User, MessageSquare, Calendar, BookOpen, Users, Search, ChevronLeft, ChevronRight } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { useAuth } from '../context/AuthContext'

const Layout = ({ children }) => {
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [showCalendarPopup, setShowCalendarPopup] = useState(false)
  const [events, setEvents] = useState([])
  const [currentDate, setCurrentDate] = useState(new Date())
  const [selectedEvent, setSelectedEvent] = useState(null)
  const location = useLocation()
  const { user, logout } = useAuth()

  const navigation = [
    { name: 'AI Assistant', href: '/', icon: MessageSquare },
    { name: 'My Courses', href: '/documents', icon: BookOpen },
    { name: 'Course Search', href: '/courses', icon: Search },
    { name: 'Users', href: '/users', icon: Users, adminOnly: true },
  ]

  const filteredNavigation = navigation.filter(item => 
    !item.adminOnly || (item.adminOnly && user?.is_superuser)
  )

  const isActive = (path) => location.pathname === path

  // Load calendar events
  useEffect(() => {
    const loadEvents = async () => {
      if (user) {
        try {
          const response = await fetch(`http://localhost:8000/api/v1/calendar/imap/events/${user.id}`);
          if (response.ok) {
            const data = await response.json();
            setEvents(data.events || []);
          }
        } catch (err) {
          console.error('Failed to load events:', err);
        }
      }
    };
    loadEvents();
  }, [user]);

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

  return (
    <div className="min-h-screen bg-dark-950">
      {/* Animated Background */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-primary-600/10 rounded-full blur-3xl animate-pulse-slow"></div>
        <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-primary-500/10 rounded-full blur-3xl animate-pulse-slow" style={{ animationDelay: '1s' }}></div>
      </div>

      {/* Sidebar */}
      <AnimatePresence>
        {sidebarOpen && (
          <motion.aside
            initial={{ x: -300 }}
            animate={{ x: 0 }}
            exit={{ x: -300 }}
            transition={{ type: 'spring', damping: 20 }}
            className="fixed inset-y-0 left-0 z-50 w-72 glass-effect border-r border-white/10"
          >
            <div className="flex flex-col h-full">
              {/* Logo */}
              <div className="flex items-center justify-between p-6 border-b border-white/10">
                <div className="flex items-center gap-3">
                  <img 
                    src="/SAGE_logo.jpg" 
                    alt="SAGE Logo" 
                    className="w-10 h-10 object-contain rounded-lg bg-white/10 p-1"
                  />
                  <div>
                    <h1 className="text-xl font-display font-bold bg-gradient-to-r from-primary-400 to-primary-600 bg-clip-text text-transparent">
                      SAGE
                    </h1>
                    <p className="text-xs text-dark-400">Smart AI Guide for Education</p>
                  </div>
                </div>
                <button
                  onClick={() => setSidebarOpen(false)}
                  className="lg:hidden p-2 hover:bg-white/5 rounded-lg transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Navigation */}
              <nav className="flex-1 p-4 space-y-2">
                {filteredNavigation.map((item) => {
                  const Icon = item.icon
                  const active = isActive(item.href)
                  return (
                    <Link
                      key={item.name}
                      to={item.href}
                      className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200 ${
                        active
                          ? 'bg-gradient-to-r from-primary-600 to-primary-500 text-white shadow-lg glow-effect'
                          : 'text-dark-300 hover:bg-white/5 hover:text-white'
                      }`}
                    >
                      <Icon className="w-5 h-5" />
                      <span className="font-medium">{item.name}</span>
                    </Link>
                  )
                })}
              </nav>

              {/* Footer */}
              <div className="p-4 border-t border-white/10">
                {/* User Info */}
                {user && (
                  <div className="mb-4 p-4 glass-effect rounded-lg">
                    <div className="flex items-center gap-3 mb-3">
                      <div className="w-10 h-10 bg-gradient-to-br from-primary-500 to-primary-700 rounded-full flex items-center justify-center">
                        <User className="w-5 h-5 text-white" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-semibold text-white truncate">
                          {user.full_name || user.username}
                        </p>
                        <p className="text-xs text-dark-400 truncate">{user.email}</p>
                      </div>
                    </div>
                    <button
                      onClick={async () => {
                        await logout();
                      }}
                      className="w-full flex items-center justify-center gap-2 px-3 py-2 bg-red-500/10 hover:bg-red-500/20 text-red-400 rounded-lg transition-colors text-sm"
                    >
                      <LogOut className="w-4 h-4" />
                      Logout
                    </button>
                  </div>
                )}
                
                <div className="card p-4">
                  <p className="text-xs text-dark-400 mb-2">Version 1.0.0</p>
                  <p className="text-xs text-dark-500">© 2025 SAGE</p>
                </div>
              </div>
            </div>
          </motion.aside>
        )}
      </AnimatePresence>

      {/* Main Content */}
      <div className={`transition-all duration-300 ${sidebarOpen ? 'lg:pl-72' : ''}`}>
        {/* Header */}
        <header className="sticky top-0 z-40 glass-effect border-b border-white/10">
          <div className="flex items-center justify-between px-6 py-4">
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="p-2 hover:bg-white/5 rounded-lg transition-colors"
            >
              <Menu className="w-6 h-6" />
            </button>

            <div className="flex items-center gap-4">
              {/* Calendar Quick View Button */}
              <button
                onClick={() => setShowCalendarPopup(true)}
                className="relative p-2 hover:bg-white/5 rounded-lg transition-colors group"
                title="Quick Calendar View"
              >
                <Calendar className="w-6 h-6 text-primary-400 group-hover:text-primary-300" />
                {events.length > 0 && (
                  <span className="absolute -top-1 -right-1 bg-primary-600 text-white text-xs w-5 h-5 rounded-full flex items-center justify-center font-semibold">
                    {events.length > 9 ? '9+' : events.length}
                  </span>
                )}
              </button>

              {user && (
                <div className="hidden md:flex items-center gap-3 px-4 py-2 glass-effect rounded-lg">
                  <div className="w-8 h-8 bg-gradient-to-br from-primary-500 to-primary-700 rounded-full flex items-center justify-center">
                    <User className="w-4 h-4 text-white" />
                  </div>
                  <div className="text-left">
                    <p className="text-sm font-semibold text-white">
                      {user.full_name || user.username}
                    </p>
                    {user.is_superuser && (
                      <p className="text-xs text-primary-400">Administrator</p>
                    )}
                  </div>
                </div>
              )}
              
              <div className="px-4 py-2 glass-effect rounded-lg">
                <span className="text-sm text-dark-300">Status: </span>
                <span className="text-sm text-green-400 font-semibold">Active</span>
              </div>
            </div>
          </div>
        </header>

        {/* Page Content */}
        <main className="relative z-10">
          {children}
        </main>
      </div>

      {/* Calendar Quick View Popup */}
      {showCalendarPopup && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-[60] p-4" onClick={() => setShowCalendarPopup(false)}>
          <div className="bg-dark-800 border-2 border-primary-500/50 rounded-xl max-w-6xl w-full max-h-[90vh] overflow-y-auto shadow-2xl" onClick={(e) => e.stopPropagation()}>
            {/* Header */}
            <div className="sticky top-0 bg-gradient-to-r from-primary-600 to-purple-600 p-6 rounded-t-xl z-10">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <Calendar className="w-8 h-8 text-white" />
                  <div>
                    <h2 className="text-2xl font-bold text-white">Quick Calendar View</h2>
                    <p className="text-white/80 text-sm">{events.length} event{events.length !== 1 ? 's' : ''} total</p>
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
                  <h3 className="text-xl font-bold text-white">{formatMonthYear(currentDate)}</h3>
                  <button
                    onClick={goToToday}
                    className="px-3 py-1 bg-white/20 hover:bg-white/30 rounded-lg text-sm font-medium transition-colors text-white"
                  >
                    Today
                  </button>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => navigateMonth(-1)}
                    className="p-2 hover:bg-white/20 rounded-lg transition-colors text-white"
                  >
                    <ChevronLeft className="w-5 h-5" />
                  </button>
                  <button
                    onClick={() => navigateMonth(1)}
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
                    
                    // Previous month's trailing days
                    for (let i = 0; i < startingDayOfWeek; i++) {
                      const prevMonthDate = new Date(currentDate.getFullYear(), currentDate.getMonth(), -startingDayOfWeek + i + 1);
                      days.push(
                        <div key={`prev-${i}`} className="min-h-[100px] p-2 bg-dark-900/30 border-r border-b border-dark-700/50">
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
                          className={`min-h-[100px] p-2 border-r border-b border-dark-700 ${
                            today ? 'bg-primary-500/10' : 'bg-dark-900/50'
                          }`}
                        >
                          <div className={`text-sm font-medium mb-2 ${
                            today ? 'bg-primary-600 text-white w-6 h-6 rounded-full flex items-center justify-center' : 'text-dark-300'
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
                                className={`text-xs p-1.5 rounded cursor-pointer transition-all hover:scale-105 ${
                                  event.event_type === 'academic' ? 'bg-blue-600/80 hover:bg-blue-600 text-white' :
                                  event.event_type === 'social' ? 'bg-purple-600/80 hover:bg-purple-600 text-white' :
                                  event.event_type === 'student_activity' ? 'bg-green-600/80 hover:bg-green-600 text-white' :
                                  event.event_type === 'career' ? 'bg-orange-600/80 hover:bg-orange-600 text-white' :
                                  'bg-gray-600/80 hover:bg-gray-600 text-white'
                                }`}
                              >
                                <div className="font-medium truncate">{event.title}</div>
                                {event.requirements && (
                                  <div className="text-[10px] opacity-90 truncate">📚 {event.requirements}</div>
                                )}
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
                        <div key={`next-${i}`} className="min-h-[100px] p-2 bg-dark-900/30 border-r border-b border-dark-700/50">
                          <div className="text-xs text-dark-600 mb-1">{i}</div>
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
      )}

      {/* Event Detail Modal */}
      {selectedEvent && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-[70] p-4" onClick={() => setSelectedEvent(null)}>
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
  )
}

export default Layout
