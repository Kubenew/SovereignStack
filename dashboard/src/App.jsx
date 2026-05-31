import React, { useEffect, useState } from 'react';
import { LayoutDashboard, Network, Database, Settings } from 'lucide-react';
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
    fetch('/api/memory/events?limit=3')
      .then(res => res.json())
      .then(data => {
        if (data.events) setEvents(data.events);
      }).catch(err => console.error("Events API Error:", err));
  }, []);

  return (
    <div className="app-container">
      {/* Sidebar */}
      <aside className="sidebar glass-panel" style={{ borderTopRightRadius: 0, borderBottomRightRadius: 0, borderLeft: 0, borderTop: 0, borderBottom: 0 }}>
        <div style={{ padding: '0 0 32px 0', display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{ width: '32px', height: '32px', borderRadius: '8px', background: 'var(--accent-gradient, var(--accent-color))' }}></div>
          <h2 style={{ fontSize: '1.25rem', margin: 0 }}>SovereignStack</h2>
        </div>

        <nav style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <button 
            className={`nav-item ${activeTab === 'overview' ? 'active' : ''}`}
            onClick={() => setActiveTab('overview')}
            style={navItemStyle(activeTab === 'overview')}
          >
            <LayoutDashboard size={20} /> Overview
          </button>
          <button 
            className={`nav-item ${activeTab === 'federation' ? 'active' : ''}`}
            onClick={() => setActiveTab('federation')}
            style={navItemStyle(activeTab === 'federation')}
          >
            <Network size={20} /> Federation
          </button>
          <button 
            className={`nav-item ${activeTab === 'memory' ? 'active' : ''}`}
            onClick={() => setActiveTab('memory')}
            style={navItemStyle(activeTab === 'memory')}
          >
            <Database size={20} /> Memory Explorer
          </button>
        </nav>

        <div style={{ marginTop: 'auto' }}>
          <button style={navItemStyle(false)}>
            <Settings size={20} /> Settings
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="main-content">
        <header className="topbar glass-panel" style={{ borderRadius: 0, borderTop: 0, borderRight: 0, borderLeft: 0 }}>
          <h3 style={{ margin: 0, fontWeight: 500, color: 'var(--text-secondary)' }}>
            {activeTab.charAt(0).toUpperCase() + activeTab.slice(1)}
          </h3>
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ 
                width: '8px', height: '8px', borderRadius: '50%', 
                background: sysHealth.healthy ? 'var(--success-color)' : 'var(--danger-color)', 
                boxShadow: `0 0 8px ${sysHealth.healthy ? 'var(--success-color)' : 'var(--danger-color)'}` 
              }}></span>
              <span style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
                {sysHealth.healthy ? 'System Connected' : 'Connecting...'}
              </span>
            </div>
          </div>
        </header>

        <div className="content-area animate-fade-in">
          {activeTab === 'overview' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '24px' }}>
                <StatCard title="Active Peers" value={sysHealth.nodes.toString()} type="success" />
                <StatCard title="Memory Vectors" value={sysHealth.vectors.toString()} type="neutral" />
                <StatCard title="Federation Status" value={sysHealth.healthy ? 'Healthy' : 'Syncing'} type={sysHealth.healthy ? 'success' : 'warning'} />
                <StatCard title="Active Agents" value="--" type="neutral" />
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '24px' }}>
                <div className="glass-panel" style={{ padding: '24px', minHeight: '300px' }}>
                  <h4 style={{ marginBottom: '16px', color: 'var(--text-secondary)' }}>System Activity</h4>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '80%', color: 'var(--text-secondary)' }}>
                    Activity Chart Area
                  </div>
                </div>
                <div className="glass-panel" style={{ padding: '24px', minHeight: '300px' }}>
                  <h4 style={{ marginBottom: '16px', color: 'var(--text-secondary)' }}>Recent Events</h4>
                  <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: '12px' }}>
                    {events.length === 0 && <li style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>No recent events.</li>}
                    {events.map((ev, i) => (
                      <li key={i} style={{ fontSize: '0.875rem' }}>
                        <span style={{ color: 'var(--accent-color)' }}>[{ev.event_type.split('.').pop()}]</span> {ev.data?.doc_id || ev.event_id.substring(0, 8)}
                      </li>
                    ))}
                  </ul>
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

const navItemStyle = (isActive) => ({
  display: 'flex',
  alignItems: 'center',
  gap: '12px',
  padding: '12px 16px',
  borderRadius: '8px',
  border: 'none',
  background: isActive ? 'rgba(99, 102, 241, 0.15)' : 'transparent',
  color: isActive ? 'var(--text-primary)' : 'var(--text-secondary)',
  cursor: 'pointer',
  fontSize: '0.95rem',
  fontWeight: 500,
  transition: 'all 0.2s ease',
  textAlign: 'left',
  width: '100%',
});

export default App;
