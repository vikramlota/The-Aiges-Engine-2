import React, { useState } from 'react';
import { auditApi } from '../api/client';
import { TrendingUp, Sparkles, AlertCircle, Key, ChevronDown, ChevronUp, CheckCircle2, AlertOctagon, AlertTriangle, ExternalLink, ShieldCheck } from 'lucide-react';

export default function AccountAuditForm() {
  const [accountUrl, setAccountUrl] = useState('');
  const [limit, setLimit] = useState(5);
  const [showConfig, setShowConfig] = useState(false);

  const [ytApiKey, setYtApiKey] = useState('');
  const [igToken, setIgToken] = useState('');
  const [igAccountId, setIgAccountId] = useState('');

  const [enableAi, setEnableAi] = useState(false);
  const [aiProvider, setAiProvider] = useState('ollama');
  const [aiModel, setAiModel] = useState('qwen3:8b');
  const [aiApiKey, setAiApiKey] = useState('');

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [accountResult, setAccountResult] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!accountUrl.trim()) {
      setError('Please provide a valid YouTube channel or Instagram profile URL.');
      return;
    }

    setLoading(true);
    try {
      const payload = {
        account_url: accountUrl.trim(),
        limit: Number(limit),
        yt_api_key: ytApiKey.trim() || null,
        ig_token: igToken.trim() || null,
        ig_account_id: igAccountId.trim() || null,
        enable_ai: enableAi,
        ai_provider: aiProvider,
        ai_model: aiModel.trim() || null,
        ai_api_key: aiProvider === 'gemini' ? null : (aiApiKey.trim() || null),
      };

      const result = await auditApi.auditAccount(payload);
      setAccountResult(result);
    } catch (err) {
      setError(err.message || 'Multi-post account audit failed.');
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setAccountResult(null);
  };

  return (
    <div className="card">
      <div className="card-header">
        <div>
          <h2>Multi-Post Account Audit</h2>
          <p>Scan multiple recent posts or videos of a creator to calculate an overall compliance health score</p>
        </div>
      </div>

      {error && (
        <div className="alert-box error">
          <AlertCircle className="w-4 h-4" />
          <span>{error}</span>
        </div>
      )}

      {accountResult ? (
        <div className="account-result-container">
          <div className="account-result-header">
            <div className="flex items-center justify-between">
              <div>
                <h3>{accountResult.target_name} ({accountResult.platform})</h3>
                <span className="text-secondary text-sm">Batch Compliance Health Assessment</span>
              </div>
              <button onClick={handleReset} className="btn-secondary">
                Audit Another Account
              </button>
            </div>
          </div>

          {/* Health Score Banner */}
          <div className="health-score-banner">
            <div className="score-circle">
              <span className="score-number">{accountResult.health_score}%</span>
              <span className="score-label">HEALTH SCORE</span>
            </div>

            <div className="score-stats-grid">
              <div className="stat-card">
                <span className="stat-val">{accountResult.total_audited}</span>
                <span className="stat-lbl">Posts Audited</span>
              </div>
              <div className="stat-card stat-success">
                <span className="stat-val">{accountResult.compliant_count}</span>
                <span className="stat-lbl">Compliant</span>
              </div>
              <div className="stat-card stat-error">
                <span className="stat-val">{accountResult.flagged_count}</span>
                <span className="stat-lbl">Violations</span>
              </div>
              <div className="stat-card stat-warning">
                <span className="stat-val">{accountResult.expert_review_count}</span>
                <span className="stat-lbl">Expert Review</span>
              </div>
            </div>
          </div>

          {/* Individual Audited Posts Table */}
          <div className="account-posts-section">
            <h4>Audited Posts Breakdown</h4>
            <div className="account-posts-table-wrapper">
              <table className="account-posts-table">
                <thead>
                  <tr>
                    <th>Post / Video</th>
                    <th>Status</th>
                    <th>Risk</th>
                    <th>Confirmed Violations</th>
                    <th>Visual OCR</th>
                  </tr>
                </thead>
                <tbody>
                  {accountResult.posts.map((post) => (
                    <tr key={post.post_id}>
                      <td>
                        <a
                          href={post.post_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="post-table-link"
                        >
                          {post.post_id.length > 15 ? `${post.post_id.substring(0, 15)}...` : post.post_id}
                          <ExternalLink className="w-3 h-3 inline ml-1" />
                        </a>
                      </td>
                      <td>
                        <span className={`status-pill pill-${post.status.toLowerCase().replace(/\s+/g, '-')}`}>
                          {post.status}
                        </span>
                      </td>
                      <td>
                        {post.risk_level ? (
                          <span className="history-risk-badge">{post.risk_level}</span>
                        ) : (
                          <span className="text-muted">-</span>
                        )}
                      </td>
                      <td>
                        {post.caption_flags && post.caption_flags.length > 0 ? (
                          <span className="text-red-400 font-semibold">
                            {post.caption_flags.join(', ')}
                          </span>
                        ) : (
                          <span className="text-emerald-400">None</span>
                        )}
                      </td>
                      <td>
                        <span className="text-xs text-secondary">
                          {post.visual_status === 'DISCLOSURE_VISIBLE' ? (
                            <span className="text-emerald-400">Label in image</span>
                          ) : post.visual_status === 'NO_MEDIA' ? (
                            'Video file'
                          ) : (
                            post.visual_status
                          )}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="audit-form">
          <div className="form-group">
            <label htmlFor="account_url">
              Channel or Profile URL <span className="text-red-400">*</span>
            </label>
            <div className="input-wrapper">
              <TrendingUp className="input-icon" />
              <input
                id="account_url"
                type="text"
                required
                placeholder="https://www.youtube.com/@techcreator or https://www.instagram.com/brandname/"
                value={accountUrl}
                onChange={(e) => setAccountUrl(e.target.value)}
              />
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="post_limit">
              Number of Recent Posts to Audit: <strong className="text-emerald-400">{limit}</strong>
            </label>
            <input
              id="post_limit"
              type="range"
              min="1"
              max="15"
              value={limit}
              onChange={(e) => setLimit(e.target.value)}
              className="range-slider"
            />
          </div>

          {/* Credentials Accordion */}
          <div className="advanced-toggle" onClick={() => setShowConfig(!showConfig)}>
            <div className="flex items-center gap-2">
              <Key className="w-4 h-4 text-emerald-400" />
              <span>API Credentials & AI Auditor Settings</span>
            </div>
            {showConfig ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </div>

          {showConfig && (
            <div className="advanced-section">
              <p className="section-note">
                Leave blank if defined in your <code>.env</code> file.
              </p>

              <div className="form-group">
                <label>YouTube Data API v3 Key</label>
                <input
                  type="password"
                  placeholder="AIzaSy..."
                  value={ytApiKey}
                  onChange={(e) => setYtApiKey(e.target.value)}
                />
              </div>

              <div className="form-grid-2">
                <div className="form-group">
                  <label>Instagram Access Token</label>
                  <input
                    type="password"
                    placeholder="EAABw..."
                    value={igToken}
                    onChange={(e) => setIgToken(e.target.value)}
                  />
                </div>

                <div className="form-group">
                  <label>Instagram Business Account ID</label>
                  <input
                    type="text"
                    placeholder="17841..."
                    value={igAccountId}
                    onChange={(e) => setIgAccountId(e.target.value)}
                  />
                </div>
              </div>
            </div>
          )}

          <button type="submit" disabled={loading} className="btn-primary" style={{ marginTop: '0.5rem' }}>
            <Sparkles className="w-4 h-4 mr-2" />
            {loading ? `Auditing ${limit} Posts from Pipeline...` : 'Run Multi-Post Account Audit'}
          </button>
        </form>
      )}
    </div>
  );
}
