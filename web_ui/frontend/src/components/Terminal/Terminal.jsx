import React, { useEffect, useRef, useState } from 'react';
import { Terminal } from 'xterm';
import { FitAddon } from 'xterm-addon-fit';
import 'xterm/css/xterm.css';
import { createAgentWebSocket, CONNECTION_STATUS } from '../../services/api';
import './Terminal.css';

const AgentTerminal = ({ agent, onClose }) => {
  const terminalRef = useRef(null);
  const terminalInstance = useRef(null);
  const fitAddon = useRef(null);
  const websocket = useRef(null);
  const [connectionStatus, setConnectionStatus] = useState(CONNECTION_STATUS.DISCONNECTED);
  const [error, setError] = useState(null);
  const [agentReady, setAgentReady] = useState(false);

  useEffect(() => {
    if (!terminalRef.current || !agent) return;

    // Initialize terminal
    initializeTerminal();
    
    // Connect to agent
    connectToAgent();

    // Cleanup on unmount
    return () => {
      cleanup();
    };
  }, [agent]);

  const initializeTerminal = () => {
    if (terminalInstance.current) return;

    console.log('Initializing terminal...');

    // Create terminal with cyberpunk theme
    terminalInstance.current = new Terminal({
      cursorBlink: true,
      convertEol: true,
      fontFamily: 'Fira Code, Monaco, Cascadia Code, monospace',
      fontSize: 14,
      lineHeight: 1.2,
      allowTransparency: true,
      disableStdin: false, // Explicitly enable stdin
      theme: {
        background: '#0a0a0f',
        foreground: '#00ffff',
        cursor: '#00ffff',
        cursorAccent: '#ff6700',
        selection: 'rgba(0, 255, 255, 0.3)',
        black: '#000000',
        red: '#ff4444',
        green: '#00ff41',
        yellow: '#ffff00',
        blue: '#0066ff',
        magenta: '#ff1493',
        cyan: '#00ffff',
        white: '#ffffff',
        brightBlack: '#333333',
        brightRed: '#ff6666',
        brightGreen: '#66ff66',
        brightYellow: '#ffff66',
        brightBlue: '#6699ff',
        brightMagenta: '#ff66cc',
        brightCyan: '#66ffff',
        brightWhite: '#ffffff',
      },
    });

    // Add fit addon
    fitAddon.current = new FitAddon();
    terminalInstance.current.loadAddon(fitAddon.current);

    // Open terminal
    console.log('Opening terminal in DOM element:', terminalRef.current);
    terminalInstance.current.open(terminalRef.current);

    // Fit terminal with delay to ensure container is rendered
    setTimeout(() => {
      if (fitAddon.current) {
        fitAddon.current.fit();
        console.log('Terminal fitted');
      }
      // Focus the terminal to enable keyboard input
      if (terminalInstance.current) {
        terminalInstance.current.focus();
        console.log('Terminal focused');
      }
    }, 200); // Increased delay

    // Handle user input
    terminalInstance.current.onData((data) => {
      console.log('Terminal input received:', data, 'Character codes:', Array.from(data).map(c => c.charCodeAt(0)));
      
      if (websocket.current && websocket.current.readyState === WebSocket.OPEN) {
        // Send data to backend
        websocket.current.send(data);
        
        // Local echo for most characters (but not for control characters like Enter, Backspace, etc.)
        const charCode = data.charCodeAt(0);
        if (charCode >= 32 && charCode <= 126) {
          // Printable ASCII characters - echo locally
          terminalInstance.current.write(data);
        } else if (charCode === 13) {
          // Enter key - move to new line and log
          console.log('Enter key pressed, sending command to agent');
          terminalInstance.current.write('\r\n');
        } else if (charCode === 8 || charCode === 127) {
          // Backspace - handle locally
          terminalInstance.current.write('\b \b');
        } else {
          console.log('Control character:', charCode);
        }
      } else {
        console.warn('WebSocket not ready, input ignored');
      }
    });

    // Additional keyboard event listener for debugging
    terminalInstance.current.onKey((e) => {
      console.log('Terminal key event:', e.key, 'DOM event:', e.domEvent);
    });

    // Welcome message with cyberpunk style
    terminalInstance.current.writeln('\x1b[36m╔═══════════════════════════════════════════════════════════════════════════════╗\x1b[0m');
    terminalInstance.current.writeln('\x1b[36m║                            \x1b[33mFRACTFLOW AGENT TERMINAL\x1b[36m                            ║\x1b[0m');
    terminalInstance.current.writeln('\x1b[36m╚═══════════════════════════════════════════════════════════════════════════════╝\x1b[0m');
    terminalInstance.current.writeln('');
    terminalInstance.current.writeln(`\x1b[32m[SYSTEM]\x1b[0m Initializing connection to agent: \x1b[33m${agent.name}\x1b[0m`);
    terminalInstance.current.writeln(`\x1b[32m[SYSTEM]\x1b[0m Agent path: \x1b[90m${agent.path}\x1b[0m`);
    terminalInstance.current.writeln('');
    
    console.log('Terminal initialized successfully, cursor should be blinking');
  };

  const connectToAgent = () => {
    try {
      setConnectionStatus(CONNECTION_STATUS.CONNECTING);
      setError(null);

      terminalInstance.current.writeln('\x1b[33m[CONNECTING]\x1b[0m Establishing WebSocket connection...');

      // Create WebSocket connection
      websocket.current = createAgentWebSocket(agent.path);

      websocket.current.onopen = () => {
        setConnectionStatus(CONNECTION_STATUS.CONNECTED);
        terminalInstance.current.writeln('\x1b[32m[CONNECTED]\x1b[0m ✓ Connection established successfully');
        terminalInstance.current.writeln('\x1b[32m[READY]\x1b[0m Agent is ready for interaction');
        terminalInstance.current.writeln('\x1b[33m[DEBUG]\x1b[0m Try typing something now... (Check browser console for debug info)');
        terminalInstance.current.writeln('');
        
        // Focus terminal after connection is established
        setTimeout(() => {
          if (terminalInstance.current) {
            terminalInstance.current.focus();
          }
        }, 100);
      };

      websocket.current.onmessage = (event) => {
        const message = event.data;
        terminalInstance.current.write(message);
        
        // Check if agent is ready for interaction
        if (message.includes('Agent system started') || message.includes('Interactive Mode')) {
          setAgentReady(true);
          console.log('Agent is now ready for interaction');
        }
      };

      websocket.current.onclose = (event) => {
        setConnectionStatus(CONNECTION_STATUS.DISCONNECTED);
        terminalInstance.current.writeln('');
        terminalInstance.current.writeln(`\x1b[31m[DISCONNECTED]\x1b[0m Connection closed (Code: ${event.code})`);
        
        if (event.code !== 1000) { // Not a normal closure
          terminalInstance.current.writeln('\x1b[33m[INFO]\x1b[0m Press Ctrl+C to exit or click the close button');
        }
      };

      websocket.current.onerror = (error) => {
        setConnectionStatus(CONNECTION_STATUS.ERROR);
        setError('WebSocket connection failed');
        terminalInstance.current.writeln('\x1b[31m[ERROR]\x1b[0m ✗ Connection failed');
        terminalInstance.current.writeln('\x1b[31m[ERROR]\x1b[0m Please ensure the backend server is running');
      };

    } catch (err) {
      setConnectionStatus(CONNECTION_STATUS.ERROR);
      setError(err.message);
      terminalInstance.current.writeln(`\x1b[31m[ERROR]\x1b[0m ${err.message}`);
    }
  };

  const cleanup = () => {
    if (websocket.current) {
      websocket.current.close();
      websocket.current = null;
    }
    
    if (terminalInstance.current) {
      terminalInstance.current.dispose();
      terminalInstance.current = null;
    }
    
    fitAddon.current = null;
  };

  const handleReconnect = () => {
    cleanup();
    setTimeout(() => {
      initializeTerminal();
      connectToAgent();
    }, 100);
  };

  const getStatusColor = () => {
    switch (connectionStatus) {
      case CONNECTION_STATUS.CONNECTED:
        return 'var(--primary-green)';
      case CONNECTION_STATUS.CONNECTING:
        return 'var(--primary-orange)';
      case CONNECTION_STATUS.ERROR:
        return '#ff4444';
      default:
        return 'var(--text-muted)';
    }
  };

  const getStatusText = () => {
    switch (connectionStatus) {
      case CONNECTION_STATUS.CONNECTED:
        return 'Connected';
      case CONNECTION_STATUS.CONNECTING:
        return 'Connecting...';
      case CONNECTION_STATUS.ERROR:
        return 'Error';
      default:
        return 'Disconnected';
    }
  };

  if (!agent) {
    return (
      <div className="terminal-container">
        <div className="terminal-placeholder">
          <div className="placeholder-icon">💻</div>
          <h3>No Agent Selected</h3>
          <p>Select an agent from the grid to start an interactive session</p>
        </div>
      </div>
    );
  }

  return (
    <div className="terminal-container">
      {/* Terminal Header */}
      <div className="terminal-header">
        <div className="terminal-title">
          <div className="title-icon">⚡</div>
          <div className="title-text">
            <span className="agent-name">{agent.name}</span>
            <span className="session-label">Interactive Session</span>
          </div>
        </div>
        
        <div className="terminal-controls">
          <div 
            className="status-indicator"
            style={{ '--status-color': getStatusColor() }}
            title={getStatusText()}
          >
            <div className="status-dot" />
            <span className="status-text">{getStatusText()}</span>
          </div>
          
          {connectionStatus === CONNECTION_STATUS.ERROR && (
            <button 
              onClick={handleReconnect}
              className="reconnect-btn"
              title="Reconnect"
            >
              🔄
            </button>
          )}
          
          <button 
            onClick={onClose}
            className="close-btn"
            title="Close Terminal"
          >
            ✕
          </button>
        </div>
      </div>

      {/* Terminal Body */}
      <div className="terminal-body">
        <div 
          ref={terminalRef} 
          className="terminal-content"
          tabIndex={0}
          onClick={() => {
            // Focus terminal when clicked
            if (terminalInstance.current) {
              terminalInstance.current.focus();
            }
          }}
          onFocus={() => {
            // Also focus the xterm instance when the container gets focus
            if (terminalInstance.current) {
              terminalInstance.current.focus();
            }
          }}
        />
        
        {/* Scan lines effect */}
        <div className="terminal-scanlines" />
      </div>

      {/* Error Message */}
      {error && (
        <div className="terminal-error">
          <span className="error-icon">⚠️</span>
          <span className="error-text">{error}</span>
          <button onClick={handleReconnect} className="error-retry">
            Retry
          </button>
        </div>
      )}
    </div>
  );
};

export default AgentTerminal; 