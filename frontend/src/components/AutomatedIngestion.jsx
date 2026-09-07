import React, { useState, useEffect } from 'react';
import { mentionsApi } from '../api/client';
import { Activity, Trash2, PlusCircle, RefreshCw } from 'lucide-react';

export default function AutomatedIngestion() {
  const [resources, setResources] = useState([]);
  const [loading, setLoading] = useState(false);
  const [adding, setAdding] = useState(false);
  const [platform, setPlatform] = useState('Instagram');
  const [resourceId, setResourceId] = useState('');
  const [message, setMessage] = useState('');

  const fetchResources = async () => {
    setLoading(true);
    try {
      const data = await mentionsApi.listMonitoredResources();
      setResources(data || []);
    } catch (err) {
      console.error(err);
      setMessage('Failed to load monitored resources');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchResources();
  }, []);

  const handleAdd = async (e) => {
    e.preventDefault();
    if (!resourceId.trim()) return;
    setAdding(true);
    setMessage('');
    try {
      await mentionsApi.addMonitoredResource({ platform, resource_id: resourceId });
      setMessage('Added to auto-polling engine.');
      setResourceId('');
      fetchResources();
    } catch (err) {
      setMessage('Failed to add resource.');
    } finally {
      setAdding(false);
    }
  };

  const handleDelete = async (id) => {
    try {
      await mentionsApi.deleteMonitoredResource(id);
      fetchResources();
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="card" style={{ marginTop: '1rem', border: '1px solid rgba(139, 92, 246, 0.3)' }}>
      <div className="card-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Activity className="w-5 h-5 text-purple-400" />
          <div>
            <h3 style={{ margin: 0 }}>Automated Polling Engine (Phase 2.5)</h3>
            <p style={{ margin: 0, fontSize: '0.85rem', color: '#9ca3af' }}>Background workers will automatically scrape these resources every 60 seconds.</p>
          </div>
        </div>
        <button onClick={fetchResources} className="btn-secondary" style={{ padding: '0.4rem', background: 'transparent', border: 'none' }}>
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      <div style={{ padding: '1.25rem' }}>
        {message && <p style={{ fontSize: '0.85rem', color: '#a78bfa', marginBottom: '1rem' }}>{message}</p>}
        
        <form onSubmit={handleAdd} style={{ display: 'flex', gap: '1rem', marginBottom: '1.5rem', alignItems: 'flex-end' }}>
          <div style={{ flex: 1 }}>
            <label style={{ display: 'block', fontSize: '0.85rem', marginBottom: '0.25rem', color: '#9ca3af' }}>Platform</label>
            <select 
              value={platform} 
              onChange={(e) => setPlatform(e.target.value)}
              style={{ width: '100%', padding: '0.5rem', borderRadius: '0.375rem', background: 'rgba(30,30,40,0.8)', border: '1px solid rgba(255,255,255,0.1)', color: 'white' }}
            >
              <option value="Instagram">Instagram</option>
              <option value="YouTube">YouTube</option>
            </select>
          </div>
          <div style={{ flex: 2 }}>
            <label style={{ display: 'block', fontSize: '0.85rem', marginBottom: '0.25rem', color: '#9ca3af' }}>Post/Video ID</label>
            <input 
              type="text" 
              value={resourceId}
              onChange={(e) => setResourceId(e.target.value)}
              placeholder="e.g., ig_post_4021"
              style={{ width: '100%', padding: '0.5rem', borderRadius: '0.375rem', background: 'rgba(30,30,40,0.8)', border: '1px solid rgba(255,255,255,0.1)', color: 'white' }}
            />
          </div>
          <button type="submit" disabled={adding} className="btn-primary" style={{ padding: '0.55rem 1rem' }}>
            <PlusCircle className="w-4 h-4 mr-1.5" />
            Add Resource
          </button>
        </form>

        <div style={{ background: 'rgba(0,0,0,0.2)', borderRadius: '0.5rem', overflow: 'hidden' }}>
          <table style={{ width: '100%', textAlign: 'left', fontSize: '0.875rem' }}>
            <thead>
              <tr style={{ background: 'rgba(255,255,255,0.05)', color: '#9ca3af' }}>
                <th style={{ padding: '0.75rem 1rem' }}>Platform</th>
                <th style={{ padding: '0.75rem 1rem' }}>Resource ID</th>
                <th style={{ padding: '0.75rem 1rem' }}>Last Scraped</th>
                <th style={{ padding: '0.75rem 1rem', textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {resources.length === 0 ? (
                <tr>
                  <td colSpan="4" style={{ padding: '1rem', textAlign: 'center', color: '#6b7280' }}>
                    No automated resources configured.
                  </td>
                </tr>
              ) : (
                resources.map(res => (
                  <tr key={res.id} style={{ borderTop: '1px solid rgba(255,255,255,0.05)' }}>
                    <td style={{ padding: '0.75rem 1rem' }}>{res.platform}</td>
                    <td style={{ padding: '0.75rem 1rem', fontWeight: 500, color: '#e5e7eb' }}>{res.resource_id}</td>
                    <td style={{ padding: '0.75rem 1rem', color: res.last_scraped_at ? '#a78bfa' : '#6b7280' }}>
                      {res.last_scraped_at ? new Date(res.last_scraped_at + 'Z').toLocaleString() : 'Pending...'}
                    </td>
                    <td style={{ padding: '0.75rem 1rem', textAlign: 'right' }}>
                      <button onClick={() => handleDelete(res.id)} style={{ background: 'transparent', border: 'none', color: '#ef4444', cursor: 'pointer' }} title="Stop monitoring">
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
