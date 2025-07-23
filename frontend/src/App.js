import React, { useState, useEffect, useRef } from "react";
import "./App.css";

function App() {
  const [question, setQuestion] = useState("");
  const [response, setResponse] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [queryHistory, setQueryHistory] = useState([]);
  const [showHistory, setShowHistory] = useState(false);
  const [suggestions] = useState([
    "What are my sales in the last 7 days?",
    "Calculate the RoAS (Return on Ad Spend)",
    "Which product had the highest CPC?",
    "Show me the top 5 products by revenue",
    "What's the average order value?",
    "Compare sales performance by month"
  ]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const inputRef = useRef(null);

  // Load query history from localStorage on component mount
  useEffect(() => {
    const savedHistory = localStorage.getItem('queryHistory');
    if (savedHistory) {
      setQueryHistory(JSON.parse(savedHistory));
    }
  }, []);

  // Save query history to localStorage whenever it changes
  useEffect(() => {
    localStorage.setItem('queryHistory', JSON.stringify(queryHistory));
  }, [queryHistory]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!question.trim()) return;

    setLoading(true);
    setError("");
    setResponse(null);
    setShowSuggestions(false);

    const startTime = Date.now();

    try {
      const res = await fetch("http://localhost:8000/query", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          query: question,
          include_visualization: true,
        }),
      });

      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        throw new Error(errorData.error || `Server error: ${res.status}`);
      }

      const data = await res.json();
      const endTime = Date.now();

      // Add to query history
      const historyItem = {
        id: Date.now(),
        query: question,
        timestamp: new Date().toISOString(),
        executionTime: endTime - startTime,
        recordCount: data.record_count || 0,
        success: true
      };

      setQueryHistory(prev => [historyItem, ...prev.slice(0, 19)]); // Keep last 20 queries
      setResponse(data);

    } catch (err) {
      const errorMessage = err.message || "An unexpected error occurred";
      setError(errorMessage);

      // Add failed query to history
      const historyItem = {
        id: Date.now(),
        query: question,
        timestamp: new Date().toISOString(),
        error: errorMessage,
        success: false
      };

      setQueryHistory(prev => [historyItem, ...prev.slice(0, 19)]);

    } finally {
      setLoading(false);
    }
  };

  const handleSuggestionClick = (suggestion) => {
    setQuestion(suggestion);
    setShowSuggestions(false);
    inputRef.current?.focus();
  };

  const handleHistoryClick = (historyItem) => {
    if (historyItem.success) {
      setQuestion(historyItem.query);
      setShowHistory(false);
      inputRef.current?.focus();
    }
  };

  const clearHistory = () => {
    setQueryHistory([]);
    setShowHistory(false);
  };

  const formatTimestamp = (timestamp) => {
    return new Date(timestamp).toLocaleString();
  };

  const exportData = async (format) => {
    if (!question.trim()) {
      alert("Please enter a query first");
      return;
    }

    try {
      setLoading(true);
      const res = await fetch(`http://localhost:8000/export/${format}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          query: question,
          include_visualization: false,
        }),
      });

      if (!res.ok) {
        throw new Error(`Export failed: ${res.status}`);
      }

      // Create download link
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.style.display = 'none';
      a.href = url;

      // Get filename from response headers or generate one
      const contentDisposition = res.headers.get('content-disposition');
      let filename = `ecommerce_data.${format}`;
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename="(.+)"/);
        if (filenameMatch) {
          filename = filenameMatch[1];
        }
      }

      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

    } catch (err) {
      alert(`Export failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-bg">
      <div className="app-container">
        <div className="app-header">
          <div className="app-title">GenAI E-commerce Agent</div>
          <div className="app-subtitle">Ask questions about your e-commerce data in natural language</div>
        </div>

        <div className="query-section">
          <form onSubmit={handleSubmit} className="question-form">
            <div className="input-container">
              <input
                ref={inputRef}
                type="text"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                onFocus={() => setShowSuggestions(true)}
                placeholder="Ask a question about your e-commerce data..."
                className="question-input"
                required
              />
              <div className="input-actions">
                <button
                  type="button"
                  className="history-button"
                  onClick={() => setShowHistory(!showHistory)}
                  title="Query History"
                >
                  📋
                </button>
                <button
                  type="submit"
                  className="ask-button"
                  disabled={loading || !question.trim()}
                >
                  {loading ? (
                    <span className="loading-spinner">⏳</span>
                  ) : (
                    "Ask"
                  )}
                </button>
              </div>
            </div>
          </form>

          {/* Query Suggestions */}
          {showSuggestions && !loading && (
            <div className="suggestions-container">
              <div className="suggestions-header">Try these examples:</div>
              <div className="suggestions-list">
                {suggestions.map((suggestion, index) => (
                  <button
                    key={index}
                    className="suggestion-item"
                    onClick={() => handleSuggestionClick(suggestion)}
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Query History */}
          {showHistory && (
            <div className="history-container">
              <div className="history-header">
                <span>Query History</span>
                {queryHistory.length > 0 && (
                  <button className="clear-history" onClick={clearHistory}>
                    Clear
                  </button>
                )}
              </div>
              {queryHistory.length === 0 ? (
                <div className="history-empty">No queries yet</div>
              ) : (
                <div className="history-list">
                  {queryHistory.slice(0, 10).map((item) => (
                    <div
                      key={item.id}
                      className={`history-item ${item.success ? 'success' : 'error'}`}
                      onClick={() => handleHistoryClick(item)}
                    >
                      <div className="history-query">{item.query}</div>
                      <div className="history-meta">
                        <span className="history-time">
                          {formatTimestamp(item.timestamp)}
                        </span>
                        {item.success && item.recordCount !== undefined && (
                          <span className="history-records">
                            {item.recordCount} records
                          </span>
                        )}
                        {item.executionTime && (
                          <span className="history-duration">
                            {item.executionTime}ms
                          </span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
        {/* Loading State */}
        {loading && (
          <div className="loading-container">
            <div className="loading-spinner-large">⏳</div>
            <div className="loading-text">Processing your query...</div>
            <div className="loading-steps">
              <div className="loading-step">🧠 Analyzing your question</div>
              <div className="loading-step">🔍 Generating SQL query</div>
              <div className="loading-step">📊 Fetching data</div>
              <div className="loading-step">📈 Creating visualization</div>
            </div>
          </div>
        )}

        {/* Error Message */}
        {error && (
          <div className="error-container">
            <div className="error-icon">⚠️</div>
            <div className="error-content">
              <div className="error-title">Something went wrong</div>
              <div className="error-message">{error}</div>
              <button
                className="error-retry"
                onClick={() => setError("")}
              >
                Dismiss
              </button>
            </div>
          </div>
        )}

        {/* Response */}
        {response && !loading && (
          <div className="response-card">
            <div className="response-header">
              <div className="response-title">Results</div>
              <div className="response-actions">
                {response.execution_time && (
                  <div className="response-meta">
                    Executed in {response.execution_time}s
                    {response.record_count !== undefined && (
                      <span> • {response.record_count} records</span>
                    )}
                  </div>
                )}
                <div className="export-buttons">
                  <button
                    className="export-btn csv-btn"
                    onClick={() => exportData('csv')}
                    disabled={loading}
                    title="Export as CSV"
                  >
                    📊 CSV
                  </button>
                  <button
                    className="export-btn json-btn"
                    onClick={() => exportData('json')}
                    disabled={loading}
                    title="Export as JSON"
                  >
                    📄 JSON
                  </button>
                </div>
              </div>
            </div>

            <div className="section">
              <div className="section-header">💬 Answer</div>
              <div className="section-content">{response.response}</div>
            </div>

            {response.visualization && (
              <div className="section">
                <div className="section-header">📊 Visualization</div>
                <div className="visualization-container">
                  {response.visualization.startsWith('data:text/html') ? (
                    <iframe
                      src={response.visualization}
                      className="visualization-iframe"
                      title="Interactive Chart"
                      frameBorder="0"
                    />
                  ) : (
                    <img
                      src={response.visualization}
                      alt="Visualization"
                      className="visualization-img"
                    />
                  )}
                </div>
              </div>
            )}

            {response.sql_query && (
              <div className="section">
                <div className="section-header">🔍 SQL Query</div>
                <pre className="sql-query">{response.sql_query}</pre>
              </div>
            )}

            {response.data && response.data.length > 0 && (
              <div className="section">
                <div className="section-header">
                  📋 Raw Data ({response.data.length} records)
                </div>
                <div className="data-container">
                  <pre className="data-json">
                    {JSON.stringify(response.data.slice(0, 10), null, 2)}
                    {response.data.length > 10 && (
                      <div className="data-truncated">
                        ... and {response.data.length - 10} more records
                      </div>
                    )}
                  </pre>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
