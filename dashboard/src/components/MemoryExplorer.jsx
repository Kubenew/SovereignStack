import React, { useState } from 'react';
import { Search } from 'lucide-react';
import { motion } from 'framer-motion';

const MemoryExplorer = () => {
  const [searchTerm, setSearchTerm] = useState('');
  
  const memoryLogs = [
    { id: '1', key: 'usr_ctx_901', type: 'Vector', action: 'Upsert', time: '2 mins ago', size: '2.4 MB' },
    { id: '2', key: 'agt_sys_prompt', type: 'KV Cache', action: 'Read', time: '5 mins ago', size: '14 KB' },
    { id: '3', key: 'federated_state_3', type: 'CRDT', action: 'Sync', time: '12 mins ago', size: '840 KB' },
    { id: '4', key: 'doc_emb_442', type: 'Vector', action: 'Upsert', time: '1 hr ago', size: '1.2 MB' },
    { id: '5', key: 'usr_pref_theme', type: 'KV Cache', action: 'Read', time: '2 hrs ago', size: '2 KB' },
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ position: 'relative', width: '320px' }}>
          <Search size={18} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-secondary)' }} />
          <input 
            type="text" 
            placeholder="Search memory entries..." 
            value={searchTerm}
            onChange={e => setSearchTerm(e.target.value)}
            style={{ 
              width: '100%', 
              padding: '10px 10px 10px 40px', 
              borderRadius: '8px', 
              border: '1px solid var(--glass-border)',
              background: 'var(--glass-bg)',
              color: 'var(--text-primary)',
              outline: 'none'
            }}
          />
        </div>
        <button className="btn-primary">Clear Cache</button>
      </div>

      <div className="glass-panel" style={{ overflow: 'hidden' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid var(--glass-border)' }}>
              <th style={{ padding: '16px 24px', color: 'var(--text-secondary)', fontWeight: 500, fontSize: '0.875rem' }}>Key</th>
              <th style={{ padding: '16px 24px', color: 'var(--text-secondary)', fontWeight: 500, fontSize: '0.875rem' }}>Type</th>
              <th style={{ padding: '16px 24px', color: 'var(--text-secondary)', fontWeight: 500, fontSize: '0.875rem' }}>Action</th>
              <th style={{ padding: '16px 24px', color: 'var(--text-secondary)', fontWeight: 500, fontSize: '0.875rem' }}>Size</th>
              <th style={{ padding: '16px 24px', color: 'var(--text-secondary)', fontWeight: 500, fontSize: '0.875rem' }}>Time</th>
            </tr>
          </thead>
          <tbody>
            {memoryLogs.map((log, index) => (
              <motion.tr 
                key={log.id} 
                style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.04)' }}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.05 }}
              >
                <td style={{ padding: '16px 24px', fontWeight: 500 }}>{log.key}</td>
                <td style={{ padding: '16px 24px' }}>
                  <span style={{ 
                    padding: '4px 8px', borderRadius: '4px', fontSize: '0.75rem',
                    background: log.type === 'Vector' ? 'rgba(99, 102, 241, 0.2)' : 'rgba(16, 185, 129, 0.2)',
                    color: log.type === 'Vector' ? '#a5b4fc' : '#6ee7b7'
                  }}>
                    {log.type}
                  </span>
                </td>
                <td style={{ padding: '16px 24px', color: 'var(--text-secondary)' }}>{log.action}</td>
                <td style={{ padding: '16px 24px', color: 'var(--text-secondary)' }}>{log.size}</td>
                <td style={{ padding: '16px 24px', color: 'var(--text-secondary)' }}>{log.time}</td>
              </motion.tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default MemoryExplorer;
