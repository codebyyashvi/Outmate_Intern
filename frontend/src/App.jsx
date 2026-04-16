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
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-lg max-w-2xl w-full max-h-96 overflow-auto p-6">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-bold">Raw JSON Data</h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-2xl"
          >
            ×
          </button>
        </div>
        <pre className="bg-gray-100 p-4 rounded overflow-auto text-sm">
          {JSON.stringify(data, null, 2)}
        </pre>
      </div>
    </div>
  );
}

function ResultsTable({ results, onViewJSON }) {
  return (
    <div className="overflow-x-auto mt-6">
      <table className="w-full border-collapse border border-gray-300">
        <thead className="bg-gray-100">
          <tr>
            <th className="border p-2 text-left">Name</th>
            <th className="border p-2 text-left">Type</th>
            <th className="border p-2 text-left">Industry / Title</th>
            <th className="border p-2 text-left">Location</th>
            <th className="border p-2 text-left">Revenue / Company</th>
            <th className="border p-2 text-left">Employees</th>
            <th className="border p-2 text-left">Founded</th>
            <th className="border p-2 text-center">Actions</th>
          </tr>
        </thead>
        <tbody>
          {results.map((row, i) => (
            <tr key={i} className="hover:bg-gray-50">
              <td className="border p-2">
                <a
                  href={row.linkedin_url || row.domain || "#"}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-600 hover:underline font-semibold"
                >
                  {row.name}
                </a>
              </td>
              <td className="border p-2 text-xs">
                <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded">
                  {row.type}
                </span>
              </td>
              <td className="border p-2 text-sm">
                {row.industry || row.job_title || "—"}
              </td>
              <td className="border p-2 text-sm">{row.country || "—"}</td>
              <td className="border p-2 text-sm">{row.revenue || row.company_name || "—"}</td>
              <td className="border p-2 text-sm">{row.employee_count || "—"}</td>
              <td className="border p-2 text-sm">{row.founded_year || "—"}</td>
              <td className="border p-2 text-center">
                <button
                  onClick={() => onViewJSON(row)}
                  className="bg-blue-500 text-white px-3 py-1 rounded text-sm hover:bg-blue-600"
                >
                  JSON
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
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

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 py-8 px-4">
      <div className="max-w-5xl mx-auto">
        {/* Header */}
        <header className="mb-8">
          <h1 className="text-4xl font-bold text-slate-900 mb-2">
              OutMate – NLP Enrichment Demo
          </h1>
          <p className="text-gray-600">
            Convert natural language into structured B2B data enrichment
          </p>
        </header>

        {/* Main Card */}
        <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
          {/* Error Banner */}
          {error && (
            <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
              <p className="text-red-700">{error}</p>
              <button
                onClick={() => setError("")}
                className="ml-auto text-red-500 hover:text-red-700"
              >
                ×
              </button>
            </div>
          )}

          {/* Input Section */}
          <div className="mb-6">
            <label className="block text-sm font-semibold text-slate-700 mb-2">
              Enter Your Search Prompt
            </label>
            <textarea
              className="w-full border border-gray-300 rounded-lg p-3 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
              rows="4"
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="Example: Find SaaS companies in the US with 50-500 employees..."
            />
            <div className="flex gap-2 mt-3">
              <button
                onClick={handleSearch}
                disabled={loading}
                className={`flex-1 px-6 py-2 rounded-lg font-semibold transition ${
                  loading
                    ? "bg-gray-400 cursor-not-allowed text-gray-600"
                    : "bg-blue-600 hover:bg-blue-700 text-white"
                }`}
              >
                {loading ? "🔄 Processing..." : "🔍 Search & Enrich"}
              </button>
              <button
                onClick={handleClear}
                className="px-6 py-2 rounded-lg font-semibold bg-gray-200 hover:bg-gray-300 text-gray-800"
              >
                Clear
              </button>
            </div>
            <p className="text-xs text-gray-500 mt-2">
              ⓘ <strong>Max 3 results</strong> per query to optimize API usage
            </p>
          </div>

          {/* Sample Prompts */}
          <div className="mb-6 border-t pt-6">
            <h3 className="text-sm font-semibold text-slate-700 mb-3">
              Try Sample Prompts
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
              {SAMPLE_PROMPTS.map((sample, i) => (
                <button
                  key={i}
                  onClick={() => handleSamplePrompt(sample)}
                  className="text-left text-sm p-3 bg-slate-50 hover:bg-blue-50 border border-gray-200 hover:border-blue-300 rounded-lg transition truncate"
                  title={sample}
                >
                  {sample.substring(0, 50)}...
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Results Section */}
        {results.length > 0 && (
          <div className="bg-white rounded-lg shadow-lg p-6">
            <h2 className="text-xl font-bold text-slate-900 mb-4">
              ✓ Results ({results.length} records)
            </h2>
            <ResultsTable results={results} onViewJSON={handleViewJSON} />
          </div>
        )}

        {/* Empty State */}
        {!loading && results.length === 0 && !error && (
          <div className="text-center py-12 bg-white rounded-lg shadow-lg">
            <p className="text-gray-500 text-lg">
              Enter a prompt and click "Search & Enrich" to get started
            </p>
          </div>
        )}
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