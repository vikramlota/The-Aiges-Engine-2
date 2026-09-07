import React, { useState, useEffect } from 'react';
import { mentionsApi } from '../api/client';
import {
  TrendingDown,
  TrendingUp,
  AlertOctagon,
  AlertTriangle,
  Smile,
  Frown,
  Meh,
  MessageSquare,
  PlusCircle,
  RefreshCw,
  Sparkles,
  Filter,
  CheckCircle2,
  Calendar,
  Camera,
  Copy,
  Check,
  ShieldCheck,
  Send,
  Edit3,
  Globe,
  Trash2,
  HelpCircle
} from 'lucide-react';
import AutomatedIngestion from './AutomatedIngestion';

const DEMO_PRESETS = {
  '-- Select a Demo Preset --': null,
  'Balanced Customer Feedback': [
    { text: 'Really loved the packaging and the texture is amazing!', author_handle: '@priya_m' },
    { text: 'Received it on time. Seems decent so far.', author_handle: '@rahul_k' },
    { text: 'Great results on my dry skin after one week.', author_handle: '@ananya_glow' },
    { text: 'Where can I order the full-size bottle?', author_handle: '@deepak88' },
    { text: 'Did not notice much difference honestly.', author_handle: '@sneha_v' },
  ],
  'Reputation Crisis / Backlash Spike': [
    { text: 'Total scam! The product caused severe burning and allergy!', author_handle: '@angry_buyer1' },
    { text: 'Fake claims! I will file a complaint in consumer court and CCPA.', author_handle: '@rohit_legal' },
    { text: 'Worst customer support ever. They cheated me and refused my refund.', author_handle: '@meera_s' },
    { text: 'Broken bottle delivered, packaging is hazardous and leaking!', author_handle: '@vikram_g' },
    { text: 'Do not buy this, it is deceptive marketing and counterfeit!', author_handle: '@neha_alert' },
  ],
  'Indic / Hinglish Multilingual Feedback': [
    { text: 'Bhai bilkul bekaar customer service hai, delivery late aayi aur paisa barbaad!', author_handle: '@harsh_delhi' },
    { text: 'यह उत्पाद सच में बहुत अच्छा और असरदार है, मुझे बहुत पसंद आया!', author_handle: '@pooja_patel' },
    { text: 'Ekdum ghatiya experience, product nakli nikla. Total fraud seller!', author_handle: '@arjun_99' },
    { text: 'Packaging bohot zabardast hai, quality ekdum A1!', author_handle: '@simran_kaur' },
    { text: 'Customer care wale phone nahi uthate, bilkul bakwas support.', author_handle: '@varun_mumbai' },
  ],
};

export default function SentimentMonitor() {
  const [summary, setSummary] = useState(null);
  const [mentions, setMentions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filterSentiment, setFilterSentiment] = useState(null);
  const [filterLanguage, setFilterLanguage] = useState(null);
  const [filterFlaggedOnly, setFilterFlaggedOnly] = useState(false);

  // Ingestion form state
  const [showIngest, setShowIngest] = useState(false);
  const [postId, setPostId] = useState(`ig_${Date.now().toString().slice(-6)}`);
  const [rawComments, setRawComments] = useState('');
  const [authorHandle, setAuthorHandle] = useState('@user');
  const [ingesting, setIngesting] = useState(false);
  const [ingestMsg, setIngestMsg] = useState('');

  // DPDP Retention cleanup state
  const [cleaningRetention, setCleaningRetention] = useState(false);
  const [cleanupMsg, setCleanupMsg] = useState(null);

  // Phase 2.2 Response Drafting & Approval states
  const [draftingIds, setDraftingIds] = useState(new Set());
  const [approvingIds, setApprovingIds] = useState(new Set());
  const [editedReplies, setEditedReplies] = useState({});
  const [copiedId, setCopiedId] = useState(null);

  const loadData = async () => {
    setLoading(true);
    try {
      const [sumData, mentionsData] = await Promise.all([
        mentionsApi.getSummary(),
        mentionsApi.getMentions({
          sentiment: filterSentiment,
          language: filterLanguage,
          flagged_only: filterFlaggedOnly,
          limit: 100,
        }),
      ]);
      setSummary(sumData);
      setMentions(mentionsData);

      // Initialize editedReplies for existing drafts
      const initialEdits = {};
      mentionsData.forEach((m) => {
        if (m.drafted_reply) {
          initialEdits[m.id] = m.drafted_reply;
        }
      });
      setEditedReplies(initialEdits);
    } catch (err) {
      console.error('Failed to load sentiment monitoring data', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [filterSentiment, filterLanguage, filterFlaggedOnly]);

  const handleRetentionCleanup = async () => {
    if (!window.confirm('Execute DPDP Act Data Retention Cleanup?\nThis will permanently purge all comment mentions older than 90 days.')) {
      return;
    }
    setCleaningRetention(true);
    setCleanupMsg(null);
    try {
      const res = await mentionsApi.cleanupMentions(90);
      setCleanupMsg(`DPDP Retention Cleanup complete: Purged ${res.deleted_count} comment mentions older than 90 days.`);
      await loadData();
      setTimeout(() => setCleanupMsg(null), 6000);
    } catch (err) {
      alert(`Cleanup failed: ${err.message}`);
    } finally {
      setCleaningRetention(false);
    }
  };

  const handlePresetSelect = (presetKey) => {
    const preset = DEMO_PRESETS[presetKey];
    if (!preset) return;
    const formatted = preset.map((c) => `${c.author_handle}: ${c.text}`).join('\n');
    setRawComments(formatted);
  };

  const handleIngestSubmit = async (e) => {
    e.preventDefault();
    if (!rawComments.trim()) return;

    setIngesting(true);
    setIngestMsg('');

    try {
      const lines = rawComments
        .split('\n')
        .map((l) => l.trim())
        .filter(Boolean);

      const parsedComments = lines.map((line) => {
        let handle = authorHandle;
        let text = line;
        if (line.includes(':')) {
          const parts = line.split(':');
          if (parts[0].startsWith('@')) {
            handle = parts[0].trim();
            text = parts.slice(1).join(':').trim();
          }
        }
        return { text, author_handle: handle };
      });

      await mentionsApi.ingestMentions({
        post_id: postId.trim() || `post_${Date.now()}`,
        platform: 'Instagram',
        author_handle: authorHandle,
        comments: parsedComments,
      });

      setIngestMsg(`Successfully analyzed and ingested ${parsedComments.length} comments!`);
      setRawComments('');
      setPostId(`ig_${Date.now().toString().slice(-6)}`);
      await loadData();
    } catch (err) {
      setIngestMsg(`Ingestion failed: ${err.message}`);
    } finally {
      setIngesting(false);
    }
  };

  // --- Phase 2.2: Response-Drafting Handlers ---

  const handleDraftReply = async (mentionId) => {
    setDraftingIds((prev) => new Set(prev).add(mentionId));
    try {
      const res = await mentionsApi.draftReply(mentionId, { brand_name: 'Our Brand' });
      setMentions((prev) =>
        prev.map((m) =>
          m.id === mentionId
            ? { ...m, drafted_reply: res.drafted_reply, draft_explanation: res.draft_explanation }
            : m
        )
      );
      setEditedReplies((prev) => ({ ...prev, [mentionId]: res.drafted_reply }));
    } catch (err) {
      alert(`Draft generation failed: ${err.message}`);
    } finally {
      setDraftingIds((prev) => {
        const next = new Set(prev);
        next.delete(mentionId);
        return next;
      });
    }
  };

  const handleApproveReply = async (mentionId) => {
    setApprovingIds((prev) => new Set(prev).add(mentionId));
    try {
      const currentText = editedReplies[mentionId];
      const res = await mentionsApi.approveReply(mentionId, { edited_reply: currentText });
      setMentions((prev) =>
        prev.map((m) =>
          m.id === mentionId
            ? {
                ...m,
                drafted_reply: res.drafted_reply,
                approved_by: res.approved_by,
                approved_at: res.approved_at,
              }
            : m
        )
      );
    } catch (err) {
      alert(`Approval failed: ${err.message}`);
    } finally {
      setApprovingIds((prev) => {
        const next = new Set(prev);
        next.delete(mentionId);
        return next;
      });
    }
  };

  const handleCopyReply = (mentionId, text) => {
    navigator.clipboard.writeText(text);
    setCopiedId(mentionId);
    setTimeout(() => setCopiedId(null), 2000);
  };

  return (
    <div className="sentiment-monitor-container">
      {/* Top Action Bar */}
      <div className="sentiment-header-bar">
        <div>
          <h2>Sentiment & Reputation Monitor</h2>
          <p>Phase 2.1 Anomaly Monitoring & Phase 2.2 Human-Approved Response Drafting</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={handleRetentionCleanup}
            disabled={cleaningRetention}
            className="btn-secondary"
            style={{ padding: '0.5rem 0.9rem', fontSize: '0.825rem' }}
            title="Purge mentions older than 90 days for DPDP Act compliance"
          >
            <Trash2 className="w-3.5 h-3.5 mr-1.5 text-red-400" />
            {cleaningRetention ? 'Purging Old Data...' : 'DPDP Purge (90d+)'}
          </button>
          <button onClick={() => setShowIngest(!showIngest)} className="btn-primary" style={{ padding: '0.5rem 1rem', fontSize: '0.85rem' }}>
            <PlusCircle className="w-4 h-4 mr-1.5" />
            {showIngest ? 'Close Ingest Form' : 'Ingest Post Comments'}
          </button>
          <button onClick={loadData} className="btn-secondary" title="Refresh data">
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {cleanupMsg && (
        <div className="alert-box" style={{ background: 'rgba(59, 130, 246, 0.15)', color: '#93c5fd', borderColor: 'rgba(59, 130, 246, 0.3)' }}>
          <CheckCircle2 className="w-4 h-4" />
          <span>{cleanupMsg}</span>
        </div>
      )}

      {/* Statistical Anomaly Spike Alert Banner */}
      {summary?.anomaly?.is_anomalous && (
        <div className="anomaly-alert-banner">
          <div className="anomaly-alert-icon">
            <AlertOctagon className="w-8 h-8 text-red-400 animate-pulse" />
          </div>
          <div className="anomaly-alert-content">
            <div className="anomaly-badge">🚨 REPUTATION ANOMALY SPIKE DETECTED</div>
            <h3>{summary.anomaly.explanation}</h3>
            <p>
              Daily negative feedback ({summary.anomaly.current_daily_negative}) has exceeded the 2x statistical baseline
              ({summary.anomaly.trailing_7day_avg}/day). Review flagged comments below and use the Response-Drafting Agent to draft de-escalating replies.
            </p>
          </div>
        </div>
      )}

      {/* Ingestion Drawer */}
      {showIngest && (
        <div className="card ingest-card">
          <div className="card-header">
            <div>
              <h3>Ingest Comments for Audited Instagram Post</h3>
              <p>Scores each comment using offline VADER / Multilingual AI, flags sensitive brand crises, and updates daily trend baselines</p>
            </div>
            <div className="preset-selector">
              <select onChange={(e) => handlePresetSelect(e.target.value)} defaultValue="">
                {Object.keys(DEMO_PRESETS).map((key) => (
                  <option key={key} value={key}>
                    {key}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {ingestMsg && (
            <div className={`alert-box ${ingestMsg.includes('failed') ? 'error' : ''}`} style={{ background: ingestMsg.includes('failed') ? undefined : 'rgba(16, 185, 129, 0.15)', color: ingestMsg.includes('failed') ? undefined : '#6ee7b7' }}>
              <CheckCircle2 className="w-4 h-4" />
              <span>{ingestMsg}</span>
            </div>
          )}

          <form onSubmit={handleIngestSubmit} className="audit-form">
            <div className="form-grid-2">
              <div className="form-group">
                <label>Instagram Post ID / Shortcode</label>
                <input
                  type="text"
                  required
                  value={postId}
                  onChange={(e) => setPostId(e.target.value)}
                  placeholder="e.g. ig_post_4021"
                />
              </div>
              <div className="form-group">
                <label>Default Creator / Brand Handle</label>
                <input
                  type="text"
                  value={authorHandle}
                  onChange={(e) => setAuthorHandle(e.target.value)}
                  placeholder="e.g. @brandname"
                />
              </div>
            </div>

            <div className="form-group">
              <label>
                Comments to Analyze (One comment per line, or <code>@username: comment text</code>)
              </label>
              <textarea
                rows="5"
                required
                value={rawComments}
                onChange={(e) => setRawComments(e.target.value)}
                placeholder="@customer1: Loved this product so much!\n@buyer2: Bhai bilkul bekaar service hai, paisa barbaad!"
              />
            </div>

            <button type="submit" disabled={ingesting} className="btn-primary">
              <Sparkles className="w-4 h-4 mr-1.5" />
              {ingesting ? 'Analyzing Sentiment & Crisis Triggers...' : 'Analyze & Store Mentions'}
            </button>
          </form>
        </div>
      )}

      <AutomatedIngestion />

      {/* KPI Cards Grid */}
      <div className="sentiment-kpi-grid">
        <div className="stat-card">
          <span className="stat-val">{summary?.total_mentions || 0}</span>
          <span className="stat-lbl flex items-center gap-1">
            <MessageSquare className="w-3.5 h-3.5 text-blue-400" /> Total Mentions
          </span>
        </div>

        <div className="stat-card stat-success">
          <span className="stat-val">{summary?.positive_rate || 0}%</span>
          <span className="stat-lbl flex items-center gap-1">
            <Smile className="w-3.5 h-3.5 text-emerald-400" /> Positive ({summary?.positive_count || 0})
          </span>
        </div>

        <div className="stat-card stat-error">
          <span className="stat-val">{summary?.negative_rate || 0}%</span>
          <span className="stat-lbl flex items-center gap-1">
            <Frown className="w-3.5 h-3.5 text-red-400" /> Negative ({summary?.negative_count || 0})
          </span>
        </div>

        <div className="stat-card" style={{ borderColor: 'rgba(139, 92, 246, 0.3)' }}>
          <span className="stat-val" style={{ color: '#c4b5fd' }}>{summary?.needs_review_count || 0}</span>
          <span className="stat-lbl flex items-center gap-1">
            <HelpCircle className="w-3.5 h-3.5 text-purple-400" /> Needs Manual Read
          </span>
        </div>

        <div className="stat-card stat-warning">
          <span className="stat-val">{summary?.flagged_count || 0}</span>
          <span className="stat-lbl flex items-center gap-1">
            <AlertTriangle className="w-3.5 h-3.5 text-amber-400" /> Flagged for Review
          </span>
        </div>
      </div>

      {/* Daily Volume & Sentiment Breakdown */}
      {summary?.daily_trend && summary.daily_trend.length > 0 && (
        <div className="card" style={{ marginBottom: '1.5rem' }}>
          <div className="card-header" style={{ marginBottom: '1rem', paddingBottom: '0.75rem' }}>
            <div className="flex items-center gap-2">
              <Calendar className="w-4 h-4 text-emerald-400" />
              <h4>Daily Sentiment & Spike Tracking (Last {summary.daily_trend.length} Recorded Days)</h4>
            </div>
          </div>
          <div className="trend-table-wrapper">
            <table className="account-posts-table">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Positive</th>
                  <th>Neutral</th>
                  <th>Negative</th>
                  <th>Needs Review</th>
                  <th>Flagged Spike Alerts</th>
                </tr>
              </thead>
              <tbody>
                {summary.daily_trend.map((day) => (
                  <tr key={day.date}>
                    <td className="font-mono text-xs">{day.date}</td>
                    <td><span className="text-emerald-400 font-semibold">{day.positive}</span></td>
                    <td><span className="text-secondary">{day.neutral}</span></td>
                    <td>
                      <span className={day.negative >= 3 ? 'text-red-400 font-bold' : 'text-secondary'}>
                        {day.negative}
                      </span>
                    </td>
                    <td>
                      <span className={day.needs_review > 0 ? 'text-purple-400 font-semibold' : 'text-secondary'}>
                        {day.needs_review || 0}
                      </span>
                    </td>
                    <td>
                      {day.flagged > 0 ? (
                        <span className="status-pill pill-flagged">
                          {day.flagged} FLAGGED
                        </span>
                      ) : (
                        <span className="text-muted text-xs">Clean</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Filter Tabs */}
      <div className="mentions-feed-section">
        <div className="feed-header">
          <div>
            <h3>Consumer Comments & Response Feed ({mentions.length})</h3>
            <div className="flex items-center gap-2 mt-2 pt-2 border-t border-white/5 flex-wrap">
              <span className="text-xs text-muted flex items-center gap-1 font-semibold">
                <Globe className="w-3.5 h-3.5 text-blue-400" /> Language:
              </span>
              <button
                className={`filter-pill ${!filterLanguage ? 'active' : ''}`}
                onClick={() => setFilterLanguage(null)}
              >
                All
              </button>
              <button
                className={`filter-pill ${filterLanguage === 'en' ? 'active' : ''}`}
                onClick={() => setFilterLanguage('en')}
              >
                English (EN)
              </button>
              <button
                className={`filter-pill ${filterLanguage === 'hinglish' ? 'active' : ''}`}
                onClick={() => setFilterLanguage('hinglish')}
              >
                Hinglish
              </button>
              <button
                className={`filter-pill ${filterLanguage === 'indic' ? 'active' : ''}`}
                onClick={() => setFilterLanguage('indic')}
              >
                Indic Scripts
              </button>
            </div>
          </div>

          <div className="filter-pill-group">
            <button
              className={`filter-pill ${!filterSentiment && !filterFlaggedOnly ? 'active' : ''}`}
              onClick={() => { setFilterSentiment(null); setFilterFlaggedOnly(false); }}
            >
              All Sentiments
            </button>
            <button
              className={`filter-pill pill-warning ${filterFlaggedOnly ? 'active' : ''}`}
              onClick={() => { setFilterSentiment(null); setFilterFlaggedOnly(true); }}
            >
              ⚠️ Flagged Only ({summary?.flagged_count || 0})
            </button>
            <button
              className={`filter-pill pill-review ${filterSentiment === 'needs_review' ? 'active' : ''}`}
              onClick={() => { setFilterSentiment('needs_review'); setFilterFlaggedOnly(false); }}
            >
              🟣 Needs Manual Read ({summary?.needs_review_count || 0})
            </button>
            <button
              className={`filter-pill pill-error ${filterSentiment === 'negative' ? 'active' : ''}`}
              onClick={() => { setFilterSentiment('negative'); setFilterFlaggedOnly(false); }}
            >
              Negative
            </button>
            <button
              className={`filter-pill ${filterSentiment === 'neutral' ? 'active' : ''}`}
              onClick={() => { setFilterSentiment('neutral'); setFilterFlaggedOnly(false); }}
            >
              Neutral
            </button>
            <button
              className={`filter-pill pill-success ${filterSentiment === 'positive' ? 'active' : ''}`}
              onClick={() => { setFilterSentiment('positive'); setFilterFlaggedOnly(false); }}
            >
              Positive
            </button>
          </div>
        </div>

        {/* Mentions List with Phase 2.2 Response Drafting */}
        <div className="mentions-list">
          {loading && mentions.length === 0 ? (
            <div className="card empty-state">Loading mentions feed...</div>
          ) : mentions.length === 0 ? (
            <div className="card empty-state">
              No mentions found for the selected filter. Ingest comments above to begin monitoring!
            </div>
          ) : (
            mentions.map((m) => (
              <div key={m.id} className={`mention-card ${m.flagged_for_review ? 'mention-flagged' : ''}`}>
                <div className="mention-card-top">
                  <div className="flex items-center gap-2">
                    <span className="mention-author">{m.author_handle}</span>
                    <span className={`badge-lang badge-lang-${m.language || 'en'}`}>
                      {m.language === 'indic' ? 'Indic Script' : m.language === 'hinglish' ? 'Hinglish' : 'EN'}
                    </span>
                    <span className="badge-platform">
                      <Camera className="w-3 h-3 mr-1" /> {m.platform}
                    </span>
                    <span className="text-muted text-xs font-mono">Post: {m.post_id}</span>
                  </div>

                  <div className="flex items-center gap-2">
                    {m.sentiment === 'needs_review' ? (
                      <span className="status-pill pill-needs_review">
                        <HelpCircle className="w-3 h-3 inline mr-1" />
                        NEEDS MANUAL READ
                      </span>
                    ) : (
                      <span className={`status-pill pill-${m.sentiment}`}>
                        {m.sentiment === 'positive' && <Smile className="w-3 h-3 inline mr-1" />}
                        {m.sentiment === 'negative' && <Frown className="w-3 h-3 inline mr-1" />}
                        {m.sentiment === 'neutral' && <Meh className="w-3 h-3 inline mr-1" />}
                        {m.sentiment.toUpperCase()} ({m.sentiment_score > 0 ? `+${m.sentiment_score}` : m.sentiment_score})
                      </span>
                    )}

                    {m.flagged_for_review && (
                      <span className="status-pill pill-flagged">
                        NEEDS HUMAN REVIEW
                      </span>
                    )}
                  </div>
                </div>

                <p className="mention-text">{m.text}</p>

                {m.explanation && (
                  <div className="mention-explanation">
                    <AlertTriangle className="w-3.5 h-3.5 text-amber-400 flex-shrink-0 mt-0.5" />
                    <span>{m.explanation}</span>
                  </div>
                )}

                {/* --- Phase 2.2: Response-Drafting Agent Section --- */}
                {m.drafted_reply ? (
                  <div className="draft-reply-container">
                    <div className="draft-reply-header">
                      <div className="flex items-center gap-1.5">
                        <Sparkles className="w-4 h-4 text-emerald-400" />
                        <span className="font-semibold text-white text-sm">Suggested Brand Response Draft</span>
                      </div>

                      {m.approved_at ? (
                        <span className="badge-approved">
                          <ShieldCheck className="w-3.5 h-3.5 mr-1" /> APPROVED BY REVIEWER
                        </span>
                      ) : (
                        <span className="badge-pending-review">
                          ⏳ PENDING HUMAN SIGN-OFF
                        </span>
                      )}
                    </div>

                    {/* Editable Response Text Area */}
                    <textarea
                      rows="3"
                      className="draft-reply-textarea"
                      value={editedReplies[m.id] !== undefined ? editedReplies[m.id] : m.drafted_reply}
                      onChange={(e) => setEditedReplies({ ...editedReplies, [m.id]: e.target.value })}
                      placeholder="Suggested reply text..."
                      disabled={Boolean(m.approved_at)}
                    />

                    {/* Strategy Explanation */}
                    {m.draft_explanation && (
                      <div className="draft-strategy-box">
                        <span className="strategy-title">💡 Strategic Rationale:</span>
                        <p>{m.draft_explanation}</p>
                      </div>
                    )}

                    {/* Action Buttons: Approve, Copy, Re-Draft */}
                    <div className="draft-actions-bar">
                      {!m.approved_at ? (
                        <button
                          className="btn-primary btn-sm"
                          onClick={() => handleApproveReply(m.id)}
                          disabled={approvingIds.has(m.id)}
                        >
                          <Check className="w-3.5 h-3.5 mr-1" />
                          {approvingIds.has(m.id) ? 'Saving Approval...' : 'Approve Response'}
                        </button>
                      ) : (
                        <span className="text-emerald-400 text-xs font-semibold flex items-center gap-1">
                          <CheckCircle2 className="w-3.5 h-3.5" /> Approved at {new Date(m.approved_at).toLocaleTimeString()}
                        </span>
                      )}

                      <div className="flex gap-2">
                        <button
                          className="btn-secondary btn-sm"
                          onClick={() => handleCopyReply(m.id, editedReplies[m.id] || m.drafted_reply)}
                        >
                          {copiedId === m.id ? (
                            <>
                              <Check className="w-3.5 h-3.5 mr-1 text-emerald-400" /> Copied!
                            </>
                          ) : (
                            <>
                              <Copy className="w-3.5 h-3.5 mr-1" /> Copy Reply
                            </>
                          )}
                        </button>

                        {!m.approved_at && (
                          <button
                            className="btn-secondary btn-sm"
                            onClick={() => handleDraftReply(m.id)}
                            disabled={draftingIds.has(m.id)}
                          >
                            <RefreshCw className={`w-3.5 h-3.5 mr-1 ${draftingIds.has(m.id) ? 'animate-spin' : ''}`} />
                            Regenerate
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="draft-trigger-row">
                    <button
                      className="btn-draft-trigger"
                      onClick={() => handleDraftReply(m.id)}
                      disabled={draftingIds.has(m.id)}
                    >
                      <Sparkles className={`w-3.5 h-3.5 mr-1.5 ${draftingIds.has(m.id) ? 'animate-spin' : ''}`} />
                      {draftingIds.has(m.id) ? 'Drafting Brand Response...' : 'Draft Response with AI'}
                    </button>
                  </div>
                )}

                <div className="mention-card-bottom">
                  <span className="text-muted text-xs">
                    Detected: {new Date(m.detected_at).toLocaleString()}
                  </span>
                  <span className="text-secondary text-xs">
                    {m.approved_at ? 'Ready for public posting via official platform' : 'Human review required before publishing'}
                  </span>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
