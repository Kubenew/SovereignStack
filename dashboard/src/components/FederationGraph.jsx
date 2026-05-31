import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';

const FederationGraph = () => {
  const [nodes, setNodes] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetch('/api/federation/mesh/peers')
      .then(res => res.json())
      .then(data => {
        const peers = data.sync_peers || [];
        setNodes(peers.map(p => ({
          id: p.peer_id,
          role: 'Peer Node',
          status: p.healthy ? 'Active' : 'Offline',
          jurisdiction: p.jurisdiction,
          lastSync: new Date(p.last_sync * 1000).toLocaleTimeString()
        })));
        if (peers.length === 0) {
          // If no peers are synced, show known ones as offline/pending
          const known = data.known_peers || [];
          setNodes(known.map(k => ({
            id: k,
            role: 'Configured Peer',
            status: 'Pending',
            jurisdiction: 'Unknown',
            lastSync: 'Never'
          })));
        }
      })
      .catch(err => {
        console.error("Federation API Error:", err);
        setError("Failed to load federation data. Ensure backend is running.");
      });
  }, []);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      <div className="glass-panel" style={{ padding: '24px' }}>
        <h4 style={{ color: 'var(--text-secondary)', marginBottom: '24px', fontWeight: 500 }}>Federation Network Map</h4>
        
        {error && <div style={{ color: 'var(--danger-color)', marginBottom: '16px' }}>{error}</div>}
        
        {nodes.length === 0 && !error && (
          <div style={{ color: 'var(--text-secondary)' }}>No federation peers connected.</div>
        )}
        
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '20px' }}>
          {nodes.map((node, i) => (
            <motion.div 
              key={node.id}
              className="glass-panel"
              style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '12px', background: 'rgba(255, 255, 255, 0.03)' }}
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: i * 0.1 }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontWeight: 600, fontSize: '1.1rem' }}>{node.id}</span>
                <span style={{ 
                  fontSize: '0.75rem', 
                  padding: '4px 8px', 
                  borderRadius: '12px', 
                  background: node.status === 'Active' ? 'rgba(16, 185, 129, 0.2)' : 'rgba(245, 158, 11, 0.2)',
                  color: node.status === 'Active' ? 'var(--success-color)' : 'var(--warning-color)'
                }}>
                  {node.status}
                </span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
                <span>{node.role}</span>
                <span>Jurisdiction: {node.jurisdiction}</span>
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                Last Sync: {node.lastSync}
              </div>
            </motion.div>
          ))}
        </div>
      </div>
      
      <div className="glass-panel" style={{ padding: '24px' }}>
        <h4 style={{ color: 'var(--text-secondary)', marginBottom: '16px', fontWeight: 500 }}>Sharded Weight Status (Secure Inference)</h4>
        <div style={{ height: '8px', width: '100%', background: 'var(--glass-bg)', borderRadius: '4px', overflow: 'hidden', display: 'flex' }}>
          <div style={{ width: '100%', background: 'var(--accent-color)' }}></div>
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '12px', fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
          <span>Local Node (100%)</span>
        </div>
      </div>
    </div>
  );
};

export default FederationGraph;
