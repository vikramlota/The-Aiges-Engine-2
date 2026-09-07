import React, { useState, useEffect } from 'react';
import { adAllocationApi } from '../api/client';
import {
  TrendingUp,
  PieChart,
  DollarSign,
  Sparkles,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  PlusCircle,
  ArrowRight,
  ShieldCheck,
  BarChart2,
  Percent,
  Layers,
  ArrowUpRight,
  ArrowDownRight
} from 'lucide-react';

const PILOT_PRESETS = {
  'D2C Festive Scaling': {
    name: 'D2C Festive Scaling Campaign',
    total_monthly_budget: 200000.0,
    channels: [
      {
        name: 'Instagram Reels',
        current_allocation_pct: 25.0,
        current_spend: 50000.0,
        impressions: 240000,
        clicks: 6000,
        conversions: 320,
        revenue: 185000.0,
      },
      {
        name: 'Meta Feed',
        current_allocation_pct: 40.0,
        current_spend: 80000.0,
        impressions: 320000,
        clicks: 4500,
        conversions: 110,
        revenue: 104000.0,
      },
      {
        name: 'YouTube Shorts',
        current_allocation_pct: 20.0,
        current_spend: 40000.0,
        impressions: 160000,
        clicks: 3200,
        conversions: 140,
        revenue: 98000.0,
      },
      {
        name: 'Google Search Ads',
        current_allocation_pct: 15.0,
        current_spend: 30000.0,
        impressions: 45000,
        clicks: 1800,
        conversions: 65,
        revenue: 62000.0,
      },
    ],
  },
  'Creative Fatigue Dilemma': {
    name: 'Q4 Product Launch Test',
    total_monthly_budget: 150000.0,
    channels: [
      {
        name: 'Instagram Reels',
        current_allocation_pct: 35.0,
        current_spend: 52500.0,
        impressions: 180000,
        clicks: 3600,
        conversions: 90,
        revenue: 72000.0,
      },
      {
        name: 'YouTube Shorts',
        current_allocation_pct: 35.0,
        current_spend: 52500.0,
        impressions: 190000,
        clicks: 4100,
        conversions: 195,
        revenue: 168000.0,
      },
      {
        name: 'Meta Feed',
        current_allocation_pct: 30.0,
        current_spend: 45000.0,
        impressions: 140000,
        clicks: 2100,
        conversions: 42,
        revenue: 41000.0,
      },
    ],
  },
};

export default function AdAllocationDashboard() {
  const [campaigns, setCampaigns] = useState([]);
  const [selectedCampaignId, setSelectedCampaignId] = useState(null);
  const [currentCampaign, setCurrentCampaign] = useState(null);
  const [recommendation, setRecommendation] = useState(null);

  const [loading, setLoading] = useState(true);
  const [optimizing, setOptimizing] = useState(false);
  const [approving, setApproving] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);

  // New campaign form state
  const [newCampaignName, setNewCampaignName] = useState('');
  const [newBudget, setNewBudget] = useState(100000);

  const loadCampaigns = async () => {
    setLoading(true);
    try {
      const data = await adAllocationApi.listCampaigns();
      setCampaigns(data);
      if (data.length > 0 && !selectedCampaignId) {
        setSelectedCampaignId(data[0].id);
      }
    } catch (err) {
      console.error('Failed to load campaigns', err);
    } finally {
      setLoading(false);
    }
  };

  const loadCampaignDetail = async (campId) => {
    if (!campId) return;
    try {
      const detail = await adAllocationApi.getCampaign(campId);
      setCurrentCampaign(detail);
      setRecommendation(null); // reset recommendation on campaign switch
    } catch (err) {
      console.error('Failed to load campaign detail', err);
    }
  };

  useEffect(() => {
    loadCampaigns();
  }, []);

  useEffect(() => {
    if (selectedCampaignId) {
      loadCampaignDetail(selectedCampaignId);
    }
  }, [selectedCampaignId]);

  const handleCreatePilot = async (presetKey) => {
    const preset = PILOT_PRESETS[presetKey];
    if (!preset) return;
    setLoading(true);
    try {
      const created = await adAllocationApi.createCampaign({
        name: preset.name,
        total_monthly_budget: preset.total_monthly_budget,
        currency: 'INR',
        channels: preset.channels,
      });
      await loadCampaigns();
      setSelectedCampaignId(created.id);
      setShowCreateModal(false);
    } catch (err) {
      alert(`Failed to create preset campaign: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleRunOptimizer = async () => {
    if (!selectedCampaignId) return;
    setOptimizing(true);
    try {
      const rec = await adAllocationApi.generateRecommendation(selectedCampaignId);
      setRecommendation(rec);
    } catch (err) {
      alert(`Optimization failed: ${err.message}`);
    } finally {
      setOptimizing(false);
    }
  };

  const handleApproveShift = async () => {
    if (!recommendation) return;
    setApproving(true);
    try {
      const approved = await adAllocationApi.approveRecommendation(recommendation.id);
      setRecommendation(approved);
      // Reload campaign to reflect updated allocation percentages
      await loadCampaignDetail(selectedCampaignId);
    } catch (err) {
      alert(`Approval failed: ${err.message}`);
    } finally {
      setApproving(false);
    }
  };

  // Compute summary stats for current campaign
  const channels = currentCampaign?.channels || [];
  const totalSpend = channels.reduce((acc, c) => acc + c.current_spend, 0);
  const totalRevenue = channels.reduce((acc, c) => acc + c.revenue, 0);
  const totalConversions = channels.reduce((acc, c) => acc + c.conversions, 0);
  const blendedRoas = totalSpend > 0 ? (totalRevenue / totalSpend).toFixed(2) : '0.00';

  return (
    <div className="ad-allocation-container">
      {/* Top Action & Campaign Bar */}
      <div className="sentiment-header-bar">
        <div>
          <h2>Ad-Allocation Agent (Thompson Sampling)</h2>
          <p>Multi-armed bandit budget optimization with strict human sign-off and zero black-box spend changes</p>
        </div>

        <div className="flex items-center gap-2">
          {campaigns.length > 0 && (
            <select
              className="campaign-select"
              value={selectedCampaignId || ''}
              onChange={(e) => setSelectedCampaignId(Number(e.target.value))}
            >
              {campaigns.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name} (₹{c.total_monthly_budget.toLocaleString()})
                </option>
              ))}
            </select>
          )}

          <button
            onClick={() => setShowCreateModal(!showCreateModal)}
            className="btn-primary"
            style={{ padding: '0.45rem 0.85rem', fontSize: '0.85rem' }}
          >
            <PlusCircle className="w-4 h-4 mr-1.5" />
            New Campaign / Presets
          </button>
        </div>
      </div>

      {/* Preset / Creation Drawer */}
      {showCreateModal && (
        <div className="card ingest-card">
          <div className="card-header">
            <div>
              <h3>Load a Sandbox Ad Campaign</h3>
              <p>Test the Thompson Sampling multi-armed bandit against real-world advertising scenarios</p>
            </div>
            <button onClick={() => setShowCreateModal(false)} className="btn-secondary btn-sm">
              Close
            </button>
          </div>

          <div className="pilot-preset-grid">
            {Object.keys(PILOT_PRESETS).map((key) => {
              const p = PILOT_PRESETS[key];
              return (
                <div key={key} className="pilot-preset-card">
                  <h4>{p.name}</h4>
                  <p className="text-secondary text-xs" style={{ marginBottom: '0.5rem' }}>
                    Monthly Budget: ₹{p.total_monthly_budget.toLocaleString()} • {p.channels.length} Channels
                  </p>
                  <ul className="text-xs text-gray-300" style={{ marginBottom: '0.75rem', paddingLeft: '1.2rem' }}>
                    {p.channels.map((ch) => (
                      <li key={ch.name}>
                        {ch.name}: ₹{ch.current_spend.toLocaleString()} spend → {ch.conversions} conv (
                        {(ch.revenue / ch.current_spend).toFixed(1)}x ROAS)
                      </li>
                    ))}
                  </ul>
                  <button onClick={() => handleCreatePilot(key)} className="btn-primary btn-sm">
                    Load & Optimize This Campaign
                  </button>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Empty State if no campaigns */}
      {campaigns.length === 0 && !loading && (
        <div className="card empty-state">
          <h3>No ad campaigns found</h3>
          <p>Load one of the sandbox pilot campaigns above to test the game-theory allocation optimizer!</p>
        </div>
      )}

      {/* Campaign KPI Cards */}
      {currentCampaign && (
        <>
          <div className="sentiment-kpi-grid">
            <div className="stat-card">
              <span className="stat-val">₹{currentCampaign.total_monthly_budget.toLocaleString()}</span>
              <span className="stat-lbl flex items-center gap-1">
                <DollarSign className="w-3.5 h-3.5 text-blue-400" /> Total Campaign Budget
              </span>
            </div>

            <div className="stat-card">
              <span className="stat-val">₹{totalSpend.toLocaleString()}</span>
              <span className="stat-lbl flex items-center gap-1">
                <Layers className="w-3.5 h-3.5 text-purple-400" /> Recorded Spend
              </span>
            </div>

            <div className="stat-card stat-success">
              <span className="stat-val">{blendedRoas}x</span>
              <span className="stat-lbl flex items-center gap-1">
                <TrendingUp className="w-3.5 h-3.5 text-emerald-400" /> Blended Campaign ROAS
              </span>
            </div>

            <div className="stat-card">
              <span className="stat-val">{totalConversions}</span>
              <span className="stat-lbl flex items-center gap-1">
                <BarChart2 className="w-3.5 h-3.5 text-amber-400" /> Total Conversions
              </span>
            </div>
          </div>

          {/* Current Channel Performance Table */}
          <div className="card" style={{ marginBottom: '1.5rem' }}>
            <div className="card-header">
              <div className="flex items-center gap-2">
                <PieChart className="w-4 h-4 text-emerald-400" />
                <h4>Active Channel Performance (Prior to Optimizer Shift)</h4>
              </div>

              <button
                onClick={handleRunOptimizer}
                disabled={optimizing || channels.length < 2}
                className="btn-primary"
                style={{ padding: '0.45rem 1rem', fontSize: '0.85rem' }}
              >
                <Sparkles className={`w-4 h-4 mr-1.5 ${optimizing ? 'animate-spin' : ''}`} />
                {optimizing ? 'Running Thompson Sampling...' : 'Run Bandit Optimizer'}
              </button>
            </div>

            <div className="account-posts-table-wrapper">
              <table className="account-posts-table">
                <thead>
                  <tr>
                    <th>Channel Name</th>
                    <th>Current Allocation</th>
                    <th>Spend</th>
                    <th>Conversions</th>
                    <th>Revenue</th>
                    <th>ROAS</th>
                  </tr>
                </thead>
                <tbody>
                  {channels.map((ch) => {
                    const roas = ch.current_spend > 0 ? (ch.revenue / ch.current_spend).toFixed(2) : '0.00';
                    return (
                      <tr key={ch.id}>
                        <td className="font-semibold text-white">{ch.name}</td>
                        <td>
                          <div className="flex items-center gap-2">
                            <div className="alloc-bar-bg">
                              <div
                                className="alloc-bar-fill"
                                style={{ width: `${Math.min(100, ch.current_allocation_pct)}%` }}
                              />
                            </div>
                            <span className="text-xs font-mono">{ch.current_allocation_pct}%</span>
                          </div>
                        </td>
                        <td>₹{ch.current_spend.toLocaleString()}</td>
                        <td>{ch.conversions}</td>
                        <td>₹{ch.revenue.toLocaleString()}</td>
                        <td>
                          <span
                            className={`status-pill ${
                              Number(roas) >= 2.5
                                ? 'pill-positive'
                                : Number(roas) >= 1.5
                                ? 'pill-neutral'
                                : 'pill-negative'
                            }`}
                          >
                            {roas}x ROAS
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          {/* Recommendation Workbench */}
          {recommendation && (
            <div className="card recommendation-workbench">
              <div className="recommendation-header">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="badge-advisory">💡 ADVISORY BUDGET SHIFT RECOMMENDATION</span>
                    {recommendation.status === 'APPROVED' ? (
                      <span className="badge-approved">
                        <ShieldCheck className="w-3.5 h-3.5 mr-1" /> APPROVED & APPLIED
                      </span>
                    ) : (
                      <span className="badge-pending-review">
                        ⏳ REQUIRES HUMAN SIGN-OFF
                      </span>
                    )}
                  </div>
                  <h3 style={{ marginTop: '0.4rem', color: '#fff' }}>
                    Thompson Sampling Marginal ROI Allocation
                  </h3>
                </div>

                <div className="confidence-pill">
                  <span>Confidence:</span>
                  <strong>{Math.round(recommendation.confidence * 100)}%</strong>
                </div>
              </div>

              {/* Shift Breakdown Grid */}
              <div className="shift-cards-grid">
                {recommendation.shifts.map((s) => {
                  const isPositive = s.delta_pct > 0;
                  return (
                    <div key={s.channel_name} className={`shift-card ${isPositive ? 'shift-positive' : 'shift-negative'}`}>
                      <div className="shift-card-top">
                        <span className="shift-channel-name">{s.channel_name}</span>
                        <span className={`shift-delta ${isPositive ? 'text-emerald-400' : 'text-red-400'}`}>
                          {isPositive ? <ArrowUpRight className="w-4 h-4 inline" /> : <ArrowDownRight className="w-4 h-4 inline" />}
                          {isPositive ? `+${s.delta_pct}%` : `${s.delta_pct}%`}
                        </span>
                      </div>

                      <div className="shift-alloc-flow">
                        <span className="font-mono text-xs">{s.current_pct}%</span>
                        <ArrowRight className="w-3.5 h-3.5 text-secondary" />
                        <span className="font-mono text-sm font-bold text-white">{s.suggested_pct}%</span>
                      </div>

                      <div className="shift-card-metrics">
                        <div>
                          <span className="text-secondary text-xs block">Target Spend</span>
                          <span className="text-white font-semibold text-xs">₹{s.suggested_spend.toLocaleString()}</span>
                        </div>
                        <div>
                          <span className="text-secondary text-xs block">Win Prob.</span>
                          <span className="text-emerald-400 font-semibold text-xs">{s.win_probability}%</span>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Statistical Rationale */}
              <div className="draft-strategy-box" style={{ marginTop: '1rem', borderLeftColor: '#10b981' }}>
                <span className="strategy-title" style={{ color: '#6ee7b7' }}>
                  📊 Statistical Rationale (Exploration vs Exploitation):
                </span>
                <p>{recommendation.reasoning}</p>
              </div>

              {/* Approval Footer */}
              <div className="draft-actions-bar" style={{ marginTop: '1rem' }}>
                {recommendation.status !== 'APPROVED' ? (
                  <button onClick={handleApproveShift} disabled={approving} className="btn-primary">
                    <CheckCircle2 className="w-4 h-4 mr-1.5" />
                    {approving ? 'Applying Budget Shift...' : 'Approve Budget Shift'}
                  </button>
                ) : (
                  <div className="flex items-center gap-1.5 text-emerald-400 font-semibold text-sm">
                    <CheckCircle2 className="w-4 h-4" />
                    Approved and applied to campaign channels at{' '}
                    {new Date(recommendation.approved_at).toLocaleTimeString()}
                  </div>
                )}

                <span className="text-muted text-xs">
                  Hard Rule: Real ad platform budgets are never automatically modified.
                </span>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
