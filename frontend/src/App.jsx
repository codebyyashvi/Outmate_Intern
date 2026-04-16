import { useState } from "react";
import axios from "axios";
import "./App.css";

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || "http://localhost:8000";

const SAMPLE_PROMPTS = [
  "Find 3 fast-growing SaaS companies in the US with 50–500 employees, raising Series B or later.",
  "Give me 3 VPs of Sales in European fintech startups with more than 100 employees.",
  "Top AI infrastructure companies hiring machine learning engineers in India.",
  "3 marketing leaders at e-commerce brands in North America doing more than $50M in revenue.",
];

function JSONModal({ isOpen, data, onClose }) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-60 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl max-w-2xl w-full max-h-[80vh] overflow-hidden flex flex-col">
        <div className="flex justify-between items-center p-6 border-b border-gray-200 bg-gradient-to-r from-blue-50 to-purple-50">
          <h3 className="text-lg font-bold text-gray-800">Raw JSON Data</h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-3xl font-light transition"
          >
            ✕
          </button>
        </div>
        <pre className="flex-1 overflow-auto p-6 bg-gray-900 text-gray-100 text-xs font-mono rounded">
          {JSON.stringify(data, null, 2)}
        </pre>
      </div>
    </div>
  );
}

function ResultCard({ row, onViewJSON }) {
  const isCompany = row.type === "company";

  return (
    <div className="group bg-white rounded-xl shadow-md hover:shadow-xl transition-all duration-300 p-6 border border-gray-100">
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <a
            href={row.linkedin_url || (row.domain ? `https://${row.domain}` : "#")}
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-600 hover:text-blue-700 font-bold text-lg block mb-1 truncate"
          >
            {row.name}
          </a>
          <span className={`inline-block px-3 py-1 rounded-full text-xs font-semibold ${
            isCompany 
              ? "bg-blue-100 text-blue-700" 
              : "bg-purple-100 text-purple-700"
          }`}>
            {isCompany ? "Company" : "Prospect"}
          </span>
        </div>
      </div>

      {/* Grid Info */}
      <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-4">
        {row.industry && (
          <div>
            <p className="text-xs text-gray-500 uppercase tracking-wider">Industry</p>
            <p className="text-sm font-semibold text-gray-800">{row.industry}</p>
          </div>
        )}
        {row.country && (
          <div>
            <p className="text-xs text-gray-500 uppercase tracking-wider">Location</p>
            <p className="text-sm font-semibold text-gray-800">{row.country}</p>
          </div>
        )}
        {row.employee_count && (
          <div>
            <p className="text-xs text-gray-500 uppercase tracking-wider">Employees</p>
            <p className="text-sm font-semibold text-gray-800">{row.employee_count.toLocaleString()}</p>
          </div>
        )}
        {row.revenue && (
          <div>
            <p className="text-xs text-gray-500 uppercase tracking-wider">Revenue</p>
            <p className="text-sm font-semibold text-gray-800">{row.revenue}</p>
          </div>
        )}
        {row.founded_year && (
          <div>
            <p className="text-xs text-gray-500 uppercase tracking-wider">Founded</p>
            <p className="text-sm font-semibold text-gray-800">{row.founded_year}</p>
          </div>
        )}
        {row.job_title && (
          <div>
            <p className="text-xs text-gray-500 uppercase tracking-wider">Title</p>
            <p className="text-sm font-semibold text-gray-800">{row.job_title}</p>
          </div>
        )}
      </div>

      {/* Tech Stack */}
      {row.tech_stack && row.tech_stack.length > 0 && (
        <div className="mb-4 pb-4 border-t border-gray-200">
          <p className="text-xs text-gray-500 uppercase tracking-wider mb-2">Tech Stack</p>
          <div className="flex flex-wrap gap-2">
            {row.tech_stack.slice(0, 5).map((tech, i) => (
              <span key={i} className="bg-gray-100 text-gray-700 px-3 py-1 rounded-full text-xs font-medium">
                {tech}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Links */}
      <div className="flex gap-2 pt-4 border-t border-gray-200">
        {row.domain && (
          <a
            href={`https://${row.domain}`}
            target="_blank"
            rel="noopener noreferrer"
            className="flex-1 text-center text-xs font-semibold text-blue-600 hover:text-blue-700 hover:bg-blue-50 py-2 rounded-lg transition"
          >
            🌐 Website
          </a>
        )}
        {row.linkedin_url && (
          <a
            href={row.linkedin_url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex-1 text-center text-xs font-semibold text-blue-600 hover:text-blue-700 hover:bg-blue-50 py-2 rounded-lg transition"
          >
            💼 LinkedIn
          </a>
        )}
        <button
          onClick={() => onViewJSON(row)}
          className="flex-1 text-center text-xs font-semibold text-gray-600 hover:text-gray-800 hover:bg-gray-100 py-2 rounded-lg transition"
        >
          { } JSON
        </button>
      </div>
    </div>
  );
}

function LoadingSpinner() {
  return (
    <div className="flex flex-col items-center justify-center py-12">
      <div className="relative w-12 h-12 mb-4">
        <div className="absolute inset-0 rounded-full border-4 border-gray-200"></div>
        <div className="absolute inset-0 rounded-full border-4 border-transparent border-t-blue-600 border-r-blue-600 animate-spin"></div>
      </div>
      <p className="text-gray-600 font-medium">Processing your request...</p>
    </div>
  );
}

function App() {
  const [prompt, setPrompt] = useState("");
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [selectedJSON, setSelectedJSON] = useState(null);
  const [showJSONModal, setShowJSONModal] = useState(false);

  const handleSearch = async () => {
    if (!prompt.trim()) {
      setError("Please enter a prompt");
      return;
    }

    setError("");
    setLoading(true);

    try {
      const res = await axios.post(`${BACKEND_URL}/api/enrich`, {
        prompt,
      });

      setResults(res.data.results || []);

      if (res.data.results.length === 0) {
        setError("No results found. Try a different prompt.");
      }
    } catch (err) {
      const errorMessage =
        err.response?.data?.detail || err.message || "Error fetching data";
      setError(`Failed to enrich data: ${errorMessage}`);
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  const handleSamplePrompt = (sample) => {
    setPrompt(sample);
  };

  const handleClear = () => {
    setPrompt("");
    setResults([]);
    setError("");
  };

  const handleViewJSON = (row) => {
    setSelectedJSON(row.raw || row);
    setShowJSONModal(true);
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && e.ctrlKey) {
      handleSearch();
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900">
      {/* Animated background elements */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-blue-500 rounded-full mix-blend-multiply filter blur-3xl opacity-10 animate-blob"></div>
        <div className="absolute top-0 right-1/4 w-96 h-96 bg-purple-500 rounded-full mix-blend-multiply filter blur-3xl opacity-10 animate-blob animation-delay-2000"></div>
        <div className="absolute -bottom-8 left-1/2 w-96 h-96 bg-blue-600 rounded-full mix-blend-multiply filter blur-3xl opacity-10 animate-blob animation-delay-4000"></div>
      </div>

      <div className="relative z-10">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12">
          {/* Header */}
          <header className="mb-12">
            <div className="text-center mb-8">
              <h1 className="text-5xl sm:text-6xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-300 via-blue-200 to-purple-300 mb-4">
                OutMate
              </h1>
              <p className="text-xl text-blue-100 mb-2">NLP Database Enrichment</p>
              <p className="text-blue-300 max-w-2xl mx-auto">
                Convert natural language into structured B2B insights. Just describe what you're looking for.
              </p>
            </div>
          </header>

          {/* Main Card */}
          <div className="bg-white bg-opacity-95 backdrop-blur-sm rounded-2xl shadow-2xl p-8 mb-8">
            {/* Error Banner */}
            {error && (
              <div className="mb-6 p-4 bg-gradient-to-r from-red-50 to-pink-50 border-l-4 border-red-500 rounded-lg flex items-start gap-3 animate-pulse">
                <span className="text-2xl">⚠️</span>
                <div className="flex-1">
                  <p className="text-red-800 font-medium">Error</p>
                  <p className="text-red-700 text-sm">{error}</p>
                </div>
                <button
                  onClick={() => setError("")}
                  className="text-red-400 hover:text-red-600 text-2xl font-light"
                >
                  ✕
                </button>
              </div>
            )}

            {/* Input Section */}
            <div className="mb-8">
              <label className="block text-sm font-semibold text-gray-800 mb-3">
                What are you looking for?
              </label>
              <textarea
                className="w-full border-2 border-gray-200 rounded-xl p-4 focus:outline-none focus:border-blue-500 focus:ring-4 focus:ring-blue-100 resize-none text-gray-800 placeholder-gray-400 font-medium"
                rows="4"
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Example: Find SaaS companies in the US with 50-500 employees raising Series B..."
              />
              <div className="flex gap-2 mt-4">
                <button
                  onClick={handleSearch}
                  disabled={loading}
                  className={`flex-1 px-6 py-3 rounded-xl font-semibold transition-all duration-300 transform hover:scale-105 ${
                    loading
                      ? "bg-gray-400 cursor-not-allowed text-gray-600"
                      : "bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white shadow-lg"
                  }`}
                >
                  {loading ? "⏳ Processing..." : "🔍 Search & Enrich"}
                </button>
                <button
                  onClick={handleClear}
                  className="px-6 py-3 rounded-xl font-semibold bg-gray-100 hover:bg-gray-200 text-gray-800 transition-all duration-300"
                >
                  Clear
                </button>
              </div>
              <p className="text-xs text-gray-500 mt-3 flex items-center gap-2">
                <span>ℹ️</span>
                <span><strong>Max 3 results</strong> per query • <strong>Ctrl+Enter</strong> to search</span>
              </p>
            </div>

            {/* Sample Prompts */}
            <div className="border-t border-gray-200 pt-8">
              <h3 className="text-sm font-bold text-gray-800 mb-4 uppercase tracking-wider">Explore Examples</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {SAMPLE_PROMPTS.map((sample, i) => (
                  <button
                    key={i}
                    onClick={() => handleSamplePrompt(sample)}
                    className="text-left text-sm p-4 bg-gradient-to-r from-blue-50 to-purple-50 hover:from-blue-100 hover:to-purple-100 border border-blue-100 hover:border-blue-300 rounded-lg transition-all duration-300 transform hover:scale-[1.02]"
                    title={sample}
                  >
                    <p className="text-gray-700 font-medium line-clamp-2">{sample}</p>
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Loading State */}
          {loading && (
            <div className="bg-white bg-opacity-95 backdrop-blur-sm rounded-2xl shadow-2xl p-12">
              <LoadingSpinner />
            </div>
          )}

          {/* Results Section */}
          {!loading && results.length > 0 && (
            <div className="animate-fade-in">
              <div className="mb-6">
                <h2 className="text-3xl font-bold text-white mb-2">
                  ✨ Results
                </h2>
                <p className="text-blue-200">
                  Found <span className="font-bold text-blue-100">{results.length}</span> enriched record{results.length !== 1 ? 's' : ''}
                </p>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {results.map((row, i) => (
                  <ResultCard
                    key={i}
                    row={row}
                    onViewJSON={handleViewJSON}
                  />
                ))}
              </div>
            </div>
          )}

          {/* Empty State */}
          {!loading && results.length === 0 && !error && (
            <div className="text-center py-16 bg-white bg-opacity-10 backdrop-blur-sm rounded-2xl border border-white border-opacity-20">
              <div className="text-5xl mb-4">📊</div>
              <p className="text-xl text-blue-100 font-medium">
                Enter a prompt to discover B2B insights
              </p>
              <p className="text-blue-300 mt-2">
                Powered by Gemini AI & Explorium Data
              </p>
            </div>
          )}
        </div>
      </div>

      {/* JSON Modal */}
      <JSONModal
        isOpen={showJSONModal}
        data={selectedJSON}
        onClose={() => setShowJSONModal(false)}
      />
    </div>
  );
}

export default App;