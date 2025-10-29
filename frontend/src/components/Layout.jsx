import { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { Menu, X, FileText, BarChart3, Home, Sparkles, LogOut, User, MessageSquare, Calendar, BookOpen, Users } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { useAuth } from '../context/AuthContext'

const Layout = ({ children }) => {
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const location = useLocation()
  const { user, logout } = useAuth()

  const navigation = [
    { name: 'AI Assistant', href: '/', icon: MessageSquare },
    { name: 'My Courses', href: '/documents', icon: BookOpen },
    { name: 'Users', href: '/users', icon: Users, adminOnly: true },
  ]

  const filteredNavigation = navigation.filter(item => 
    !item.adminOnly || (item.adminOnly && user?.is_superuser)
  )

  const isActive = (path) => location.pathname === path

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
                      onClick={logout}
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
    </div>
  )
}

export default Layout
