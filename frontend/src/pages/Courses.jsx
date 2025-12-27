import { useState } from 'react'
import axios from 'axios'

export default function Courses() {
  const [query, setQuery] = useState('')
  const [topK, setTopK] = useState(5)
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [systemStatus, setSystemStatus] = useState(null)

  // Fetch system status on component mount
  const fetchStatus = async () => {
    try {
      const response = await axios.get('/api/v1/courses/status')
      setSystemStatus(response.data)
    } catch (err) {
      console.error('Failed to fetch status:', err)
    }
  }

  // Initial status fetch
  useState(() => {
    fetchStatus()
  }, [])

  const handleSearch = async (e) => {
    e.preventDefault()
    if (!query.trim()) return

    setLoading(true)
    setError(null)
    setResults([])

    try {
      const response = await axios.post('/api/v1/courses/search', {
        query: query.trim(),
        top_k: topK
      })
      // API returns array directly, not wrapped in {results: [...]}
      setResults(response.data || [])
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to search courses')
      console.error('Search error:', err)
    } finally {
      setLoading(false)
    }
  }

  const clearSearch = () => {
    setQuery('')
    setResults([])
    setError(null)
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Course Semantic Search
          </h1>
          <p className="mt-2 text-gray-600 dark:text-gray-400">
            Search TED University courses using natural language queries powered by AI embeddings
          </p>
        </div>

        {/* System Status */}
        {systemStatus && (
          <div className="mb-6 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
            <h3 className="text-sm font-semibold text-blue-900 dark:text-blue-200 mb-2">
              System Status
            </h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div>
                <span className="text-gray-600 dark:text-gray-400">Status:</span>
                <span className="ml-2 font-medium text-green-600 dark:text-green-400">
                  {systemStatus.status}
                </span>
              </div>
              <div>
                <span className="text-gray-600 dark:text-gray-400">ChromaDB:</span>
                <span className="ml-2 font-medium text-gray-900 dark:text-white">
                  {systemStatus.chroma_count} courses
                </span>
              </div>
              <div>
                <span className="text-gray-600 dark:text-gray-400">PostgreSQL:</span>
                <span className="ml-2 font-medium text-gray-900 dark:text-white">
                  {systemStatus.postgres_count} courses
                </span>
              </div>
              <div>
                <span className="text-gray-600 dark:text-gray-400">Model:</span>
                <span className="ml-2 font-medium text-gray-900 dark:text-white text-xs">
                  intfloat/e5-large-v2
                </span>
              </div>
            </div>
          </div>
        )}

        {/* Search Form */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6 mb-6">
          <form onSubmit={handleSearch}>
            <div className="space-y-4">
              {/* Query Input */}
              <div>
                <label htmlFor="query" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Search Query
                </label>
                <input
                  type="text"
                  id="query"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="e.g., machine learning algorithms, database design, circuits and electronics..."
                  className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-white"
                />
              </div>

              {/* Top K Slider */}
              <div>
                <label htmlFor="topK" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Number of Results: {topK}
                </label>
                <input
                  type="range"
                  id="topK"
                  min="1"
                  max="20"
                  value={topK}
                  onChange={(e) => setTopK(parseInt(e.target.value))}
                  className="w-full"
                />
              </div>

              {/* Buttons */}
              <div className="flex gap-3">
                <button
                  type="submit"
                  disabled={loading || !query.trim()}
                  className="flex-1 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-medium py-3 px-6 rounded-lg transition-colors duration-200"
                >
                  {loading ? (
                    <span className="flex items-center justify-center">
                      <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      Searching...
                    </span>
                  ) : (
                    'Search Courses'
                  )}
                </button>
                <button
                  type="button"
                  onClick={clearSearch}
                  className="px-6 py-3 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300 font-medium transition-colors duration-200"
                >
                  Clear
                </button>
              </div>
            </div>
          </form>
        </div>

        {/* Error Message */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
            <p className="text-red-800 dark:text-red-200">{error}</p>
          </div>
        )}

        {/* Search Results */}
        {results.length > 0 && (
          <div>
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
              Search Results ({results.length})
            </h2>
            <div className="space-y-4">
              {results.map((result, index) => (
                <div
                  key={index}
                  className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow duration-200"
                >
                  {/* Course Header */}
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <h3 className="text-lg font-bold text-gray-900 dark:text-white">
                          {result.course_code}
                        </h3>
                        <span className="px-2 py-1 bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 text-xs font-medium rounded">
                          {result.department}
                        </span>
                        {result.level && (
                          <span className="px-2 py-1 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 text-xs font-medium rounded">
                            {result.level}
                          </span>
                        )}
                      </div>
                      <p className="text-md font-medium text-gray-800 dark:text-gray-200">
                        {result.course_title}
                      </p>
                    </div>
                    <div className="flex flex-col items-end gap-1">
                      <span className="text-2xl font-bold text-green-600 dark:text-green-400">
                        {((result.similarity_score || 0) * 100).toFixed(1)}%
                      </span>
                      <span className="text-xs text-gray-500 dark:text-gray-400">
                        similarity
                      </span>
                    </div>
                  </div>

                  {/* Course Details */}
                  <div className="grid grid-cols-3 gap-4 mb-4 text-sm">
                    <div>
                      <span className="text-gray-600 dark:text-gray-400">Credits:</span>
                      <span className="ml-2 font-medium text-gray-900 dark:text-white">
                        {result.credits || 'N/A'}
                      </span>
                    </div>
                    <div>
                      <span className="text-gray-600 dark:text-gray-400">ECTS:</span>
                      <span className="ml-2 font-medium text-gray-900 dark:text-white">
                        {result.ects || 'N/A'}
                      </span>
                    </div>
                    <div>
                      <span className="text-gray-600 dark:text-gray-400">Instructor:</span>
                      <span className="ml-2 font-medium text-gray-900 dark:text-white">
                        {result.instructor || 'N/A'}
                      </span>
                    </div>
                  </div>

                  {/* Description */}
                  {result.catalog_description && (
                    <div className="mb-4">
                      <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
                        Description
                      </h4>
                      <p className="text-sm text-gray-600 dark:text-gray-400 leading-relaxed">
                        {result.catalog_description}
                      </p>
                    </div>
                  )}

                  {/* Prerequisites */}
                  {result.prerequisites && result.prerequisites.length > 0 && (
                    <div className="mb-3">
                      <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-1">
                        Prerequisites
                      </h4>
                      <div className="flex flex-wrap gap-2">
                        {result.prerequisites.map((prereq, i) => (
                          <span
                            key={i}
                            className="px-2 py-1 bg-orange-100 dark:bg-orange-900 text-orange-800 dark:text-orange-200 text-xs rounded"
                          >
                            {prereq}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Syllabus Links */}
                  {(result.syllabus_url || result.syllabus_pdf_url) && (
                    <div className="mt-4 flex flex-wrap gap-4">
                      {result.syllabus_url && (
                        <a
                          href={result.syllabus_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 text-sm font-medium"
                        >
                          <svg className="mr-2 w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" />
                          </svg>
                          Syllabus Site
                          <svg className="ml-1 w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                          </svg>
                        </a>
                      )}
                      {result.syllabus_pdf_url && (
                        <a
                          href={result.syllabus_pdf_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center text-red-600 dark:text-red-400 hover:text-red-800 dark:hover:text-red-300 text-sm font-medium"
                        >
                          <svg className="mr-2 w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                          </svg>
                          Syllabus File
                          <svg className="ml-1 w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                          </svg>
                        </a>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* No Results */}
        {!loading && results.length === 0 && query && !error && (
          <div className="text-center py-12">
            <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <h3 className="mt-2 text-sm font-medium text-gray-900 dark:text-white">No courses found</h3>
            <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
              Try a different search query
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
