import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import './AgentCard.css';

const AgentCard = ({ agent, onClick, isSelected = false }) => {
  const [isDescriptionExpanded, setIsDescriptionExpanded] = useState(false);
  
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

  const toggleDescription = (event) => {
    event.stopPropagation(); // 防止触发卡片点击事件
    setIsDescriptionExpanded(!isDescriptionExpanded);
  };

  const agentType = getAgentType(agent.id);
  const typeColor = getAgentTypeColor(agentType);
  
  // 检查是否需要显示展开按钮
  const shouldShowExpandButton = agent.description && agent.description.length > 120;
  const displayedDescription = shouldShowExpandButton && !isDescriptionExpanded 
    ? agent.description.substring(0, 120) + '...'
    : agent.description;

  return (
    <motion.div
      className={`agent-card ${isSelected ? 'selected' : ''} ${isDescriptionExpanded ? 'expanded' : ''}`}
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
      layout
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
              <motion.div
                className="description-content"
                initial={false}
                animate={{
                  height: isDescriptionExpanded ? 'auto' : 'auto'
                }}
                transition={{ duration: 0.3, ease: 'easeInOut' }}
              >
                <p>{displayedDescription}</p>
              </motion.div>
              
              {shouldShowExpandButton && (
                <motion.button
                  className="expand-button"
                  onClick={toggleDescription}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: 0.1 }}
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                >
                  {isDescriptionExpanded ? '收起' : '展开'}
                  <motion.span 
                    className="expand-icon"
                    animate={{ rotate: isDescriptionExpanded ? 180 : 0 }}
                    transition={{ duration: 0.3 }}
                  >
                    ▼
                  </motion.span>
                </motion.button>
              )}
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