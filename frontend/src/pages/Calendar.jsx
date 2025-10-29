import { useState } from 'react';
import { motion } from 'framer-motion';
import { 
  Calendar as CalendarIcon, 
  Mail,
  ScanLine,
  Check,
  X as XIcon,
  Clock,
  BookOpen,
  FileText,
  Users,
  AlertCircle,
  ChevronLeft,
  ChevronRight,
  Plus
} from 'lucide-react';

const mockEvents = [
  {
    id: 1,
    title: 'CMPE 491 - Midterm Exam',
    date: '2025-11-05',
    time: '14:00',
    type: 'exam',
    course: 'Computer Engineering Project',
    location: 'Room B101',
    status: 'confirmed'
  },
  {
    id: 2,
    title: 'Project Report Deadline',
    date: '2025-11-08',
    time: '23:59',
    type: 'deadline',
    course: 'CMPE 491',
    status: 'confirmed'
  },
  {
    id: 3,
    title: 'CMPE 492 - Final Presentation',
    date: '2025-11-12',
    time: '10:00',
    type: 'presentation',
    course: 'Senior Project',
    location: 'Auditorium',
    status: 'confirmed'
  },
  {
    id: 4,
    title: 'Database Quiz',
    date: '2025-11-10',
    time: '15:30',
    type: 'quiz',
    course: 'CMPE 321',
    location: 'Room A205',
    status: 'pending'
  }
];

export default function Calendar() {
  const [events, setEvents] = useState(mockEvents);
  const [scanning, setScanning] = useState(false);
  const [selectedDate, setSelectedDate] = useState(new Date());
  const [view, setView] = useState('list'); // 'list' or 'calendar'

  const handleScanEmail = () => {
    setScanning(true);
    // Simulate email scanning
    setTimeout(() => {
      setScanning(false);
      // TODO: Add API call to scan emails
      alert('Email scanning complete! Found 2 new events.');
    }, 2000);
  };

  const getEventColor = (type) => {
    const colors = {
      exam: 'bg-red-100 text-red-700 border-red-200',
      quiz: 'bg-orange-100 text-orange-700 border-orange-200',
      deadline: 'bg-blue-100 text-blue-700 border-blue-200',
      presentation: 'bg-purple-100 text-purple-700 border-purple-200',
      meeting: 'bg-green-100 text-green-700 border-green-200'
    };
    return colors[type] || 'bg-gray-100 text-gray-700 border-gray-200';
  };

  const getEventIcon = (type) => {
    const icons = {
      exam: FileText,
      quiz: BookOpen,
      deadline: Clock,
      presentation: Users,
      meeting: CalendarIcon
    };
    return icons[type] || AlertCircle;
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  };

  const upcomingEvents = events
    .filter(e => new Date(e.date) >= new Date())
    .sort((a, b) => new Date(a.date) - new Date(b.date));

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
            <CalendarIcon className="w-8 h-8 text-blue-600" />
            Academic Calendar
          </h1>
          <p className="text-gray-600 mt-1">Manage your schedule and important deadlines</p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={handleScanEmail}
            disabled={scanning}
            className="flex items-center gap-2 bg-gradient-to-r from-purple-600 to-blue-600 text-white px-6 py-3 rounded-xl font-medium shadow-lg hover:shadow-xl transition-all disabled:opacity-50"
          >
            <ScanLine className={`w-5 h-5 ${scanning ? 'animate-spin' : ''}`} />
            {scanning ? 'Scanning...' : 'Scan Email'}
          </button>
          <button className="flex items-center gap-2 bg-white border border-gray-200 text-gray-700 px-6 py-3 rounded-xl font-medium hover:bg-gray-50 transition-all">
            <Plus className="w-5 h-5" />
            Add Event
          </button>
        </div>
      </div>

      {/* Email Scanning Info */}
      <div className="bg-gradient-to-r from-purple-50 to-blue-50 border border-purple-200 rounded-2xl p-6">
        <div className="flex items-start gap-4">
          <div className="w-12 h-12 bg-white rounded-xl flex items-center justify-center shadow-sm">
            <Mail className="w-6 h-6 text-purple-600" />
          </div>
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Email Scanner</h3>
            <p className="text-gray-700 mb-4">
              SAGE automatically scans your TED University email for exam dates, assignment deadlines, 
              and important academic events. Click "Scan Email" to detect new events and sync them to your calendar.
            </p>
            <div className="flex gap-4 text-sm">
              <div className="flex items-center gap-2">
                <Check className="w-4 h-4 text-green-600" />
                <span className="text-gray-700">Auto-detect exam dates</span>
              </div>
              <div className="flex items-center gap-2">
                <Check className="w-4 h-4 text-green-600" />
                <span className="text-gray-700">Assignment deadlines</span>
              </div>
              <div className="flex items-center gap-2">
                <Check className="w-4 h-4 text-green-600" />
                <span className="text-gray-700">Google Calendar sync</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {[
          { label: 'Upcoming Events', value: upcomingEvents.length, color: 'blue', icon: CalendarIcon },
          { label: 'Exams', value: events.filter(e => e.type === 'exam').length, color: 'red', icon: FileText },
          { label: 'Deadlines', value: events.filter(e => e.type === 'deadline').length, color: 'orange', icon: Clock },
          { label: 'This Week', value: events.filter(e => {
            const eventDate = new Date(e.date);
            const weekFromNow = new Date();
            weekFromNow.setDate(weekFromNow.getDate() + 7);
            return eventDate <= weekFromNow;
          }).length, color: 'green', icon: AlertCircle }
        ].map((stat, index) => {
          const Icon = stat.icon;
          return (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
              className="bg-white rounded-2xl p-6 border border-gray-200 hover:shadow-lg transition-all"
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-gray-600">{stat.label}</span>
                <Icon className={`w-5 h-5 text-${stat.color}-600`} />
              </div>
              <p className={`text-3xl font-bold text-${stat.color}-600`}>{stat.value}</p>
            </motion.div>
          );
        })}
      </div>

      {/* Events List */}
      <div className="bg-white rounded-2xl shadow-lg border border-gray-200">
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-bold text-gray-900">Upcoming Events</h2>
            <div className="flex gap-2">
              <button
                onClick={() => setView('list')}
                className={`px-4 py-2 rounded-lg transition-colors ${
                  view === 'list' ? 'bg-blue-100 text-blue-700' : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                List View
              </button>
              <button
                onClick={() => setView('calendar')}
                className={`px-4 py-2 rounded-lg transition-colors ${
                  view === 'calendar' ? 'bg-blue-100 text-blue-700' : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                Calendar View
              </button>
            </div>
          </div>
        </div>

        <div className="divide-y divide-gray-100">
          {upcomingEvents.length === 0 ? (
            <div className="p-12 text-center text-gray-500">
              <CalendarIcon className="w-16 h-16 mx-auto mb-4 text-gray-300" />
              <p className="text-lg font-medium">No upcoming events</p>
              <p className="text-sm">Scan your email to find academic events automatically</p>
            </div>
          ) : (
            upcomingEvents.map((event) => {
              const EventIcon = getEventIcon(event.type);
              return (
                <motion.div
                  key={event.id}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="p-6 hover:bg-gray-50 transition-colors"
                >
                  <div className="flex items-start gap-4">
                    <div className={`w-12 h-12 rounded-xl ${getEventColor(event.type).replace('text-', 'bg-').replace('100', '200')} flex items-center justify-center`}>
                      <EventIcon className="w-6 h-6" />
                    </div>
                    <div className="flex-1">
                      <div className="flex items-start justify-between mb-2">
                        <div>
                          <h3 className="text-lg font-semibold text-gray-900">{event.title}</h3>
                          <p className="text-sm text-gray-600">{event.course}</p>
                        </div>
                        <span className={`px-3 py-1 rounded-full text-xs font-medium border ${getEventColor(event.type)}`}>
                          {event.type.toUpperCase()}
                        </span>
                      </div>
                      <div className="flex flex-wrap gap-4 text-sm text-gray-600">
                        <div className="flex items-center gap-2">
                          <CalendarIcon className="w-4 h-4" />
                          {formatDate(event.date)}
                        </div>
                        <div className="flex items-center gap-2">
                          <Clock className="w-4 h-4" />
                          {event.time}
                        </div>
                        {event.location && (
                          <div className="flex items-center gap-2">
                            <AlertCircle className="w-4 h-4" />
                            {event.location}
                          </div>
                        )}
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <button className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors" title="Edit">
                        <FileText className="w-4 h-4" />
                      </button>
                      <button className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors" title="Delete">
                        <XIcon className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                </motion.div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
}
