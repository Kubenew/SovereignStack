import React from 'react';
import { motion } from 'framer-motion';

const StatCard = ({ title, value, trend, type = 'neutral' }) => {
  const getTrendColor = () => {
    if (type === 'success') return 'var(--success-color)';
    if (type === 'warning') return 'var(--warning-color)';
    if (type === 'danger') return 'var(--danger-color)';
    return 'var(--text-secondary)';
  };

  return (
    <motion.div 
      className="glass-panel"
      style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '12px' }}
      whileHover={{ y: -5, boxShadow: '0 12px 40px 0 rgba(0, 0, 0, 0.45)' }}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      <h4 style={{ margin: 0, color: 'var(--text-secondary)', fontSize: '0.875rem', fontWeight: 500 }}>
        {title}
      </h4>
      <div style={{ display: 'flex', alignItems: 'baseline', gap: '12px' }}>
        <h2 style={{ margin: 0, fontSize: '2rem', fontWeight: 600, color: 'var(--text-primary)' }}>
          {value}
        </h2>
        {trend && (
          <span style={{ fontSize: '0.875rem', fontWeight: 500, color: getTrendColor() }}>
            {trend}
          </span>
        )}
      </div>
    </motion.div>
  );
};

export default StatCard;
