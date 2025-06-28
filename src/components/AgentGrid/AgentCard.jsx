import React from 'react';
import { motion } from 'framer-motion';
import './AgentCard.css';

const AgentCard = ({ agent, onClick, isSelected = false }) => {
  const getAgentType = (id) => {
    if (id.includes('composite')) return 'composite';
    return 'core';
  };

  const getAgentTypeColor = (type) => {
    return type === 'composite' ? 'var(--primary-orange)' : 'var(--primary-cyan)';
  };

  const handleClick = () => {
    onClick?.(agent);
  };

  const handleKeyDown = (event) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      handleClick();
    }
  };

  const agentType = getAgentType(agent.id);
  const typeColor = getAgentTypeColor(agentType);

  return (
    <motion.div
      className={`agent-card ${isSelected ? 'selected' : ''}`}
      onClick={handleClick}
      onKeyDown={handleKeyDown}
      tabIndex={0}
      role="button"
      aria-label={`Select agent ${agent.name}`}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ 
        scale: 1.05,
        transition: { duration: 0.2 }
      }}
      whileTap={{ scale: 0.98 }}
      style={{
        '--agent-color': typeColor
      }}
    >
      {/* Glow effect background */}
      <div className="card-glow" />
      
      {/* Scan lines effect */}
      <div className="scan-lines" />
      
      {/* Card content */}
      <div className="card-content">
        {/* Header */}
        <div className="card-header">
          <div className="agent-type-badge">
            <span className="type-indicator" />
            {agentType}
          </div>
          <div className="status-indicator online" title="Agent Available" />
        </div>
        
        {/* Main content */}
        <div className="card-body">
          <h3 className="agent-name">{agent.name}</h3>
          <p className="agent-path">{agent.path}</p>
          
          {agent.description && (
            <div className="agent-description">
              <p>{agent.description.substring(0, 120)}{agent.description.length > 120 ? '...' : ''}</p>
            </div>
          )}
        </div>
        
        {/* Footer */}
        <div className="card-footer">
          <div className="action-hint">
            <span className="hint-text">Click to interact</span>
            <span className="hint-icon">→</span>
          </div>
        </div>
      </div>
      
      {/* Ripple effect */}
      <div className="ripple-container">
        <div className="ripple" />
      </div>
    </motion.div>
  );
};

export default AgentCard; 