import React, { useState, useEffect } from 'react';
import { auditApi } from '../api/client';
import { Clock, Search, RefreshCw, ChevronRight, AlertOctagon, CheckCircle2, AlertTriangle, HelpCircle } from 'lucide-react';

export default function HistoryList({ onSelectAudit, activeAuditId }) {
  const [audits, setAudits] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');

  const loadAudits = async () => {
    setLoading(true);
    try {
      const data = await auditApi.listAudits();
      setAudits(data);
    } catch (err) {
      console.error('Failed to load audit history', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAudits();
  }, []);

  const filtered = audits.filter(
    (a) =>
      a.caption.toLowerCase().includes(searchTerm.toLowerCase()) ||
      a.status.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (a.risk_level && a.risk_level.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  return (
    <div className="card history-card">
      <div className="card-header">
        <div className="flex items-center gap-2">
          <Clock className="w-5 h-5 text-emerald-400" />
          <h3>Audit History ({audits.length})</h3>
        </div>
        <button onClick={loadAudits} className="btn-icon" title="Refresh history">
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      <div className="search-bar">
        <Search className="w-4 h-4 text-gray-400" />
        <input
          type="text"
          placeholder="Filter by caption, status, or risk..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />
      </div>

      <div className="history-items-container">
        {loading && audits.length === 0 ? (
          <div className="empty-state">Loading your audit history...</div>
        ) : filtered.length === 0 ? (
          <div className="empty-state">
            {searchTerm ? 'No audits match your filter.' : 'No audit records yet. Submit a post above!'}
          </div>
        ) : (
          filtered.map((item) => {
            const isActive = activeAuditId === item.id;
            return (
              <div
                key={item.id}
                className={`history-item ${isActive ? 'active' : ''}`}
                onClick={() => onSelectAudit(item.id)}
              >
                <div className="history-item-top">
                  <span className="history-item-id">#{item.id}</span>
                  <span className={`status-pill pill-${item.status.toLowerCase().replace(/\s+/g, '-')}`}>
                    {item.status}
                  </span>
                </div>

                <p className="history-item-caption">
                  {item.caption ? (item.caption.length > 70 ? `${item.caption.substring(0, 70)}...` : item.caption) : '(No caption)'}
                </p>

                <div className="history-item-bottom">
                  <span className="history-item-date">
                    {new Date(item.created_at).toLocaleDateString()} {new Date(item.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </span>
                  {item.risk_level && (
                    <span className="history-risk-badge">{item.risk_level}</span>
                  )}
                  <ChevronRight className="w-4 h-4 text-gray-400" />
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
