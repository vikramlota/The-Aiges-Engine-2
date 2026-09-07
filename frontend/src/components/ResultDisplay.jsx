import React from 'react';
import { CheckCircle2, AlertTriangle, AlertOctagon, HelpCircle, FileText, Share2, History, ExternalLink, Camera, Sparkles } from 'lucide-react';

const STATUS_CONFIG = {
  COMPLIANT: {
    bg: 'status-compliant-bg',
    badge: 'status-compliant-badge',
    icon: CheckCircle2,
    title: 'COMPLIANT POST',
  },
  FLAGGED: {
    bg: 'status-flagged-bg',
    badge: 'status-flagged-badge',
    icon: AlertOctagon,
    title: 'COMPLIANCE VIOLATIONS FLAGGED',
  },
  'NEEDS EXPERT REVIEW': {
    bg: 'status-review-bg',
    badge: 'status-review-badge',
    icon: AlertTriangle,
    title: 'NEEDS EXPERT REVIEW',
  },
  'PENDING REVIEW': {
    bg: 'status-pending-bg',
    badge: 'status-pending-badge',
    icon: HelpCircle,
    title: 'PENDING REVIEW',
  },
};

const RISK_BADGES = {
  CRITICAL: 'risk-critical',
  HIGH: 'risk-high',
  MEDIUM: 'risk-medium',
  LOW: 'risk-low',
  ADVISORY: 'risk-advisory',
};

export default function ResultDisplay({ audit, onSelectPastAudit }) {
  if (!audit) return null;

  const statusInfo = STATUS_CONFIG[audit.status] || STATUS_CONFIG['PENDING REVIEW'];
  const StatusIcon = statusInfo.icon;
  const riskClass = audit.risk_level ? RISK_BADGES[audit.risk_level] || 'risk-advisory' : 'risk-advisory';

  const violations = audit.violations || audit.caption_flags || [];

  return (
    <div className="card result-card">
      {/* Top Banner */}
      <div className={`status-banner ${statusInfo.bg}`}>
        <div className="status-banner-left">
          <StatusIcon className="w-7 h-7" />
          <div>
            <h3>{statusInfo.title}</h3>
            <span className="audit-id">
              {audit.id ? `Audit ID #${audit.id}` : 'Link Inspection'}
              {audit.created_at && ` • ${new Date(audit.created_at).toLocaleDateString()}`}
            </span>
          </div>
        </div>

        {audit.risk_level && (
          <div className="status-banner-right">
            <span className={`risk-badge ${riskClass}`}>
              RISK: {audit.risk_level}
            </span>
          </div>
        )}
      </div>

      {/* Imported Post Header Metadata */}
      {(audit.influencer_handle || audit.post_url) && (
        <div className="result-section" style={{ background: 'rgba(15, 23, 42, 0.5)' }}>
          <div className="flex items-center justify-between">
            <div>
              {audit.influencer_handle && (
                <span className="font-semibold text-white mr-3">
                  Creator: <span className="text-emerald-400">{audit.influencer_handle}</span>
                </span>
              )}
              {audit.platform && (
                <span className="text-secondary text-sm">Platform: {audit.platform}</span>
              )}
            </div>
            {audit.post_url && (
              <a
                href={audit.post_url}
                target="_blank"
                rel="noopener noreferrer"
                className="btn-secondary"
                style={{ fontSize: '0.8rem', padding: '0.25rem 0.6rem' }}
              >
                View Post <ExternalLink className="w-3.5 h-3.5 ml-1 inline" />
              </a>
            )}
          </div>
        </div>
      )}

      {/* Visual OCR Scan Results (when imported via link) */}
      {audit.visual_status && audit.visual_status !== 'NO_MEDIA' && (
        <div className="result-section">
          <div className="section-title-with-icon" style={{ marginBottom: '0.5rem' }}>
            <Camera className="w-4 h-4 text-emerald-400" />
            <h4>Visual OCR Media Scan</h4>
          </div>
          <div className="caption-box" style={{ borderColor: audit.visual_status === 'DISCLOSURE_VISIBLE' ? 'var(--accent-emerald-border)' : 'var(--border-color)' }}>
            {audit.visual_status === 'DISCLOSURE_VISIBLE' && (
              <div className="text-emerald-400 font-semibold">
                ✅ Superimposed disclosure label detected in image: {audit.visual_flags?.join(', ')}
              </div>
            )}
            {audit.visual_status === 'TEXT_NO_DISCLOSURE' && (
              <div className="text-amber-400">
                🔍 Text was detected in the frame/image, but no approved disclosure label (#ad, #sponsored) was found.
              </div>
            )}
            {audit.visual_status === 'NO_TEXT_DETECTED' && (
              <div className="text-secondary">
                ℹ️ No text detected in visual media scan.
              </div>
            )}
            {audit.visual_status === 'OCR_NOT_INSTALLED' && (
              <div className="text-amber-300">
                ⚠️ Tesseract OCR is not installed or configured in this environment.
              </div>
            )}
          </div>
        </div>
      )}

      {/* Caption Preview */}
      <div className="result-section">
        <h4>Audited Caption</h4>
        <div className="caption-box">
          {audit.caption || <em>(No caption text provided)</em>}
        </div>
      </div>

      {/* Violations List */}
      {violations.length > 0 && (
        <div className="result-section">
          <h4>Detected Violations ({violations.length})</h4>
          <div className="violations-grid">
            {violations.map((vKey) => (
              <div key={vKey} className="violation-item">
                <div className="violation-header">
                  <AlertOctagon className="w-4 h-4 text-red-400" />
                  <span className="violation-title">{vKey.replace('_', ' ').toUpperCase()}</span>
                </div>
                <p className="violation-desc">
                  {audit.explanations?.[vKey] || `Violates statutory compliance standard for '${vKey}'.`}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Expert Review Items */}
      {audit.expert_review && audit.expert_review.length > 0 && (
        <div className="result-section">
          <h4>Items Needing Expert Review ({audit.expert_review.length})</h4>
          <div className="expert-grid">
            {audit.expert_review.map((item) => (
              <div key={item} className="expert-item">
                <AlertTriangle className="w-4 h-4 text-amber-400" />
                <span>{item.replace(/_/g, ' ').toUpperCase()}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* AI Auditor Intelligence Layer */}
      {audit.ai_status && (
        <div className="result-section" style={{ background: 'rgba(16, 185, 129, 0.05)' }}>
          <div className="section-title-with-icon" style={{ marginBottom: '0.75rem' }}>
            <Sparkles className="w-4 h-4 text-emerald-400" />
            <h4>AI Auditor Analysis ({audit.ai_status})</h4>
          </div>

          {audit.ai_claims && audit.ai_claims.length > 0 && (
            <div className="alert-box error" style={{ marginBottom: '0.75rem' }}>
              <AlertTriangle className="w-4 h-4" />
              <span><strong>Extracted Claims:</strong> {audit.ai_claims.join(', ')}</span>
            </div>
          )}

          {audit.ai_explanation && (
            <div style={{ marginBottom: '0.75rem' }}>
              <span className="text-secondary text-xs uppercase font-bold tracking-wider">Reviewer Explanation</span>
              <p className="text-sm text-gray-200 mt-1">{audit.ai_explanation}</p>
            </div>
          )}

          {audit.ai_recommended_fix && (
            <div className="alert-box" style={{ background: 'rgba(16, 185, 129, 0.15)', border: '1px solid var(--accent-emerald-border)', color: '#a7f3d0' }}>
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              <span><strong>Recommended Fix:</strong> {audit.ai_recommended_fix}</span>
            </div>
          )}
        </div>
      )}

      {/* Detailed Plain-Language Summary */}
      {audit.summary && (
        <div className="result-section">
          <h4>Full Auditor Summary</h4>
          <pre className="summary-pre">{audit.summary}</pre>
        </div>
      )}

      {/* Similar Past Audits (ChromaDB + HashingVectorizer) */}
      {audit.similar_past_audits && audit.similar_past_audits.length > 0 && (
        <div className="result-section similar-audits-section">
          <div className="section-title-with-icon">
            <History className="w-4 h-4 text-emerald-400" />
            <h4>Similar Past Audits (Vector Database Match)</h4>
          </div>
          <p className="section-subtitle">
            Retrieved via ChromaDB vector index based on caption cosine similarity:
          </p>

          <div className="similar-cards-grid">
            {audit.similar_past_audits.map((item) => (
              <div
                key={item.id}
                className="similar-card"
                onClick={() => onSelectPastAudit && onSelectPastAudit(item.id)}
              >
                <div className="similar-card-top">
                  <span className="similar-id">Audit #{item.id}</span>
                  <span className="similarity-badge">
                    {Math.round(item.similarity * 100)}% match
                  </span>
                </div>
                <p className="similar-caption">{item.caption}</p>
                <div className="similar-card-bottom">
                  <span className={`status-pill pill-${item.status.toLowerCase().replace(/\s+/g, '-')}`}>
                    {item.status}
                  </span>
                  {item.risk_level && (
                    <span className="risk-text">Risk: {item.risk_level}</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
