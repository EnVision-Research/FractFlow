import React, { useEffect, useRef, useState } from 'react';
import { Terminal } from 'xterm';
import { FitAddon } from 'xterm-addon-fit';
import 'xterm/css/xterm.css';
import { createAgentWebSocket, CONNECTION_STATUS } from '../../services/api';
import './Terminal.css';

// Enhanced connection status constants
const TERMINAL_STATUS = {
  ...CONNECTION_STATUS,
  TERMINAL_INITIALIZING: 'terminal_initializing',
  TERMINAL_READY: 'terminal_ready',
};

// PTY handles all character detection and echoing automatically

const AgentTerminal = ({ agent, onClose }) => {
  const terminalRef = useRef(null);
  const terminalInstance = useRef(null);
  const fitAddon = useRef(null);
  const websocket = useRef(null);
  const resizeObserver = useRef(null);
  const initializationPromise = useRef(null);
  
  const [connectionStatus, setConnectionStatus] = useState(TERMINAL_STATUS.DISCONNECTED);
  const [error, setError] = useState(null);
  const [agentReady, setAgentReady] = useState(false);

  useEffect(() => {
    if (!terminalRef.current || !agent) return;

    console.log('[TERMINAL] Starting initialization process for agent:', agent.name);
    
    // Initialize with enhanced timing control
    initializeWithTimingControl();

    // Cleanup on unmount
    return () => {
      cleanup();
    };
  }, [agent]);

  const initializeWithTimingControl = async () => {
    try {
      setConnectionStatus(TERMINAL_STATUS.TERMINAL_INITIALIZING);
      setError(null);

      // Create initialization promise chain
      initializationPromise.current = new Promise(async (resolve, reject) => {
        try {
          console.log('[TERMINAL] Step 1: Waiting for DOM readiness');
          await waitForDOMReady();
          
          console.log('[TERMINAL] Step 2: Initializing terminal instance');
          await initializeTerminal();
          
          console.log('[TERMINAL] Step 3: Setting up resize observer');
          setupResizeObserver();
          
          console.log('[TERMINAL] Step 4: Terminal ready, updating status');
          setConnectionStatus(TERMINAL_STATUS.TERMINAL_READY);
          
          console.log('[TERMINAL] Step 5: Connecting to agent');
          await connectToAgent();
          
          resolve();
        } catch (error) {
          console.error('[TERMINAL] Initialization failed:', error);
          reject(error);
        }
      });

      await initializationPromise.current;
    } catch (error) {
      setConnectionStatus(TERMINAL_STATUS.ERROR);
      setError(`Initialization failed: ${error.message}`);
    }
  };

  const waitForDOMReady = () => {
    return new Promise((resolve) => {
      const checkReady = () => {
        if (terminalRef.current && terminalRef.current.offsetWidth > 0) {
          console.log('[TERMINAL] DOM ready, container dimensions:', {
            width: terminalRef.current.offsetWidth,
            height: terminalRef.current.offsetHeight
          });
          resolve();
        } else {
          console.log('[TERMINAL] Waiting for DOM readiness...');
          setTimeout(checkReady, 50);
        }
      };
      checkReady();
    });
  };

  const initializeTerminal = () => {
    return new Promise((resolve, reject) => {
      try {
        if (terminalInstance.current) {
          console.log('[TERMINAL] Terminal already initialized, disposing first');
          terminalInstance.current.dispose();
        }

        console.log('[TERMINAL] Creating new terminal instance');

        // Create terminal with cyberpunk theme - optimized for PTY
        terminalInstance.current = new Terminal({
          cursorBlink: true,
          convertEol: true,
          fontFamily: 'Fira Code, Monaco, Cascadia Code, monospace',
          fontSize: 14,
          lineHeight: 1.2,
          allowTransparency: true,
          disableStdin: false,
          // PTY optimizations
          screenReaderMode: false,
          macOptionIsMeta: true,
          macOptionClickForcesSelection: false,
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
        console.log('[TERMINAL] Opening terminal in DOM element');
        terminalInstance.current.open(terminalRef.current);

        // Enhanced fit with validation
        setTimeout(() => {
          if (fitAddon.current && terminalInstance.current) {
            try {
              fitAddon.current.fit();
              console.log('[TERMINAL] Terminal fitted successfully');
              
              // Focus the terminal
              terminalInstance.current.focus();
              console.log('[TERMINAL] Terminal focused');
              
              // Setup input handling with intelligent character detection
              setupInputHandling();
              
              // Display welcome message
              displayWelcomeMessage();
              
              resolve();
            } catch (fitError) {
              console.error('[TERMINAL] Fit operation failed:', fitError);
              reject(fitError);
            }
          } else {
            reject(new Error('Terminal or fit addon not available'));
          }
        }, 300); // Increased delay for better reliability

      } catch (error) {
        console.error('[TERMINAL] Terminal initialization error:', error);
        reject(error);
      }
    });
  };

  const setupInputHandling = () => {
    if (!terminalInstance.current) return;

    // Simplified input handling for PTY - direct passthrough
    terminalInstance.current.onData((data) => {
      console.log('[INPUT] Received data:', {
        data: data,
        length: data.length,
        charCodes: Array.from(data).map(c => c.charCodeAt(0))
      });
      
      if (websocket.current && websocket.current.readyState === WebSocket.OPEN) {
        // Direct passthrough to PTY - no local echo needed
        websocket.current.send(data);
        console.log('[INPUT] Data sent to PTY');
      } else {
        console.warn('[INPUT] WebSocket not ready, input ignored');
        terminalInstance.current.write('\x1b[31m[WARNING] Not connected to agent\x1b[0m\r\n');
      }
    });

    // Enhanced keyboard event debugging
    terminalInstance.current.onKey((e) => {
      console.log('[KEYBOARD] Key event:', {
        key: e.key,
        code: e.domEvent.code,
        altKey: e.domEvent.altKey,
        ctrlKey: e.domEvent.ctrlKey,
        shiftKey: e.domEvent.shiftKey
      });
    });
  };

  const setupResizeObserver = () => {
    if (!terminalRef.current || !fitAddon.current) return;

    resizeObserver.current = new ResizeObserver(() => {
      if (fitAddon.current && terminalInstance.current) {
        try {
          fitAddon.current.fit();
          console.log('[TERMINAL] Auto-resized on container change');
        } catch (error) {
          console.warn('[TERMINAL] Auto-resize failed:', error);
        }
      }
    });

    resizeObserver.current.observe(terminalRef.current);
  };

  const displayWelcomeMessage = () => {
    if (!terminalInstance.current) return;

    terminalInstance.current.writeln('\x1b[36m╔═══════════════════════════════════════════════════════════════════════════════╗\x1b[0m');
    terminalInstance.current.writeln('\x1b[36m║                            \x1b[33mFRACTFLOW AGENT TERMINAL\x1b[36m                            ║\x1b[0m');
    terminalInstance.current.writeln('\x1b[36m╚═══════════════════════════════════════════════════════════════════════════════╝\x1b[0m');
    terminalInstance.current.writeln('');
    terminalInstance.current.writeln(`\x1b[32m[SYSTEM]\x1b[0m Initializing connection to agent: \x1b[33m${agent.name}\x1b[0m`);
    terminalInstance.current.writeln(`\x1b[32m[SYSTEM]\x1b[0m Agent path: \x1b[90m${agent.path}\x1b[0m`);
    terminalInstance.current.writeln(`\x1b[32m[SYSTEM]\x1b[0m Terminal mode: \x1b[32m✓ PTY Enabled (支持完整终端功能)\x1b[0m`);
    terminalInstance.current.writeln('');
  };

  const connectToAgent = () => {
    return new Promise((resolve, reject) => {
      try {
        setConnectionStatus(TERMINAL_STATUS.CONNECTING);

        if (!terminalInstance.current) {
          reject(new Error('Terminal not initialized'));
          return;
        }

        terminalInstance.current.writeln('\x1b[33m[CONNECTING]\x1b[0m Establishing WebSocket connection...');

        // Create WebSocket connection
        websocket.current = createAgentWebSocket(agent.path);

        const connectionTimeout = setTimeout(() => {
          reject(new Error('Connection timeout'));
        }, 10000);

        websocket.current.onopen = () => {
          clearTimeout(connectionTimeout);
          setConnectionStatus(TERMINAL_STATUS.CONNECTED);
          terminalInstance.current.writeln('\x1b[32m[CONNECTED]\x1b[0m ✓ PTY connection established successfully');
          terminalInstance.current.writeln('\x1b[32m[READY]\x1b[0m Agent terminal is ready for interaction');
          terminalInstance.current.writeln('\x1b[33m[INFO]\x1b[0m Full terminal features enabled (完整终端功能已启用)');
          terminalInstance.current.writeln('');
          
          // Focus terminal after connection
          setTimeout(() => {
            if (terminalInstance.current) {
              terminalInstance.current.focus();
            }
          }, 100);
          
          resolve();
        };

        websocket.current.onmessage = (event) => {
          const message = event.data;
          console.log('[WS→TERMINAL] Received from server:', {
            data: message,
            length: message.length,
            charCodes: Array.from(message).map(c => c.charCodeAt(0)),
            preview: message.replace(/\x1b\[[0-9;]*m/g, '') // Remove ANSI codes for better readability
          });
          
          if (terminalInstance.current) {
            terminalInstance.current.write(message);
          }
          
          // Check if agent is ready
          if (message.includes('Agent system started') || message.includes('Interactive Mode')) {
            setAgentReady(true);
            console.log('[AGENT] Agent is now ready for interaction');
          }
        };

        websocket.current.onclose = (event) => {
          clearTimeout(connectionTimeout);
          setConnectionStatus(TERMINAL_STATUS.DISCONNECTED);
          if (terminalInstance.current) {
            terminalInstance.current.writeln('');
            terminalInstance.current.writeln(`\x1b[31m[DISCONNECTED]\x1b[0m Connection closed (Code: ${event.code})`);
            
            if (event.code !== 1000) {
              terminalInstance.current.writeln('\x1b[33m[INFO]\x1b[0m Click the retry button to reconnect');
            }
          }
        };

        websocket.current.onerror = (error) => {
          clearTimeout(connectionTimeout);
          setConnectionStatus(TERMINAL_STATUS.ERROR);
          setError('WebSocket connection failed');
          if (terminalInstance.current) {
            terminalInstance.current.writeln('\x1b[31m[ERROR]\x1b[0m ✗ Connection failed');
            terminalInstance.current.writeln('\x1b[31m[ERROR]\x1b[0m Please ensure the backend server is running');
          }
          reject(error);
        };

      } catch (err) {
        setConnectionStatus(TERMINAL_STATUS.ERROR);
        setError(err.message);
        if (terminalInstance.current) {
          terminalInstance.current.writeln(`\x1b[31m[ERROR]\x1b[0m ${err.message}`);
        }
        reject(err);
      }
    });
  };

  const cleanup = () => {
    console.log('[TERMINAL] Cleaning up resources');
    
    if (resizeObserver.current) {
      resizeObserver.current.disconnect();
      resizeObserver.current = null;
    }
    
    if (websocket.current) {
      websocket.current.close();
      websocket.current = null;
    }
    
    if (terminalInstance.current) {
      terminalInstance.current.dispose();
      terminalInstance.current = null;
    }
    
    fitAddon.current = null;
    initializationPromise.current = null;
  };

  const handleReconnect = () => {
    console.log('[TERMINAL] Reconnection requested');
    cleanup();
    setTimeout(() => {
      initializeWithTimingControl();
    }, 200);
  };

  const getStatusColor = () => {
    switch (connectionStatus) {
      case TERMINAL_STATUS.CONNECTED:
        return 'var(--primary-green)';
      case TERMINAL_STATUS.CONNECTING:
      case TERMINAL_STATUS.TERMINAL_INITIALIZING:
        return 'var(--primary-orange)';
      case TERMINAL_STATUS.ERROR:
        return '#ff4444';
      case TERMINAL_STATUS.TERMINAL_READY:
        return 'var(--primary-cyan)';
      default:
        return 'var(--text-muted)';
    }
  };

  const getStatusText = () => {
    switch (connectionStatus) {
      case TERMINAL_STATUS.CONNECTED:
        return 'Connected';
      case TERMINAL_STATUS.CONNECTING:
        return 'Connecting...';
      case TERMINAL_STATUS.TERMINAL_INITIALIZING:
        return 'Initializing...';
      case TERMINAL_STATUS.TERMINAL_READY:
        return 'Terminal Ready';
      case TERMINAL_STATUS.ERROR:
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
          
          {connectionStatus === TERMINAL_STATUS.ERROR && (
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