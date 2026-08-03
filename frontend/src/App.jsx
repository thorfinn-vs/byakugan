import React, { useState } from 'react';

export default function App() {
  // Target Configuration State
  const [url, setUrl] = useState('');
  const [cookie, setCookie] = useState('');
  const [authHeader, setAuthHeader] = useState('');
  const [selectedMethods, setSelectedMethods] = useState(['GET', 'POST', 'PUT', 'PATCH']);

  // Modal & Async Loading State
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [loading, setLoading] = useState(false);

  // Analysis Results & Errors State
  const [results, setResults] = useState(null);
  const [errorMessage, setErrorMessage] = useState('');
  const [activeTab, setActiveTab] = useState('json'); // 'json', 'curl', 'burp'

  // Method Chip Toggler
  const toggleMethod = (method) => {
    if (method === 'DELETE' && !selectedMethods.includes('DELETE')) {
      setShowDeleteModal(true);
      return;
    }

    if (selectedMethods.includes(method)) {
      setSelectedMethods(selectedMethods.filter((m) => m !== method));
    } else {
      setSelectedMethods([...selectedMethods, method]);
    }
  };

  const confirmDeleteMethod = () => {
    setSelectedMethods([...selectedMethods, 'DELETE']);
    setShowDeleteModal(false);
  };

  // Execute Probe Handler
  const handleProbe = async () => {
    if (!url) {
      setErrorMessage('Please enter a target API Endpoint URL!');
      return;
    }

    setErrorMessage('');
    setLoading(true);
    setResults(null);

    const payload = {
      url: url,
      cookie: cookie,
      headers: authHeader ? { Authorization: authHeader } : {},
      methods: selectedMethods
    };

    try {
      const response = await fetch('http://localhost:5000/api/probe', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      const data = await response.json();
      if (response.ok) {
        setResults(data);
      } else {
        setErrorMessage(data.error || 'Failed to probe target endpoint.');
      }
    } catch (err) {
      setErrorMessage('Could not connect to Byakugan backend (http://localhost:5000). Make sure app.py is running!');
    } finally {
      setLoading(false);
    }
  };

  // Helper to generate cURL snippet
  const getCurlSnippet = () => {
    if (!results || !results.url) return '';
    const bodyStr = JSON.stringify(results.synthesized_payload, null, 2);
    let curl = `curl -X PUT "${results.url}" \\\n  -H "Content-Type: application/json"`;
    if (authHeader) curl += ` \\\n  -H "Authorization: ${authHeader}"`;
    if (cookie) curl += ` \\\n  -H "Cookie: ${cookie}"`;
    curl += ` \\\n  -d '${bodyStr}'`;
    return curl;
  };

  // Helper to generate Burp Repeater snippet
  const getBurpSnippet = () => {
    if (!results || !results.url) return '';
    try {
      const parsedUrl = new URL(results.url);
      const path = parsedUrl.pathname + parsedUrl.search;
      const host = parsedUrl.host;
      const bodyStr = JSON.stringify(results.synthesized_payload, null, 2);

      let raw = `PUT ${path} HTTP/1.1\nHost: ${host}\nContent-Type: application/json\nContent-Length: ${bodyStr.length}\n`;
      if (authHeader) raw += `Authorization: ${authHeader}\n`;
      if (cookie) raw += `Cookie: ${cookie}\n`;
      raw += `User-Agent: Byakugan-Probe/1.0\n\n${bodyStr}`;
      return raw;
    } catch (e) {
      return JSON.stringify(results.synthesized_payload, null, 2);
    }
  };

  return (
    <div className="app-container">
      {/* Header Bar */}
      <header className="header">
        <div className="logo-group">
          <div className="eye-icon">
            <div className="eye-pupil"></div>
          </div>
          <div>
            <h1 className="app-title">BYAKUGAN 👁️</h1>
            <p className="subtitle">REST API Method & Schema Introspection Workbench</p>
          </div>
        </div>
      </header>

      {/* Main Grid */}
      <div className="grid-2">
        {/* Left Column: Input Setup */}
        <div>
          <div className="card">
            <h2 className="card-title">🎯 Target Endpoint Setup</h2>

            {errorMessage && (
              <div style={{ color: 'var(--accent-red)', marginBottom: '1rem', fontSize: '0.875rem' }}>
                ⚠️ {errorMessage}
              </div>
            )}

            <div className="form-group">
              <label className="form-label">API Endpoint URL</label>
              <input
                type="text"
                className="input-text"
                placeholder="https://api.target.com/v1/users/123"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
              />
            </div>

            <div className="form-group">
              <label className="form-label">Cookie String (Optional)</label>
              <input
                type="text"
                className="input-text"
                placeholder="session=abc123xyz; token=eyJ..."
                value={cookie}
                onChange={(e) => setCookie(e.target.value)}
              />
            </div>

            <div className="form-group">
              <label className="form-label">Authorization Header (Optional)</label>
              <input
                type="text"
                className="input-text"
                placeholder="Bearer eyJhbGciOi..."
                value={authHeader}
                onChange={(e) => setAuthHeader(e.target.value)}
              />
            </div>

            <div className="form-group">
              <label className="form-label">HTTP Methods to Probe</label>
              <div className="verb-toggle-group">
                {['GET', 'POST', 'PUT', 'PATCH', 'DELETE'].map((method) => {
                  const activeClass = selectedMethods.includes(method) ? `active-${method.toLowerCase()}` : '';
                  return (
                    <div
                      key={method}
                      className={`verb-chip ${activeClass}`}
                      onClick={() => toggleMethod(method)}
                    >
                      {method}
                    </div>
                  );
                })}
              </div>
            </div>

            <button className="btn-primary" onClick={handleProbe} disabled={loading}>
              {loading ? '👁️ Scanning API Schema...' : '👁️ Activate Byakugan Probe'}
            </button>
          </div>
        </div>

        {/* Right Column: Schema Matrix & Payload Workbench */}
        <div>
          {results ? (
            <div>
              {/* Field Classification Matrix */}
              <div className="card">
                <h2 className="card-title">📊 Discovered Field Matrix</h2>

                <div style={{ marginBottom: '1rem' }}>
                  <div className="form-label">Allowed Writable Fields</div>
                  <div className="badge-list">
                    {results.field_analysis.allowed_fields?.map((field) => (
                      <span key={field} className="badge badge-green">✓ {field}</span>
                    )) || <span style={{ color: 'var(--text-dim)', fontSize: '0.8rem' }}>None detected</span>}
                  </div>
                </div>

                <div style={{ marginBottom: '1rem' }}>
                  <div className="form-label">Required Fields (Discovered via Validation Errors)</div>
                  <div className="badge-list">
                    {results.field_analysis.required_fields?.map((field) => (
                      <span key={field} className="badge badge-purple">* {field}</span>
                    )) || <span style={{ color: 'var(--text-dim)', fontSize: '0.8rem' }}>None required</span>}
                  </div>
                </div>

                <div style={{ marginBottom: '1rem' }}>
                  <div className="form-label">Read-Only / System IDs</div>
                  <div className="badge-list">
                    {results.field_analysis.read_only_fields?.map((field) => (
                      <span key={field} className="badge badge-amber">🔒 {field}</span>
                    )) || <span style={{ color: 'var(--text-dim)', fontSize: '0.8rem' }}>None</span>}
                  </div>
                </div>

                <div>
                  <div className="form-label">Mass Assignment Targets (Privilege / Security)</div>
                  <div className="badge-list">
                    {results.field_analysis.mass_assignment_candidates?.map((field) => (
                      <span key={field} className="badge badge-red">⚡ {field}</span>
                    )) || <span style={{ color: 'var(--text-dim)', fontSize: '0.8rem' }}>None flagged</span>}
                  </div>
                </div>
              </div>

              {/* Synthesized Payload & Exporter */}
              <div className="card">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                  <h2 className="card-title" style={{ margin: 0 }}>🛠️ Synthesized Payload</h2>
                  <div style={{ display: 'flex', gap: '0.5rem' }}>
                    <button
                      className={`verb-chip ${activeTab === 'json' ? 'active-patch' : ''}`}
                      onClick={() => setActiveTab('json')}
                    >
                      JSON Body
                    </button>
                    <button
                      className={`verb-chip ${activeTab === 'curl' ? 'active-put' : ''}`}
                      onClick={() => setActiveTab('curl')}
                    >
                      cURL Export
                    </button>
                    <button
                      className={`verb-chip ${activeTab === 'burp' ? 'active-post' : ''}`}
                      onClick={() => setActiveTab('burp')}
                    >
                      Burp Raw
                    </button>
                  </div>
                </div>

                <pre className="code-block">
                  {activeTab === 'json' && JSON.stringify(results.synthesized_payload, null, 2)}
                  {activeTab === 'curl' && getCurlSnippet()}
                  {activeTab === 'burp' && getBurpSnippet()}
                </pre>
              </div>
            </div>
          ) : (
            <div className="card" style={{ textAlign: 'center', padding: '3.5rem 1.5rem', color: 'var(--text-muted)' }}>
              <div style={{ fontSize: '2.8rem', marginBottom: '0.5rem' }}>👁️</div>
              <h3>Byakugan Standby</h3>
              <p style={{ fontSize: '0.85rem', marginTop: '0.5rem' }}>
                Enter an API endpoint URL and click probe to visualize allowed fields, validation errors, and reconstructed JSON payloads.
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Safety Modal for DELETE Method */}
      {showDeleteModal && (
        <div className="modal-backdrop">
          <div className="modal-card">
            <h2 style={{ color: 'var(--accent-red)', marginBottom: '0.75rem' }}>⚠️ Destructive Operation Warning</h2>
            <p style={{ fontSize: '0.9rem', marginBottom: '1rem' }}>
              Probing the <strong>DELETE</strong> method will send an HTTP DELETE request to the target API endpoint.
            </p>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
              Are you sure you want to include <code>DELETE</code> in your method test list?
            </p>

            <div className="modal-actions">
              <button className="btn-secondary" onClick={() => setShowDeleteModal(false)}>Cancel</button>
              <button className="btn-danger" onClick={confirmDeleteMethod}>Confirm DELETE Probe</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
