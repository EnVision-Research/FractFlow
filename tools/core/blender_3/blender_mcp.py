"""
Blender MCP Tool Provider - Execute Code Only

This module provides a simplified interface to the blender-mcp execute_code functionality.
Only exposes the execute_blender_code tool for Python code execution in Blender.
"""

import sys
from pathlib import Path
from mcp.server.fastmcp import FastMCP, Context

# Add blender-mcp to path so we can import its modules
current_dir = Path(__file__).parent
blender_mcp_src = current_dir / "blender-mcp" / "src"
if blender_mcp_src.exists():
    sys.path.insert(0, str(blender_mcp_src))

# Import the original blender-mcp server functions
try:
    from blender_mcp.server import execute_blender_code as _original_execute_blender_code
    from blender_mcp.server import get_blender_connection
except ImportError as e:
    print(f"Warning: Could not import blender-mcp modules: {e}")
    _original_execute_blender_code = None

# Initialize FastMCP server
mcp = FastMCP("blender_code_executor")

@mcp.tool()
def execute_blender_code(ctx: Context, code: str) -> str:
    """
    Execute Python code directly in Blender.
    
    This tool connects directly to the Blender addon socket server and executes 
    arbitrary Python code within the Blender environment. Make sure Blender is 
    running with the MCP addon enabled and listening on the default port (8888).
    
    Parameters:
        code: str - Python code to execute in Blender
    
    Returns:
        str - Execution result, error message, or status information
    
    Examples:
        - execute_blender_code("import bpy; bpy.ops.mesh.primitive_cube_add()")
        - execute_blender_code("bpy.context.object.location = (2, 0, 1)")
        - execute_blender_code("print([obj.name for obj in bpy.context.scene.objects])")
    """
    if _original_execute_blender_code is None:
        return "Error: blender-mcp modules not available. Please check the installation."
    
    try:
        # Call the original blender-mcp function directly
        return _original_execute_blender_code(ctx, code)
    except Exception as e:
        return f"Error executing code: {str(e)}"

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio') 