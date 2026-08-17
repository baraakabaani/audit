import { useState, useEffect } from 'react';
import { getEngagements, createEngagement, type Engagement } from './api';
import EngagementDashboard from './components/EngagementDashboard';
import './App.css';

export default function App() {
  const [engagements, setEngagements] = useState<Engagement[]>([]);
  const [selected, setSelected] = useState<number | null>(null);
  const [creating, setCreating] = useState(false);
  const [newName, setNewName] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    loadEngagements();
  }, []);

  async function loadEngagements() {
    try {
      const data = await getEngagements();
      setEngagements(data);
    } catch {
      setError('Cannot connect to backend. Make sure the server is running on port 8000.');
    }
  }

  async function handleCreate() {
    if (!newName.trim()) return;
    setLoading(true);
    try {
      const result = await createEngagement({ name: newName });
      setNewName('');
      setCreating(false);
      await loadEngagements();
      setSelected(result.id);
    } catch {
      setError('Failed to create engagement.');
    }
    setLoading(false);
  }

  if (selected !== null) {
    return (
      <EngagementDashboard
        engagementId={selected}
        onBack={() => { setSelected(null); loadEngagements(); }}
      />
    );
  }

  return (
    <div className="app-root">
      <header className="app-header">
        <div className="header-inner">
          <h1>Audit Automation System</h1>
          <p className="subtitle">Professional Financial Statement &amp; Audit Report Preparation</p>
        </div>
        <div className="disclaimer-bar">
          ⚠ AI-generated classifications are subject to auditor review and approval.
          This system does not replace professional judgment.
        </div>
      </header>

      <main className="main-content">
        <div className="page-header">
          <h2>Engagements</h2>
          <button className="btn-primary" onClick={() => setCreating(true)}>+ New Engagement</button>
        </div>

        {error && <div className="alert alert-error">{error}</div>}

        {creating && (
          <div className="card mb-4">
            <h3 className="card-title">New Engagement</h3>
            <input
              className="input"
              placeholder="e.g. Dubai Women Establishment — December 2024"
              value={newName}
              onChange={e => setNewName(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleCreate()}
            />
            <div className="btn-row mt-2">
              <button className="btn-primary" onClick={handleCreate} disabled={loading}>
                {loading ? 'Creating…' : 'Create'}
              </button>
              <button className="btn-secondary" onClick={() => setCreating(false)}>Cancel</button>
            </div>
          </div>
        )}

        {engagements.length === 0 && !creating ? (
          <div className="empty-state">
            <p>No engagements yet. Click <strong>+ New Engagement</strong> to begin.</p>
          </div>
        ) : (
          <div className="engagement-list">
            {engagements.map(e => (
              <div key={e.id} className="engagement-card" onClick={() => setSelected(e.id)}>
                <div className="engagement-name">{e.name}</div>
                <div className="engagement-meta">
                  {e.entity_name && <span>{e.entity_name}</span>}
                  {e.period && <span> · {e.period}</span>}
                  <span className={`status-badge status-${e.status}`}>{e.status}</span>
                </div>
                <div className="engagement-sub">{e.currency} · {e.created_at?.slice(0, 10)}</div>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
