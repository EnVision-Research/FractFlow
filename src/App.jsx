import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import AgentGrid from './components/AgentGrid/AgentGrid';
import AgentTerminal from './components/Terminal/Terminal';
import './App.css';

function App() {
  const [selectedAgent, setSelectedAgent] = useState(null);
  const [showTerminal, setShowTerminal] = useState(false);

  const handleAgentSelect = (agent) => {
    setSelectedAgent(agent);
    setShowTerminal(true);
  };

  const handleTerminalClose = () => {
    setShowTerminal(false);
    // Keep selectedAgent for potential future interactions
  };

  return (
    <div className="app">
      {/* Background Effects */}
      <div className="app-background">
        <div className="bg-grid"></div>
        <div className="bg-glow"></div>
      </div>

      {/* Main Content */}
      <div className="app-content">
        {/* Agent Grid - Left Side */}
        <motion.div 
          className="grid-panel"
          animate={{ 
            width: showTerminal ? '60%' : '100%',
            transition: { duration: 0.5, ease: 'easeInOut' }
          }}
        >
          <AgentGrid
            onAgentSelect={handleAgentSelect}
            selectedAgent={selectedAgent}
          />
        </motion.div>

        {/* Terminal Panel - Right Side */}
        <AnimatePresence>
          {showTerminal && (
            <motion.div
              className="terminal-panel"
              initial={{ width: 0, opacity: 0 }}
              animate={{ 
                width: '40%', 
                opacity: 1,
                transition: { duration: 0.5, ease: 'easeInOut' }
              }}
              exit={{ 
                width: 0, 
                opacity: 0,
                transition: { duration: 0.3, ease: 'easeInOut' }
              }}
            >
              <AgentTerminal
                agent={selectedAgent}
                onClose={handleTerminalClose}
              />
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Quick Actions Overlay */}
      <AnimatePresence>
        {selectedAgent && !showTerminal && (
          <motion.div
            className="quick-actions"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 20 }}
            transition={{ duration: 0.3 }}
          >
            <div className="action-card">
              <div className="action-info">
                <h3>{selectedAgent.name}</h3>
                <p>Ready for interaction</p>
              </div>
              <button 
                onClick={() => setShowTerminal(true)}
                className="action-button"
              >
                <span className="button-icon">⚡</span>
                Launch Terminal
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Status Bar */}
      <div className="status-bar">
        <div className="status-left">
          <span className="status-item">
            <span className="status-indicator online"></span>
            FractFlow System Online
          </span>
        </div>
        <div className="status-right">
          {selectedAgent && (
            <span className="status-item">
              Selected: <span className="agent-name">{selectedAgent.name}</span>
            </span>
          )}
          <span className="status-item">
            Terminal: <span className={showTerminal ? 'active' : 'inactive'}>
              {showTerminal ? 'Active' : 'Inactive'}
            </span>
          </span>
        </div>
      </div>
    </div>
  );
}

export default App; 