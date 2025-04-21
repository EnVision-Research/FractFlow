"""
Logging utilities for the FractFlow project.

Provides standardized logging functions and formatting to ensure
consistent logging across the entire system.
"""

import logging
import inspect
import json
import sys
from typing import Any, Dict, Optional, Union

# ANSI color codes
COLORS = {
    'RESET': '\033[0m',
    'BLACK': '\033[30m',
    'RED': '\033[31m',
    'GREEN': '\033[32m',
    'YELLOW': '\033[33m',
    'BLUE': '\033[34m',
    'MAGENTA': '\033[35m',
    'CYAN': '\033[36m',
    'WHITE': '\033[37m',
    'BOLD': '\033[1m',
    'UNDERLINE': '\033[4m',
    # Add dark color series
    'DARK_GRAY': '\033[90m',
    'DARK_RED': '\033[31;2m',
    'DARK_GREEN': '\033[32;2m',
    'DARK_YELLOW': '\033[33;2m',
    'DARK_BLUE': '\033[34;2m',
    'DARK_MAGENTA': '\033[35;2m',
    'DARK_CYAN': '\033[36;2m',
    'DARK_WHITE': '\033[37;2m',
}

# Set colors for log levels
LEVEL_COLORS = {
    'DEBUG': COLORS['BLUE'],
    'INFO': COLORS['GREEN'],
    'WARNING': COLORS['YELLOW'],
    'ERROR': COLORS['RED'],
    'CRITICAL': COLORS['MAGENTA'] + COLORS['BOLD']
}

# Define color configuration for message content
MESSAGE_COLORS = {
    'DEBUG': COLORS['DARK_BLUE'],
    'INFO': COLORS['DARK_GREEN'],  # Make INFO level messages darker
    'WARNING': COLORS['DARK_YELLOW'],
    'ERROR': COLORS['RED'],  # Keep errors visible
    'CRITICAL': COLORS['MAGENTA'],  # Keep critical errors visible
}

class ColorFormatter(logging.Formatter):
    """Formatter that adds color to logs"""
    
    def format(self, record):
        # Save original level name and message
        levelname = record.levelname
        message = record.getMessage()
        
        # Don't add color if not running in a terminal environment
        if sys.stdout.isatty():
            # Add color to level name
            level_color = LEVEL_COLORS.get(levelname, COLORS['RESET'])
            record.levelname = f"{level_color}{levelname}{COLORS['RESET']}"
            
            # Add color to message content (reduced brightness)
            message_color = MESSAGE_COLORS.get(levelname, COLORS['RESET'])
            
            # Replace original message with colored version
            record.msg = f"{message_color}{record.msg}{COLORS['RESET']}"
            
        formatted = super().format(record)
        
        # Restore original level name and message to avoid affecting other formatters
        record.levelname = levelname
        record.msg = record.msg.replace(f"{message_color}", "").replace(f"{COLORS['RESET']}", "")
        return formatted

# Configure default logging format
DEFAULT_FORMAT = '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
DEFAULT_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

def setup_logging(level: int = logging.INFO, use_colors: bool = True, namespace_levels: Optional[Dict[str, int]] = None):
    """
    Configure logging with standard formatting.
    
    Args:
        level: The logging level to use for root logger
        use_colors: Whether to enable colored output
        namespace_levels: Dictionary mapping logger namespaces to their log levels
    """
    # 创建根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # 移除所有现有处理器
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler()
    # 让处理器使用根logger的级别
    console_handler.setLevel(logging.DEBUG)  # 设置为DEBUG以允许所有级别通过
    
    # 使用带颜色的格式化器 
    if use_colors and sys.stdout.isatty():
        formatter = ColorFormatter(
            fmt=DEFAULT_FORMAT,
            datefmt=DEFAULT_DATE_FORMAT
        )
    else:
        formatter = logging.Formatter(
            fmt=DEFAULT_FORMAT,
            datefmt=DEFAULT_DATE_FORMAT
        )
    
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # 设置特定命名空间的日志级别
    if namespace_levels:
        for namespace, namespace_level in namespace_levels.items():
            # 获取指定命名空间的日志器并设置级别
            ns_logger = logging.getLogger(namespace)
            ns_logger.setLevel(namespace_level)
            # 确保propagate设置为True
            ns_logger.propagate = True
            
                
    # Output current log levels for debugging
    print(f"Root logger level: {logging.getLevelName(root_logger.level)}")
    print(f"Console handler level: {logging.getLevelName(console_handler.level)}")

def get_logger(name: Optional[str] = None):
    """
    Get a logger with the given name or the caller's module name.
    
    Args:
        name: Logger name (if None, uses caller's module name)
        
    Returns:
        A logger instance
    """
    if name is None:
        # Get the caller's module name
        frame = inspect.stack()[1]
        module = inspect.getmodule(frame[0])
        name = module.__name__ if module else "unknown"
    
    logger = logging.getLogger(name)
    return LoggerWrapper(logger)

class LoggerWrapper:
    """
    Wrapper around standard logger to provide improved formatting.
    """
    
    def __init__(self, logger):
        """
        Initialize the logger wrapper.
        
        Args:
            logger: The standard logger to wrap
        """
        self.logger = logger
        self.use_colors = sys.stdout.isatty()
    
    def _format_data(self, data: Union[Dict[str, Any], str]) -> str:
        """Format dictionary data for readable output."""
        if isinstance(data, dict):
            # Add color to key-value pairs
            if self.use_colors:
                # Use cyan to highlight key names, and make values darker
                return " | ".join(f"{COLORS['CYAN']}{k.upper()}{COLORS['RESET']}={COLORS['DARK_WHITE']}{self._format_value(v)}{COLORS['RESET']}" for k, v in data.items())
            else:
                return " | ".join(f"{k.upper()}={self._format_value(v)}" for k, v in data.items())
        return str(data)
    
    def _format_value(self, value: Any) -> str:
        """Format a value for logging, handling different types appropriately."""
        if isinstance(value, dict):
            return json.dumps(value, ensure_ascii=False)
        elif isinstance(value, (list, tuple)):
            if len(value) > 3:
                # Still maintain simplified representation of list items
                return f"[{len(value)} items]"
            return str(value)
        return str(value)
    
    def _get_level_color(self, level_name: str) -> str:
        """Get color corresponding to log level"""
        if not self.use_colors:
            return ""
        return LEVEL_COLORS.get(level_name.upper(), "")
    
    def info(self, message: str, data: Optional[Dict[str, Any]] = None):
        """Log an info message with optional structured data."""
        if data:
            self.logger.info(f"{message} {self._format_data(data)}")
        else:
            self.logger.info(message)
    
    def debug(self, message: str, data: Optional[Dict[str, Any]] = None):
        """Log a debug message with optional structured data."""
        if data:
            self.logger.debug(f"{message} {self._format_data(data)}")
        else:
            self.logger.debug(message)
    
    def warning(self, message: str, data: Optional[Dict[str, Any]] = None):
        """Log a warning message with optional structured data."""
        if data:
            self.logger.warning(f"{message} {self._format_data(data)}")
        else:
            self.logger.warning(message)
    
    def error(self, message: str, data: Optional[Dict[str, Any]] = None):
        """Log an error message with optional structured data."""
        if data:
            self.logger.error(f"{message} {self._format_data(data)}")
        else:
            self.logger.error(message)
    
    def critical(self, message: str, data: Optional[Dict[str, Any]] = None):
        """Log a critical message with optional structured data."""
        if data:
            self.logger.critical(f"{message} {self._format_data(data)}")
        else:
            self.logger.critical(message)
    
    def highlight(self, message: str, data: Optional[Dict[str, Any]] = None):
        """
        Highlight important results or final output, using bright colors and bold text.
        
        Args:
            message: Message to highlight
            data: Optional structured data
        """
        highlighted_msg = message
        if self.use_colors:
            highlighted_msg = f"{COLORS['BOLD']}{COLORS['WHITE']}{message}{COLORS['RESET']}"
            
        if data:
            # Highlight data portion
            formatted_data = " ".join(f"{COLORS['BOLD']}{COLORS['CYAN']}{k.upper()}{COLORS['RESET']}={COLORS['WHITE']}{self._format_value(v)}{COLORS['RESET']}" 
                                    for k, v in data.items()) if self.use_colors else self._format_data(data)
            self.logger.info(f"{highlighted_msg} {formatted_data}")
        else:
            self.logger.info(highlighted_msg)
            
    def result(self, message: str, data: Optional[Dict[str, Any]] = None):
        """
        Log final results in a highlighted format.
        This is an alias for the highlight method.
        
        Args:
            message: Result message
            data: Optional structured data
        """
        self.highlight(message, data) 