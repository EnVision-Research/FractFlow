import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import AgentCard from './AgentCard';
import { fetchAgents } from '../../services/api';
import './AgentGrid.css';

const AgentGrid = ({ onAgentSelect, selectedAgent }) => {
  const [agents, setAgents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filter, setFilter] = useState('all'); // 'all', 'core', 'composite'

  // Fetch agents on component mount
  useEffect(() => {
    loadAgents();
  }, []);

  const loadAgents = async () => {
    try {
      setLoading(true);
      setError(null);
      const agentData = await fetchAgents();
      setAgents(agentData);
    } catch (err) {
      setError(err.message);
      console.error('Failed to load agents:', err);
    } finally {
      setLoading(false);
    }
  };

  // Filter and search logic
  const filteredAgents = agents.filter(agent => {
    const matchesSearch = agent.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         agent.path.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         (agent.description && agent.description.toLowerCase().includes(searchTerm.toLowerCase()));
    
    const matchesFilter = filter === 'all' || 
                         (filter === 'composite' && agent.id.includes('composite')) ||
                         (filter === 'core' && !agent.id.includes('composite'));
    
    return matchesSearch && matchesFilter;
  });

  const handleAgentClick = (agent) => {
    onAgentSelect?.(agent);
  };

  const handleRetry = () => {
    loadAgents();
  };

  if (loading) {
    return (
      <div className="agent-grid-container">
        <div className="loading-state">
          <div className="loading-spinner" />
          <h2>Scanning for Agents...</h2>
          <p>Initializing FractFlow Agent Discovery System</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="agent-grid-container">
        <div className="error-state">
          <div className="error-icon">⚠️</div>
          <h2>Connection Failed</h2>
          <p>{error}</p>
          <button onClick={handleRetry} className="retry-button">
            Retry Connection
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="agent-grid-container">
      {/* Header */}
      <div className="grid-header">
        <div className="header-content">
          <h1 className="grid-title">FractFlow Agent Network</h1>
          <p className="grid-subtitle">
            {agents.length} Agent{agents.length !== 1 ? 's' : ''} Available
          </p>
        </div>
        
        {/* Controls */}
        <div className="grid-controls">
          {/* Search */}
          <div className="search-container">
            <input
              type="text"
              placeholder="Search agents..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="search-input"
            />
            <div className="search-icon">🔍</div>
          </div>
          
          {/* Filter */}
          <div className="filter-container">
            <select
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              className="filter-select"
            >
              <option value="all">All Types</option>
              <option value="core">Core Agents</option>
              <option value="composite">Composite Agents</option>
            </select>
          </div>
        </div>
      </div>

      {/* Results info */}
      {searchTerm && (
        <div className="results-info">
          Found {filteredAgents.length} agent{filteredAgents.length !== 1 ? 's' : ''} 
          {searchTerm && ` matching "${searchTerm}"`}
        </div>
      )}

      {/* Agent Grid */}
      <motion.div 
        className="agent-grid"
        layout
      >
        <AnimatePresence>
          {filteredAgents.map((agent, index) => (
            <motion.div
              key={agent.id}
              layout
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.8 }}
              transition={{ 
                duration: 0.3,
                delay: index * 0.05 // Stagger animation
              }}
            >
              <AgentCard
                agent={agent}
                onClick={handleAgentClick}
                isSelected={selectedAgent?.id === agent.id}
              />
            </motion.div>
          ))}
        </AnimatePresence>
      </motion.div>

      {/* Empty state */}
      {filteredAgents.length === 0 && !loading && (
        <div className="empty-state">
          <div className="empty-icon">🤖</div>
          <h3>No Agents Found</h3>
          <p>
            {searchTerm 
              ? `No agents match your search for "${searchTerm}"`
              : 'No agents are currently available'
            }
          </p>
          {searchTerm && (
            <button 
              onClick={() => setSearchTerm('')}
              className="clear-search-button"
            >
              Clear Search
            </button>
          )}
        </div>
      )}
    </div>
  );
};

export default AgentGrid; 