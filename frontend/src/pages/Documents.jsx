import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { FileText, Upload, Trash2, Search } from 'lucide-react'
import api from '../services/api'

const Documents = () => {
  const [documents, setDocuments] = useState([])
  const [searchTerm, setSearchTerm] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchDocuments()
  }, [])

  const fetchDocuments = async () => {
    try {
      setLoading(true)
      const response = await api.get('/documents/')
      setDocuments(response.data)
    } catch (error) {
      console.error('Error fetching documents:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (id) => {
    if (window.confirm('Are you sure you want to delete this document?')) {
      try {
        await api.delete(`/documents/${id}`)
        setDocuments(documents.filter(doc => doc.id !== id))
      } catch (error) {
        console.error('Error deleting document:', error)
      }
    }
  }

  const filteredDocuments = documents.filter(doc =>
    doc.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
    doc.filename.toLowerCase().includes(searchTerm.toLowerCase())
  )

  return (
    <div className="p-8 space-y-8">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center justify-between"
      >
        <div>
          <h1 className="text-4xl font-display font-bold text-white mb-2">Documents</h1>
          <p className="text-dark-400">Manage and organize your document library</p>
        </div>
        <button className="btn-primary flex items-center gap-2">
          <Upload className="w-5 h-5" />
          Upload Document
        </button>
      </motion.div>

      {/* Search */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="card"
      >
        <div className="relative">
          <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 w-5 h-5 text-dark-400" />
          <input
            type="text"
            placeholder="Search documents..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-12 pr-4 py-3 bg-dark-900/50 border border-white/10 rounded-lg text-white placeholder-dark-500 focus:outline-none focus:ring-2 focus:ring-primary-500 transition-all"
          />
        </div>
      </motion.div>

      {/* Documents Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {loading ? (
          Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="card animate-pulse">
              <div className="h-32 bg-dark-800 rounded-lg mb-4"></div>
              <div className="h-4 bg-dark-800 rounded w-3/4 mb-2"></div>
              <div className="h-3 bg-dark-800 rounded w-1/2"></div>
            </div>
          ))
        ) : filteredDocuments.length > 0 ? (
          filteredDocuments.map((doc, index) => (
            <motion.div
              key={doc.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.05 }}
              className="card group hover:scale-105"
            >
              <div className="flex items-start justify-between mb-4">
                <div className="p-3 bg-primary-500/20 rounded-xl">
                  <FileText className="w-8 h-8 text-primary-400" />
                </div>
                <button
                  onClick={() => handleDelete(doc.id)}
                  className="p-2 opacity-0 group-hover:opacity-100 hover:bg-red-500/20 rounded-lg transition-all"
                >
                  <Trash2 className="w-4 h-4 text-red-400" />
                </button>
              </div>
              
              <h3 className="text-lg font-semibold text-white mb-2 line-clamp-2">
                {doc.title}
              </h3>
              <p className="text-sm text-dark-400 mb-4">{doc.filename}</p>
              
              <div className="flex items-center justify-between">
                <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
                  doc.is_processed 
                    ? 'bg-green-500/20 text-green-400' 
                    : 'bg-yellow-500/20 text-yellow-400'
                }`}>
                  {doc.is_processed ? 'Processed' : 'Pending'}
                </span>
                {doc.document_type && (
                  <span className="text-xs text-dark-500 capitalize">
                    {doc.document_type}
                  </span>
                )}
              </div>
            </motion.div>
          ))
        ) : (
          <div className="col-span-full">
            <div className="card text-center py-12">
              <FileText className="w-16 h-16 text-dark-700 mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-white mb-2">No documents found</h3>
              <p className="text-dark-400 mb-6">
                {searchTerm ? 'Try a different search term' : 'Upload your first document to get started'}
              </p>
              <button className="btn-primary inline-flex items-center gap-2">
                <Upload className="w-5 h-5" />
                Upload Document
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default Documents
