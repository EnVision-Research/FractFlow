#!/usr/bin/env python3
"""
Example HTTP Tool for FractFlow
Demonstrates HTTP transport mode usage.
"""

import sys
import os

# Add FractFlow to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'FractFlow'))

from FractFlow.tool_template import ToolTemplate


class ExampleHttpTool(ToolTemplate):
    """
    Example tool demonstrating HTTP transport mode.
    
    This tool shows how to create a FractFlow tool that can run in HTTP mode,
    making it accessible over the network instead of just as a local subprocess.
    """
    
    # Required attributes
    SYSTEM_PROMPT = """
You are a helpful example assistant that can perform simple operations.

Available operations:
- Greet users with personalized messages
- Perform basic calculations
- Return system information

Format your responses clearly and helpfully.
"""
    
    TOOL_DESCRIPTION = """
Example tool for testing HTTP transport functionality.

This tool demonstrates how FractFlow tools can run in HTTP mode, allowing
network-based access instead of local subprocess execution.

Parameters:
    query: str - Natural language description of the operation to perform

Returns:
    result: str - Operation result with clear formatting
    status: success/error indication
"""
    
    # HTTP Transport Configuration
    TRANSPORT_MODE = "http"  # Enable HTTP mode
    HTTP_PORT = 8003        # Use specific port (avoiding conflicts)
    HTTP_HOST = "0.0.0.0" 


if __name__ == "__main__":
    print("Starting Example HTTP Tool...")
    print("Use Ctrl+C to stop the server")
    
    # This will automatically use HTTP transport based on TRANSPORT_MODE
    ExampleHttpTool.main() 