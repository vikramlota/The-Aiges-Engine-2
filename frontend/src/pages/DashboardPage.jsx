import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { auditApi } from '../api/client';
import AuditForm from '../components/AuditForm';
import LinkAuditForm from '../components/LinkAuditForm';
import AccountAuditForm from '../components/AccountAuditForm';
import SentimentMonitor from '../components/SentimentMonitor';
import AdAllocationDashboard from '../components/AdAllocationDashboard';
import ResultDisplay from '../components/ResultDisplay';
import HistoryList from '../components/HistoryList';
import { Shield, LogOut, PlusCircle, PenTool, Link2, TrendingUp, BarChart3, CheckSquare, DollarSign } from 'lucide-react';

export default function DashboardPage() {
  const { user, logout } = useAuth();
  const [navSection, setNavSection] = useState('compliance'); // 'compliance' | 'sentiment'
  const [activeTab, setActiveTab] = useState('manual'); // 'manual' | 'link' | 'account'
  const [currentAudit, setCurrentAudit] = useState(null);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [historyRefreshKey, setHistoryRefreshKey] = useState(0);

  const handleAuditComplete = (result) => {
    setCurrentAudit(result);
    setHistoryRefreshKey((prev) => prev + 1);
  };

  const handleSelectAudit = async (auditId) => {
    setLoadingDetail(true);
    try {
      const detail = await auditApi.getAudit(auditId);
      setCurrentAudit(detail);
      setNavSection('compliance');
      window.scrollTo({ top: 0, behavior: 'smooth' });
    } catch (err) {
      console.error('Failed to load audit detail', err);
    } finally {
      setLoadingDetail(false);
    }
  };

  const handleNewAudit = () => {
    setCurrentAudit(null);
  };

  return (
    <div className="app-container">
      {/* Top Header */}
      <header className="top-nav">
        <div className="nav-brand">
          <Shield className="w-6 h-6 text-emerald-400" />
          <span className="brand-title">The Aiges Engine</span>
          <span className="brand-subtitle">Compliance & Reputation</span>
        </div>

        {/* Primary Phase Navigation */}
        <div className="nav-primary-tabs">
          <button
            className={`nav-tab-pill ${navSection === 'compliance' ? 'active' : ''}`}
            onClick={() => setNavSection('compliance')}
          >
            <CheckSquare className="w-4 h-4 mr-1.5" />
            Compliance Audits
          </button>

          <button
            className={`nav-tab-pill ${navSection === 'sentiment' ? 'active' : ''}`}
            onClick={() => { setNavSection('sentiment'); setCurrentAudit(null); }}
          >
            <BarChart3 className="w-4 h-4 mr-1.5 text-blue-400" />
            Sentiment & Reputation
          </button>

          <button
            className={`nav-tab-pill ${navSection === 'allocation' ? 'active' : ''}`}
            onClick={() => { setNavSection('allocation'); setCurrentAudit(null); }}
          >
            <DollarSign className="w-4 h-4 mr-1.5 text-purple-400" />
            Ad Budget Optimizer
          </button>
        </div>

        <div className="nav-user-actions">
          <div className="user-pill">
            <span className="user-email">{user?.email}</span>
          </div>
          <button onClick={logout} className="btn-logout" title="Sign out">
            <LogOut className="w-4 h-4 mr-1" />
            <span>Sign Out</span>
          </button>
        </div>
      </header>

      {/* Main Content Layout */}
      <main className="dashboard-content">
        {navSection === 'sentiment' ? (
          <SentimentMonitor />
        ) : navSection === 'allocation' ? (
          <AdAllocationDashboard />
        ) : (
          <div className="dashboard-grid">
            {/* Main Column: Form or Active Result */}
            <div className="main-column">
              {/* Mode Tab Switcher */}
              <div className="mode-tabs">
                <button
                  className={`tab-btn ${activeTab === 'manual' ? 'active' : ''}`}
                  onClick={() => { setActiveTab('manual'); setCurrentAudit(null); }}
                >
                  <PenTool className="w-4 h-4 mr-1.5" />
                  Single Post Manual Check
                </button>

                <button
                  className={`tab-btn ${activeTab === 'link' ? 'active' : ''}`}
                  onClick={() => { setActiveTab('link'); setCurrentAudit(null); }}
                >
                  <Link2 className="w-4 h-4 mr-1.5" />
                  Import Single Link
                </button>

                <button
                  className={`tab-btn ${activeTab === 'account' ? 'active' : ''}`}
                  onClick={() => { setActiveTab('account'); setCurrentAudit(null); }}
                >
                  <TrendingUp className="w-4 h-4 mr-1.5" />
                  Audit Account Videos / Posts
                </button>
              </div>

              {currentAudit ? (
                <div className="active-result-wrapper">
                  <div className="result-action-bar">
                    <button onClick={handleNewAudit} className="btn-secondary">
                      <PlusCircle className="w-4 h-4 mr-1" />
                      Audit Another Post
                    </button>
                  </div>
                  {loadingDetail ? (
                    <div className="card loading-placeholder">Fetching audit details...</div>
                  ) : (
                    <ResultDisplay audit={currentAudit} onSelectPastAudit={handleSelectAudit} />
                  )}
                </div>
              ) : (
                <>
                  {activeTab === 'manual' && <AuditForm onAuditComplete={handleAuditComplete} />}
                  {activeTab === 'link' && <LinkAuditForm onAuditComplete={handleAuditComplete} />}
                  {activeTab === 'account' && <AccountAuditForm />}
                </>
              )}
            </div>

            {/* Sidebar Column: History */}
            <div className="sidebar-column">
              <HistoryList
                key={historyRefreshKey}
                activeAuditId={currentAudit?.id}
                onSelectAudit={handleSelectAudit}
              />
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
