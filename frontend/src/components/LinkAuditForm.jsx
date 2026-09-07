import React, { useState } from 'react';
import { auditApi } from '../api/client';
import { Link2, Sparkles, AlertCircle, Key, ChevronDown, ChevronUp, CheckCircle, Video, Camera, ShieldCheck } from 'lucide-react';

export default function LinkAuditForm({ onAuditComplete }) {
  const [url, setUrl] = useState('');
  const [igUsername, setIgUsername] = useState('');
  const [showConfig, setShowConfig] = useState(false);

  // Optional credentials
  const [ytApiKey, setYtApiKey] = useState('');
  const [igToken, setIgToken] = useState('');
  const [igAccountId, setIgAccountId] = useState('');

  // AI auditor config
  const [enableAi, setEnableAi] = useState(false);
  const [aiProvider, setAiProvider] = useState('ollama');
  const [aiModel, setAiModel] = useState('qwen3:8b');
  const [aiApiKey, setAiApiKey] = useState('');

  const handleProviderChange = (newProvider) => {
    setAiProvider(newProvider);
    if (newProvider === 'gemini') {
      setAiApiKey('');
      setAiModel('gemini-3.6-flash');
    } else if (newProvider === 'groq') {
      setAiModel('llama-3.3-70b-versatile');
    } else {
      setAiModel('qwen3:8b');
    }
  };

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const isInstagram = url.includes('instagram.com');
  const isYouTube = url.includes('youtube.com') || url.includes('youtu.be');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!url.trim()) {
      setError('Please provide a valid YouTube or Instagram post URL.');
      return;
    }

    setLoading(true);
    try {
      const payload = {
        url: url.trim(),
        ig_username: igUsername.trim() || null,
        yt_api_key: ytApiKey.trim() || null,
        ig_token: igToken.trim() || null,
        ig_account_id: igAccountId.trim() || null,
        enable_ai: enableAi,
        ai_provider: aiProvider,
        ai_model: aiModel.trim() || null,
        ai_api_key: aiProvider === 'gemini' ? null : (aiApiKey.trim() || null),
      };

      const result = await auditApi.auditLink(payload);
      onAuditComplete(result);
    } catch (err) {
      setError(err.message || 'Failed to fetch and audit post.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card">
      <div className="card-header">
        <div>
          <h2>Verify Post / Video via Link</h2>
          <p>Ingest public Instagram posts or YouTube videos to run automated OCR and compliance auditing</p>
        </div>
        <div className="platform-badges-row">
          <span className="badge-platform"><Video className="w-3.5 h-3.5 mr-1" /> YouTube</span>
          <span className="badge-platform"><Camera className="w-3.5 h-3.5 mr-1" /> Instagram</span>
        </div>
      </div>

      {error && (
        <div className="alert-box error">
          <AlertCircle className="w-4 h-4" />
          <span>{error}</span>
        </div>
      )}

      <form onSubmit={handleSubmit} className="audit-form">
        <div className="form-group">
          <label htmlFor="post_url">
            Post or Video URL <span className="text-red-400">*</span>
          </label>
          <div className="input-wrapper">
            <Link2 className="input-icon" />
            <input
              id="post_url"
              type="text"
              required
              placeholder="https://www.youtube.com/watch?v=... or https://www.instagram.com/p/..."
              value={url}
              onChange={(e) => setUrl(e.target.value)}
            />
          </div>
        </div>

        {isInstagram && (
          <div className="form-group">
            <label htmlFor="ig_username">
              Instagram Creator Username <span className="text-red-400">*</span>
            </label>
            <input
              id="ig_username"
              type="text"
              placeholder="e.g. gyanm.samarth.academy (required for Meta Business Discovery API)"
              value={igUsername}
              onChange={(e) => setIgUsername(e.target.value)}
            />
          </div>
        )}

        {/* Credentials & AI Config Accordion */}
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
              Leave blank if already defined in your <code>.env</code> file.
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

            <hr className="divider-subtle" />

            {/* AI Auditor settings */}
            <div className="checkbox-row" style={{ marginTop: '0.75rem' }}>
              <input
                type="checkbox"
                id="enable_ai"
                checked={enableAi}
                onChange={(e) => setEnableAi(e.target.checked)}
              />
              <label htmlFor="enable_ai">Enable AI Auditor Layer (LangChain)</label>
            </div>

            {enableAi && (
              <div className="nested-field">
                <div className="form-grid-2" style={{ marginTop: '0.5rem' }}>
                  <div className="form-group">
                    <label>AI Provider</label>
                    <select value={aiProvider} onChange={(e) => handleProviderChange(e.target.value)}>
                      <option value="ollama">Ollama (Local)</option>
                      <option value="gemini">Google Gemini</option>
                      <option value="groq">Groq</option>
                    </select>
                  </div>

                  <div className="form-group">
                    <label>Model Name</label>
                    <input
                      type="text"
                      value={aiModel}
                      onChange={(e) => setAiModel(e.target.value)}
                      placeholder={aiProvider === 'gemini' ? 'gemini-3.6-flash' : aiProvider === 'groq' ? 'llama-3.3-70b-versatile' : 'qwen3:8b'}
                    />
                  </div>
                </div>

                {aiProvider === 'gemini' && (
                  <div className="env-notice-box">
                    <ShieldCheck className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                    <span>
                      Gemini API key is configured and loaded securely from backend <code>.env</code>.
                    </span>
                  </div>
                )}

                {aiProvider === 'groq' && (
                  <div className="form-group">
                    <label>Groq API Key (Optional)</label>
                    <input
                      type="password"
                      placeholder="Leave blank to use GROQ_API_KEY from backend .env"
                      value={aiApiKey}
                      onChange={(e) => setAiApiKey(e.target.value)}
                    />
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        <button type="submit" disabled={loading} className="btn-primary" style={{ marginTop: '0.5rem' }}>
          <Sparkles className="w-4 h-4 mr-2" />
          {loading ? 'Fetching Media & Auditing OCR...' : 'Fetch and Audit Post'}
        </button>
      </form>
    </div>
  );
}
