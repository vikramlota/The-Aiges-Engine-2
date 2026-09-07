import React, { useState, useEffect } from 'react';
import { metaApi, auditApi } from '../api/client';
import { Send, Sparkles, AlertCircle, HelpCircle, ChevronDown, ChevronUp } from 'lucide-react';

const PRESETS = {
  '-- Choose an Example Preset --': null,
  'Compliant Post': {
    caption: '#ad Loving this new serum from XYZ Skincare! My skin has never felt better.',
    platform: 'Instagram',
    content_type: 'static_post',
    material_connection: 'paid',
  },
  'Ambiguous Label (#collab)': {
    caption: 'Had so much fun trying this out! #style #ootd #fashion #india #reels #trending #collab',
    platform: 'Instagram',
    content_type: 'reel_story',
    material_connection: 'paid',
    story_label_superimposed: false,
  },
  'Unsubstantiated Health Claim': {
    caption: '#ad This herbal tea cures thyroid completely and clears skin in 3 days!',
    platform: 'Instagram',
    content_type: 'static_post',
    material_connection: 'paid',
    makes_health_finance_or_technical_claim: true,
    credentials_or_substantiation_shown: false,
  },
  'Prohibited Real Money Gaming': {
    caption: '#ad Download this gaming app and win real cash today, link in bio!',
    platform: 'Instagram',
    content_type: 'static_post',
    material_connection: 'paid',
    product_category: 'real_money_gaming',
  },
};

export default function AuditForm({ onAuditComplete }) {
  const [meta, setMeta] = useState(null);
  const [loadingMeta, setLoadingMeta] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [showAdvanced, setShowAdvanced] = useState(false);

  // Form State
  const [formData, setFormData] = useState({
    platform: 'Instagram',
    content_type: 'static_post',
    material_connection: 'paid',
    caption: '',
    influencer_handle: '',
    post_url: '',
    is_virtual_influencer: false,
    ai_disclosure_present_and_persistent: null,
    makes_health_finance_or_technical_claim: false,
    credentials_or_substantiation_shown: null,
    video_verbal_disclosure_second: null,
    video_overlay_covers_sponsored_segment: null,
    story_label_superimposed: null,
    ai_generated_or_enhanced: false,
    ai_content_label_present: null,
    names_specific_competitor: false,
    unqualified_superiority_claim: null,
    product_category: '',
    mandatory_disclaimer_present: null,
    content_categories: [],
  });

  // Fetch metadata on mount
  useEffect(() => {
    async function loadMeta() {
      try {
        const data = await metaApi.getMeta();
        setMeta(data);
        if (data.platforms?.length) setFormData((prev) => ({ ...prev, platform: data.platforms[0] }));
        if (data.content_types?.length) setFormData((prev) => ({ ...prev, content_type: data.content_types[0] }));
        if (data.material_connections?.length) setFormData((prev) => ({ ...prev, material_connection: data.material_connections[0].key }));
      } catch (err) {
        setError('Failed to load compliance metadata from server.');
      } finally {
        setLoadingMeta(false);
      }
    }
    loadMeta();
  }, []);

  const handleChange = (field, value) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const handlePresetSelect = (presetKey) => {
    const preset = PRESETS[presetKey];
    if (!preset) return;
    setFormData((prev) => ({
      ...prev,
      ...preset,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSubmitting(true);

    try {
      // Clean up optional fields before posting
      const payload = {
        ...formData,
        product_category: formData.product_category || null,
        video_verbal_disclosure_second:
          ['video', 'youtube_short', 'audio_podcast'].includes(formData.content_type) && formData.video_verbal_disclosure_second !== null && formData.video_verbal_disclosure_second !== ''
            ? Number(formData.video_verbal_disclosure_second)
            : null,
      };

      const result = await auditApi.createAudit(payload);
      onAuditComplete(result);
    } catch (err) {
      setError(err.message || 'Audit submission failed.');
    } finally {
      setSubmitting(false);
    }
  };

  const isVideoOrAudio = ['video', 'youtube_short', 'audio_podcast'].includes(formData.content_type);
  const isStoryOrReel = formData.content_type === 'reel_story';

  if (loadingMeta) {
    return <div className="card loading-placeholder">Loading compliance rules & metadata...</div>;
  }

  return (
    <div className="card">
      <div className="card-header">
        <div>
          <h2>New Compliance Audit</h2>
          <p>Inspect post caption and metadata against statutory ASCI & CCPA guidelines</p>
        </div>
        <div className="preset-selector">
          <select onChange={(e) => handlePresetSelect(e.target.value)} defaultValue="">
            {Object.keys(PRESETS).map((key) => (
              <option key={key} value={key}>
                {key}
              </option>
            ))}
          </select>
        </div>
      </div>

      {error && (
        <div className="alert-box error">
          <AlertCircle className="w-4 h-4" />
          <span>{error}</span>
        </div>
      )}

      <form onSubmit={handleSubmit} className="audit-form">
        {/* Caption */}
        <div className="form-group">
          <label htmlFor="caption">
            Post Caption / Description <span className="text-red-400">*</span>
          </label>
          <textarea
            id="caption"
            rows="4"
            required
            placeholder="Paste caption text, including all hashtags (e.g., #ad, #sponsored, #collab)..."
            value={formData.caption}
            onChange={(e) => handleChange('caption', e.target.value)}
          />
        </div>

        {/* Primary Meta Selectors */}
        <div className="form-grid-3">
          <div className="form-group">
            <label htmlFor="platform">Platform</label>
            <select
              id="platform"
              value={formData.platform}
              onChange={(e) => handleChange('platform', e.target.value)}
            >
              {meta?.platforms.map((p) => (
                <option key={p} value={p}>
                  {p}
                </option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="content_type">Content Type</label>
            <select
              id="content_type"
              value={formData.content_type}
              onChange={(e) => handleChange('content_type', e.target.value)}
            >
              {meta?.content_types.map((ct) => (
                <option key={ct} value={ct}>
                  {ct.replace('_', ' ').toUpperCase()}
                </option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="material_connection">Material Connection</label>
            <select
              id="material_connection"
              value={formData.material_connection}
              onChange={(e) => handleChange('material_connection', e.target.value)}
            >
              {meta?.material_connections.map((mc) => (
                <option key={mc.key} value={mc.key} title={mc.label}>
                  {mc.key.toUpperCase()}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Conditional Media Checks */}
        {isVideoOrAudio && (
          <div className="conditional-box">
            <h4>Video / Audio Specific Disclosures</h4>
            <div className="form-grid-2">
              <div className="form-group">
                <label>Verbal Disclosure Second (within first 10s)</label>
                <input
                  type="number"
                  placeholder="e.g. 3 (-1 if confirmed absent)"
                  value={formData.video_verbal_disclosure_second ?? ''}
                  onChange={(e) =>
                    handleChange('video_verbal_disclosure_second', e.target.value === '' ? null : e.target.value)
                  }
                />
              </div>

              <div className="form-group">
                <label>Overlay Covers Sponsored Segment?</label>
                <select
                  value={formData.video_overlay_covers_sponsored_segment === null ? '' : String(formData.video_overlay_covers_sponsored_segment)}
                  onChange={(e) =>
                    handleChange(
                      'video_overlay_covers_sponsored_segment',
                      e.target.value === '' ? null : e.target.value === 'true'
                    )
                  }
                >
                  <option value="">Pending / Not Reviewed</option>
                  <option value="true">Yes, overlay is persistent</option>
                  <option value="false">No, missing overlay</option>
                </select>
              </div>
            </div>
          </div>
        )}

        {isStoryOrReel && (
          <div className="conditional-box">
            <h4>Story / Reel Overlay</h4>
            <div className="form-group">
              <label>Is disclosure label superimposed directly on media?</label>
              <select
                value={formData.story_label_superimposed === null ? '' : String(formData.story_label_superimposed)}
                onChange={(e) =>
                  handleChange('story_label_superimposed', e.target.value === '' ? null : e.target.value === 'true')
                }
              >
                <option value="">Pending / Not Reviewed</option>
                <option value="true">Yes, superimposed on video/image</option>
                <option value="false">No, not superimposed</option>
              </select>
            </div>
          </div>
        )}

        {/* Toggle Advanced Compliance Checks */}
        <div className="advanced-toggle" onClick={() => setShowAdvanced(!showAdvanced)}>
          <span>Specific Claims & Special Categories</span>
          {showAdvanced ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </div>

        {showAdvanced && (
          <div className="advanced-section">
            <div className="checkbox-row">
              <input
                type="checkbox"
                id="is_virtual_influencer"
                checked={formData.is_virtual_influencer}
                onChange={(e) => handleChange('is_virtual_influencer', e.target.checked)}
              />
              <label htmlFor="is_virtual_influencer">Virtual / CGI Influencer Persona</label>
            </div>
            {formData.is_virtual_influencer && (
              <div className="nested-field">
                <label>AI Disclosure Present & Persistent?</label>
                <select
                  value={formData.ai_disclosure_present_and_persistent === null ? '' : String(formData.ai_disclosure_present_and_persistent)}
                  onChange={(e) =>
                    handleChange('ai_disclosure_present_and_persistent', e.target.value === '' ? null : e.target.value === 'true')
                  }
                >
                  <option value="">Pending Review</option>
                  <option value="true">Yes</option>
                  <option value="false">No (Flag)</option>
                </select>
              </div>
            )}

            <div className="checkbox-row">
              <input
                type="checkbox"
                id="makes_health_claim"
                checked={formData.makes_health_finance_or_technical_claim}
                onChange={(e) => handleChange('makes_health_finance_or_technical_claim', e.target.checked)}
              />
              <label htmlFor="makes_health_claim">Makes Health, Finance, or Technical Claims</label>
            </div>
            {formData.makes_health_finance_or_technical_claim && (
              <div className="nested-field">
                <label>Credentials or Substantiation Disclosed?</label>
                <select
                  value={formData.credentials_or_substantiation_shown === null ? '' : String(formData.credentials_or_substantiation_shown)}
                  onChange={(e) =>
                    handleChange('credentials_or_substantiation_shown', e.target.value === '' ? null : e.target.value === 'true')
                  }
                >
                  <option value="">Pending Review</option>
                  <option value="true">Yes, verified credentials / clinical evidence shown</option>
                  <option value="false">No, unverified claim</option>
                </select>
              </div>
            )}

            <div className="checkbox-row">
              <input
                type="checkbox"
                id="names_competitor"
                checked={formData.names_specific_competitor}
                onChange={(e) => handleChange('names_specific_competitor', e.target.checked)}
              />
              <label htmlFor="names_competitor">Comparative Ad (Names Specific Competitor)</label>
            </div>
            {formData.names_specific_competitor && (
              <div className="nested-field">
                <label>Unqualified Superiority Claim?</label>
                <select
                  value={formData.unqualified_superiority_claim === null ? '' : String(formData.unqualified_superiority_claim)}
                  onChange={(e) =>
                    handleChange('unqualified_superiority_claim', e.target.value === '' ? null : e.target.value === 'true')
                  }
                >
                  <option value="">Pending Review</option>
                  <option value="true">Yes (Unsubstantiated superiority)</option>
                  <option value="false">No (Evidence substantiated)</option>
                </select>
              </div>
            )}

            <div className="form-group" style={{ marginTop: '0.75rem' }}>
              <label>Special Product Category</label>
              <select
                value={formData.product_category}
                onChange={(e) => handleChange('product_category', e.target.value)}
              >
                <option value="">None / General Consumer</option>
                <option value="real_money_gaming">Real Money Gaming (Online Gaming Act 2025/2026)</option>
                <option value="virtual_digital_asset">Virtual Digital Asset / Crypto (ASCI Guidelines)</option>
              </select>
            </div>
          </div>
        )}

        <button type="submit" disabled={submitting} className="btn-primary" style={{ marginTop: '1rem' }}>
          <Sparkles className="w-4 h-4 mr-2" />
          {submitting ? 'Auditing Post...' : 'Run Compliance Audit'}
        </button>
      </form>
    </div>
  );
}
