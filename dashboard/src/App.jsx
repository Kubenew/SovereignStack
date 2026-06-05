import React, { useEffect, useState } from 'react';
import { LayoutDashboard, Network, Database, Settings, ShieldCheck, Activity } from 'lucide-react';
import StatCard from './components/StatCard';
import FederationGraph from './components/FederationGraph';
import MemoryExplorer from './components/MemoryExplorer';
import './index.css';

function App() {
  const [activeTab, setActiveTab] = useState('overview');
  const [sysHealth, setSysHealth] = useState({ healthy: false, nodes: 0, vectors: 0 });
  const [events, setEvents] = useState([]);

  useEffect(() => {
    // Fetch Federation Health & Peers
    fetch('/api/federation/mesh/peers')
      .then(res => res.json())
      .then(data => {
        setSysHealth(prev => ({ ...prev, nodes: data.active_peers?.length || 0, healthy: true }));
      }).catch(err => console.error("Federation API Error:", err));

    // Fetch Memory Health
    fetch('/api/memory/health')
      .then(res => res.json())
      .then(data => {
        setSysHealth(prev => ({ ...prev, vectors: data.vector_count || 0 }));
      }).catch(err => console.error("Memory API Error:", err));

    // Fetch recent events
    fetch('/api/memory/events?limit=4')
      .then(res => res.json())
      .then(data => {
        if (data.events) setEvents(data.events);
      }).catch(err => console.error("Events API Error:", err));
  }, []);

  return (
    <div className="app-container">
      {/* Sidebar */}
      <aside className="sidebar glass-panel" style={{ borderRadius: '0 16px 16px 0', borderLeft: 'none' }}>
        <div style={{ padding: '0 0 40px 0', display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div style={{ 
            width: '36px', height: '36px', borderRadius: '10px', 
            background: 'linear-gradient(135deg, var(--accent-color), #4F46E5)',
            boxShadow: '0 4px 12px var(--accent-glow)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            color: 'white'
          }}>
            <ShieldCheck size={20} />
          </div>
          <h2 className="text-gradient" style={{ fontSize: '1.4rem', margin: 0, fontWeight: 700 }}>
            SovereignStack
          </h2>
        </div>

        <nav style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          <button 
            className={`nav-item ${activeTab === 'overview' ? 'active' : ''}`}
            onClick={() => setActiveTab('overview')}
          >
            <LayoutDashboard size={20} /> <span style={{ flex: 1 }}>Overview</span>
          </button>
          <button 
            className={`nav-item ${activeTab === 'federation' ? 'active' : ''}`}
            onClick={() => setActiveTab('federation')}
          >
            <Network size={20} /> <span style={{ flex: 1 }}>Federation Mesh</span>
          </button>
          <button 
            className={`nav-item ${activeTab === 'memory' ? 'active' : ''}`}
            onClick={() => setActiveTab('memory')}
          >
            <Database size={20} /> <span style={{ flex: 1 }}>Memory Vectors</span>
          </button>
        </nav>

        <div style={{ marginTop: 'auto' }}>
          <div className="glass-panel" style={{ padding: '16px', marginBottom: '16px', borderRadius: '12px', background: 'rgba(255,255,255,0.02)' }}>
            <h5 style={{ fontSize: '0.8rem', textTransform: 'uppercase', color: 'var(--text-secondary)', marginBottom: '12px', letterSpacing: '0.05em' }}>Node Status</h5>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <div className={`status-dot ${sysHealth.healthy ? 'healthy' : 'syncing'}`}></div>
              <span style={{ fontSize: '0.9rem', fontWeight: 500, color: sysHealth.healthy ? 'var(--text-primary)' : 'var(--warning-color)' }}>
                {sysHealth.healthy ? 'Active & Enforcing' : 'Synchronizing...'}
              </span>
            </div>
          </div>
          <button className="nav-item">
            <Settings size={20} /> <span>Settings</span>
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="main-content">
        <header className="topbar glass-panel" style={{ borderRadius: '0 0 16px 16px', borderTop: 'none', margin: '0 40px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <h3 style={{ margin: 0, fontWeight: 600, color: 'var(--text-primary)', fontSize: '1.25rem' }}>
              {activeTab === 'overview' && 'System Overview'}
              {activeTab === 'federation' && 'Federation Network'}
              {activeTab === 'memory' && 'Vector Memory Bank'}
            </h3>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
            <button className="btn-primary" style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '8px 16px', fontSize: '0.9rem' }}>
              <Activity size={16} /> Run Diagnostics
            </button>
          </div>
        </header>

        <div className="content-area animate-fade-in" style={{ padding: '40px' }}>
          {activeTab === 'overview' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
              
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '24px' }}>
                <StatCard title="Active Federation Peers" value={sysHealth.nodes.toString()} type="success" />
                <StatCard title="Memory Vectors" value={sysHealth.vectors.toString()} type="neutral" />
                <StatCard title="Compliance Mode" value="STRICT" type="success" trend="Active" />
                <StatCard title="System Alerts" value="0" type="neutral" trend="All clear" />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '24px' }}>
                <div className="glass-panel" style={{ padding: '32px', minHeight: '380px', display: 'flex', flexDirection: 'column' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
                    <h4 style={{ margin: 0, color: 'var(--text-primary)', fontSize: '1.1rem' }}>Inference Throughput</h4>
                    <span style={{ fontSize: '0.85rem', color: 'var(--success-color)', background: 'var(--success-glow)', padding: '4px 10px', borderRadius: '12px', fontWeight: 600 }}>Live</span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', flex: 1, background: 'rgba(255,255,255,0.02)', borderRadius: '12px', border: '1px dashed var(--glass-border)' }}>
                    <p style={{ color: 'var(--text-secondary)' }}>Throughput Chart Visualization Area</p>
                  </div>
                </div>

                <div className="glass-panel" style={{ padding: '32px', minHeight: '380px', display: 'flex', flexDirection: 'column' }}>
                  <h4 style={{ margin: '0 0 24px 0', color: 'var(--text-primary)', fontSize: '1.1rem' }}>Audit Ledger Events</h4>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', flex: 1 }}>
                    {events.length === 0 && (
                      <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-secondary)' }}>
                        No events logged.
                      </div>
                    )}
                    {events.map((ev, i) => (
                      <div key={i} style={{ 
                        padding: '16px', borderRadius: '12px', background: 'rgba(255,255,255,0.03)', 
                        borderLeft: '3px solid var(--accent-color)', display: 'flex', flexDirection: 'column', gap: '6px'
                      }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                          <span style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--accent-hover)' }}>
                            {ev.event_type.split('.').pop().toUpperCase()}
                          </span>
                          <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                            {new Date(ev.timestamp * 1000).toLocaleTimeString()}
                          </span>
                        </div>
                        <span style={{ fontSize: '0.9rem', color: 'var(--text-primary)' }}>
                          {ev.data?.doc_id || ev.event_id.substring(0, 12) + "..."}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}
          {activeTab === 'federation' && <FederationGraph />}
          {activeTab === 'memory' && <MemoryExplorer />}
        </div>
      </main>
    </div>
  );
}

export default App;
