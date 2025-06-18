"""
File I/O Agent - Unified Interface

This module provides a unified interface for file I/O operations that can run in multiple modes:
1. MCP Server mode (default): Provides AI-enhanced file operations as MCP tools
2. Interactive mode: Runs as an interactive agent with file I/O capabilities
3. Single query mode: Processes a single query and exits

Usage:
  python file_io_agent.py                        # MCP Server mode (default)
  python file_io_agent.py --interactive          # Interactive mode
  python file_io_agent.py --query "..."          # Single query mode
"""

import os
import sys

# Add the project root directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../..'))
sys.path.append(project_root)

# Import the FractFlow ToolTemplate
from FractFlow.tool_template import ToolTemplate

class FileIOAgent(ToolTemplate):
    """File I/O operations agent using ToolTemplate"""
    
    SYSTEM_PROMPT = """
You are a File I/O Assistant specialized in helping with text file operations.

# Core Capabilities
- Reading: get file content (whole file, line ranges, with line numbers, in chunks)
- Writing: create, overwrite, append to, and insert into files
- Information: check file existence, count lines
- Management: delete specific lines (single or multiple)
- Directory: list files and subdirectories in directories

# Key Workflows

## Working with Large Files
1. FIRST check file size by getting the total line count
2. If file is large (>1000 lines), use chunking strategy:
   - Divide file into manageable chunks (500-1000 lines)
   - Process each chunk separately while maintaining context
   - Consider using overlap between chunks (50-100 lines) for better continuity

## File Editing Workflow
1. ALWAYS verify file exists before attempting to read or modify
2. For modifications, read current content first to understand the file
3. Choose the most appropriate action:
   - create_file: When creating new or completely overwriting
   - append_content: When adding to the end
   - insert_content_at_line: When adding at specific position
   - delete_line_at: When removing content

Always choose the most efficient and appropriate tool for each task.
When working with line numbers, remember they are 1-indexed (first line is 1).

注意：
1. 无论传入的query 有多长，你都必须确保把信息能完整地保存下来，不要省略、遗漏任何信息。
2. 跟你交流的是LLM，不是人类，你做完之后，不需要提任何建议，只需要把是否顺利执行返回就行。
3. 在编辑一个文件之前，请先查看文件相邻5行的内容，以确保编辑的正确性。
"""
    
    TOOLS = [
        ("tools/core/file_io/file_io_mcp.py", "file_operations")
    ]
    
    MCP_SERVER_NAME = "file_io_agent"
    
    TOOL_DESCRIPTION = """Processes file operations including reading, writing, management, and directory listing tasks.
    
    Parameters:
        query: str - File operation with path and details (e.g., "Read lines 10-20 from /path/file.txt", "Create file config.py with content: import os", or "List files in output directory")
        
    Returns:
        str - Operation result with file content, directory listing, or confirmation message
        
    Note: Supports chunked reading for large files, line-based operations, directory browsing, and automatic directory creation.
    """
    
    @classmethod
    def create_config(cls):
        """Custom configuration for File I/O agent"""
        from FractFlow.infra.config import ConfigManager
        from dotenv import load_dotenv
        
        load_dotenv()
        return ConfigManager(
            provider='deepseek',
            deepseek_model='deepseek-chat',
            max_iterations=20,  # Higher iterations for complex file operations
            custom_system_prompt=cls.SYSTEM_PROMPT,
            tool_calling_version='stable'
        )

if __name__ == "__main__":
    FileIOAgent.main() 