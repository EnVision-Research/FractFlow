import os
import pathlib
from typing import List, Dict, Union, Optional, Tuple
import re
from mcp.server.fastmcp import FastMCP

# Initialize MCP server
mcp = FastMCP("file_io_tool")


def normalize_path(file_path: str) -> str:
    """
    Normalize a file path to prevent path traversal attacks.
    
    Args:
        file_path: The file path to normalize
        
    Returns:
        Normalized file path
    """
    # Convert to absolute path if not already
    path = os.path.abspath(os.path.expanduser(file_path))
    return path


def ensure_parent_directory(file_path: str) -> None:
    """
    Ensure that the parent directory of a file exists.
    
    Args:
        file_path: The file path
    """
    parent_dir = os.path.dirname(file_path)
    if parent_dir and not os.path.exists(parent_dir):
        os.makedirs(parent_dir)


def check_file_exists(file_path: str) -> Dict[str, Union[bool, str]]:
    """
    Check if a file exists at the specified path.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Dictionary with 'exists' status and additional info
    """
    try:
        path = normalize_path(file_path)
        exists = os.path.isfile(path)
        
        result = {
            "exists": exists,
            "path": path
        }
        
        if not exists:
            result["message"] = f"File does not exist: {path}"
        
        return result
    except Exception as e:
        return {
            "exists": False,
            "error": str(e),
            "message": f"Error checking file existence: {str(e)}"
        }


@mcp.tool()
def get_total_line_count(file_path: str) -> Dict[str, Union[int, str, bool]]:
    """
    Counts the total number of lines in a text file.
    
    Parameters:
        file_path: str - Absolute or relative path to the file
    
    Notes:
        - Returns 0 for empty files
        - Fails if file doesn't exist
        - Counts all lines including empty ones
        - Performance may degrade for very large files (>100MB)
    
    Returns:
        dict with keys:
        - success: bool - True if operation succeeded, False otherwise
        - line_count: int - Number of lines in file (only if success=True)
        - path: str - Normalized absolute path to the file
        - error: str - Error type if operation failed
        - message: str - Detailed error message if operation failed
    
    Examples:
        "How many lines are in log.txt?" → get_total_line_count(file_path="log.txt")
        "Count lines in ./src/main.py" → get_total_line_count(file_path="./src/main.py")
    """
    try:
        path = normalize_path(file_path)
        
        # Check if file exists
        if not os.path.isfile(path):
            return {
                "success": False,
                "error": "File not found",
                "message": f"File does not exist: {path}. Please check the file path or create the file first."
            }
        
        # Count lines
        with open(path, 'r', encoding='utf-8') as file:
            line_count = sum(1 for _ in file)
        
        return {
            "success": True,
            "line_count": line_count,
            "path": path
        }
    except PermissionError:
        return {
            "success": False,
            "error": "Permission denied",
            "message": f"Cannot read file due to permission issues: {path}. Please check file permissions."
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"Error counting lines in file: {str(e)}"
        }


@mcp.tool()
def read_lines(file_path: str, start_line: int = 1, end_line: Optional[int] = None) -> Dict[str, Union[str, int, bool, List[str]]]:
    """
    Reads specific line range from a text file.
    
    Parameters:
        file_path: str - Absolute or relative path to the file
        start_line: int - First line to read (1-indexed, default=1)
        end_line: int - Last line to read (1-indexed, inclusive, default=end of file)
    
    Notes:
        - Line numbers are 1-indexed (first line is 1, not 0)
        - If end_line exceeds file length, reads until end of file
        - Returns error if start_line < 1 or start_line > file length
        - Returns empty content for empty files
    
    Returns:
        dict with keys:
        - success: bool - True if operation succeeded, False otherwise
        - content: str - File content from specified range (only if success=True)
        - lines: list - List of line strings (only if success=True)
        - start_line: int - Actual starting line read
        - end_line: int - Actual ending line read
        - line_count: int - Total number of lines in file
        - path: str - Normalized absolute path to the file
        - error: str - Error type if operation failed
        - message: str - Success/error message
    
    Examples:
        "Read file data.txt" → read_lines(file_path="data.txt")
        "Show lines 10-20 from log.txt" → read_lines(file_path="log.txt", start_line=10, end_line=20)
        "Read first 5 lines of config.ini" → read_lines(file_path="config.ini", end_line=5)
    """
    try:
        path = normalize_path(file_path)
        
        # Check if file exists
        if not os.path.isfile(path):
            return {
                "success": False,
                "error": "File not found",
                "message": f"File does not exist: {path}. Please check the file path or create the file first."
            }
        
        # Validate line ranges
        if start_line < 1:
            return {
                "success": False,
                "error": "Invalid start line",
                "message": f"Start line must be at least 1, got {start_line}."
            }
            
        # Get file line count
        line_count_result = get_total_line_count(path)
        if not line_count_result.get("success", False):
            return line_count_result
            
        line_count = line_count_result["line_count"]
        
        # Empty file check
        if line_count == 0:
            return {
                "success": True,
                "content": "",
                "lines": [],
                "start_line": start_line,
                "end_line": start_line,
                "line_count": 0,
                "path": path,
                "message": "File is empty"
            }
            
        # Adjust end_line if not specified or exceeds file length
        if end_line is None or end_line > line_count:
            end_line = line_count
            
        # Check if start_line is beyond file length
        if start_line > line_count:
            return {
                "success": False,
                "error": "Invalid start line",
                "message": f"Start line ({start_line}) exceeds file length ({line_count})."
            }
            
        # Read file content
        with open(path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
            
        # Get requested lines (adjust for 0-indexed list)
        requested_lines = lines[start_line-1:end_line]
        content = ''.join(requested_lines)
        
        return {
            "success": True,
            "content": content,
            "lines": requested_lines,
            "start_line": start_line,
            "end_line": end_line,
            "line_count": line_count,
            "path": path
        }
    except PermissionError:
        return {
            "success": False,
            "error": "Permission denied",
            "message": f"Cannot read file due to permission issues: {path}. Please check file permissions."
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"Error reading file range: {str(e)}"
        }


@mcp.tool()
def read_file_in_chunks(file_path: str, chunk_size: int, 
                    overlap: int = 0, 
                    chunk_index: Optional[int] = None) -> Dict[str, Union[str, int, bool, List[Dict]]]:
    """
    Divides file into chunks for processing large files, with optional overlap between chunks.
    
    Parameters:
        file_path: str - Absolute or relative path to the file
        chunk_size: int - Number of lines per chunk
        overlap: int - Number of overlapping lines between chunks (default=0)
        chunk_index: int - Specific chunk to retrieve (0-indexed, default=None)
    
    Notes:
        - When chunk_index is None, returns metadata about all chunks without content
        - When chunk_index is specified, returns content of only that chunk
        - chunk_index is 0-indexed (first chunk is 0)
        - overlap must be less than chunk_size
        - For large files, first get metadata (without chunk_index), then request specific chunks
    
    Returns:
        If chunk_index is None:
            dict with keys:
            - success: bool - True if operation succeeded, False otherwise
            - chunks: list - List of dicts with chunk metadata (index, start_line, end_line)
            - chunk_count: int - Total number of chunks
            - line_count: int - Total number of lines in file
            - path: str - Normalized absolute path to the file
            - message: str - Success/error message
        
        If chunk_index is specified:
            dict with keys:
            - success: bool - True if operation succeeded, False otherwise
            - content: str - Content of the specified chunk
            - lines: list - List of line strings in the chunk
            - chunk_index: int - Index of the retrieved chunk
            - total_chunks: int - Total number of chunks
            - start_line: int - Starting line number of chunk
            - end_line: int - Ending line number of chunk
            - line_count: int - Total number of lines in file
            - path: str - Normalized absolute path to the file
            - error: str - Error type if operation failed
            - message: str - Success/error message
    
    Examples:
        "Get chunk info for large_log.txt with 500-line chunks" → read_file_in_chunks(file_path="large_log.txt", chunk_size=500)
        "Read chunk 2 from data.csv with 100-line chunks" → read_file_in_chunks(file_path="data.csv", chunk_size=100, chunk_index=2)
        "Read chunk 1 with 30 lines of overlap" → read_file_in_chunks(file_path="file.txt", chunk_size=200, overlap=30, chunk_index=1)
    """
    try:
        path = normalize_path(file_path)
        
        # Check if file exists
        if not os.path.isfile(path):
            return {
                "success": False,
                "error": "File not found",
                "message": f"File does not exist: {path}. Please check the file path or create the file first."
            }
            
        # Validate parameters
        if chunk_size <= 0:
            return {
                "success": False,
                "error": "Invalid chunk size",
                "message": f"Chunk size must be positive, got {chunk_size}."
            }
            
        if overlap < 0:
            return {
                "success": False,
                "error": "Invalid overlap",
                "message": f"Overlap must be non-negative, got {overlap}."
            }
            
        if overlap >= chunk_size:
            return {
                "success": False,
                "error": "Invalid overlap",
                "message": f"Overlap ({overlap}) must be less than chunk size ({chunk_size})."
            }
        
        # Get file line count
        line_count_result = get_total_line_count(path)
        if not line_count_result.get("success", False):
            return line_count_result
            
        line_count = line_count_result["line_count"]
        
        # Empty file check
        if line_count == 0:
            return {
                "success": True,
                "chunks": [],
                "chunk_count": 0,
                "line_count": 0,
                "path": path,
                "message": "File is empty"
            }
            
        # Calculate number of chunks
        if line_count <= chunk_size:
            chunk_count = 1
        else:
            # Calculate effective step size between chunks
            step = chunk_size - overlap
            chunk_count = (line_count - chunk_size) // step + 2
            
        # Generate chunk metadata
        chunks = []
        for i in range(chunk_count):
            start = i * (chunk_size - overlap) + 1  # 1-indexed
            end = min(start + chunk_size - 1, line_count)  # inclusive end
            
            chunks.append({
                "index": i,
                "start_line": start,
                "end_line": end
            })
        
        # If chunk_index is specified, return that specific chunk
        if chunk_index is not None:
            if chunk_index < 0 or chunk_index >= chunk_count:
                return {
                    "success": False,
                    "error": "Invalid chunk index",
                    "message": f"Chunk index must be between 0 and {chunk_count-1}, got {chunk_index}."
                }
                
            chunk_info = chunks[chunk_index]
            chunk_content = read_lines(path, chunk_info["start_line"], chunk_info["end_line"])
            
            if not chunk_content.get("success", False):
                return chunk_content
                
            return {
                "success": True,
                "content": chunk_content["content"],
                "lines": chunk_content["lines"],
                "chunk_index": chunk_index,
                "total_chunks": chunk_count,
                "start_line": chunk_info["start_line"],
                "end_line": chunk_info["end_line"],
                "line_count": line_count,
                "path": path
            }
        else:
            # Return metadata about all chunks
            return {
                "success": True,
                "chunks": chunks,
                "chunk_count": chunk_count,
                "line_count": line_count,
                "path": path,
                "message": f"File contains {line_count} lines divided into {chunk_count} chunks of size {chunk_size} with overlap {overlap}"
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"Error reading file chunks: {str(e)}"
        }


@mcp.tool()
def read_with_line_numbers(file_path: str, start_line: int = 1, 
                               end_line: Optional[int] = None) -> Dict[str, Union[str, int, bool]]:
    """
    Reads file content with line numbers prefixed to each line (similar to 'cat -n').
    
    Parameters:
        file_path: str - Absolute or relative path to the file
        start_line: int - First line to read (1-indexed, default=1)
        end_line: int - Last line to read (1-indexed, inclusive, default=end of file)
    
    Notes:
        - Line numbers are 1-indexed (first line is 1, not 0)
        - Line numbers are displayed with consistent width
        - Format is "{line_number:4d} | {line_content}"
        - Otherwise behaves identically to read_lines()
    
    Returns:
        dict with keys:
        - success: bool - True if operation succeeded, False otherwise
        - content: str - File content with line numbers
        - lines: list - List of line strings without line numbers
        - start_line: int - Actual starting line read
        - end_line: int - Actual ending line read
        - line_count: int - Total number of lines in file
        - path: str - Normalized absolute path to the file
        - error: str - Error type if operation failed
        - message: str - Success/error message
    
    Examples:
        "Show file.py with line numbers" → read_with_line_numbers(file_path="file.py")
        "Display lines 50-100 from log.txt with line numbers" → read_with_line_numbers(file_path="log.txt", start_line=50, end_line=100)
    """
    try:
        # First get the content without line numbers
        result = read_lines(file_path, start_line, end_line)
        
        if not result.get("success", False):
            return result
            
        # Add line numbers to each line
        lines = result.get("lines", [])
        line_count = len(lines)
        content_with_numbers = ""
        
        for i, line in enumerate(lines):
            line_num = start_line + i
            content_with_numbers += f"{line_num:4d} | {line}"
            
            # Add newline if not present and not the last line
            if not line.endswith('\n') and i < line_count - 1:
                content_with_numbers += '\n'
                
        # Update the result with the new content
        result["content"] = content_with_numbers
        return result
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"Error reading file with line numbers: {str(e)}"
        }


@mcp.tool()
def create_file(file_path: str, content: str) -> Dict[str, Union[bool, str]]:
    """
    Creates a new file or overwrites an existing file with specified content.
    
    Parameters:
        file_path: str - Absolute or relative path to the file
        content: str - Text content to write to the file
    
    Notes:
        - Creates parent directories if they don't exist
        - Overwrites file if it already exists without confirmation
        - Preserves the content string exactly, including newlines and whitespace
        - For appending instead of overwriting, use append_to_file
        - For inserting at specific line, use insert_at_line
        - WARNING: This function OVERWRITES existing files completely
    
    Returns:
        dict with keys:
        - success: bool - True if operation succeeded, False otherwise
        - path: str - Normalized absolute path to the file
        - message: str - Success/error message
        - error: str - Error type if operation failed
    
    Examples:
        "Create file notes.txt with content 'Meeting notes'" → create_file(file_path="notes.txt", content="Meeting notes")
        "Write 'Hello World' to ./output/greeting.txt" → create_file(file_path="./output/greeting.txt", content="Hello World")
    """
    try:
        path = normalize_path(file_path)
        
        # Ensure parent directory exists
        ensure_parent_directory(path)
        
        # Write content to file
        with open(path, 'w', encoding='utf-8') as file:
            file.write(content)
            
        return {
            "success": True,
            "path": path,
            "message": f"File written successfully: {path}"
        }
    except PermissionError:
        return {
            "success": False,
            "error": "Permission denied",
            "message": f"Cannot write to file due to permission issues: {path}. Please check file permissions."
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"Error writing to file: {str(e)}"
        }


@mcp.tool()
def append_to_file(file_path: str, content: str) -> Dict[str, Union[bool, str]]:
    """
    Appends content to the end of an existing file or creates new file with content.
    
    Parameters:
        file_path: str - Absolute or relative path to the file
        content: str - Text content to append to the file
    
    Notes:
        - Creates parent directories if they don't exist
        - Creates the file if it doesn't exist
        - Always appends content to the end, never overwrites existing content
        - Preserves the content string exactly, including newlines and whitespace
        - Use this instead of create_file when you want to add content to existing files
    
    Returns:
        dict with keys:
        - success: bool - True if operation succeeded, False otherwise
        - path: str - Normalized absolute path to the file
        - message: str - Success/error message
        - error: str - Error type if operation failed
    
    Examples:
        "Add 'New line' to end of log.txt" → append_to_file(file_path="log.txt", content="New line\n")
        "Append section to article.md" → append_to_file(file_path="article.md", content="\n\n## New Section\nContent here")
    """
    try:
        path = normalize_path(file_path)
        
        # Ensure parent directory exists
        ensure_parent_directory(path)
        
        # Append content to file
        with open(path, 'a', encoding='utf-8') as file:
            file.write(content)
            
        return {
            "success": True,
            "path": path,
            "message": f"Content appended successfully to: {path}"
        }
    except PermissionError:
        return {
            "success": False,
            "error": "Permission denied",
            "message": f"Cannot append to file due to permission issues: {path}. Please check file permissions."
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"Error appending to file: {str(e)}"
        }


@mcp.tool()
def insert_at_line(file_path: str, line_number: int, content: str) -> Dict[str, Union[bool, str, int]]:
    """
    Inserts content at a specific line number in a file.
    
    Parameters:
        file_path: str - Absolute or relative path to the file
        line_number: int - Line number to insert at (1-indexed)
        content: str - Text content to insert
    
    Notes:
        - Line numbers are 1-indexed (first line is 1, not 0)
        - Creates parent directories and file if they don't exist
        - If line_number exceeds file length, content is appended to end
        - If line_number exceeds file length with gap, empty lines are added
        - Existing lines are shifted down after insertion point
        - Automatically adds newline if content doesn't end with one
    
    Returns:
        dict with keys:
        - success: bool - True if operation succeeded, False otherwise
        - path: str - Normalized absolute path to the file
        - line_count: int - Total number of lines after insertion
        - message: str - Success/error message
        - error: str - Error type if operation failed
    
    Examples:
        "Insert header at line 1 of file.txt" → insert_at_line(file_path="file.txt", line_number=1, content="# Header")
        "Add comment at line 50" → insert_at_line(file_path="code.py", line_number=50, content="# Comment line")
    """
    try:
        path = normalize_path(file_path)
        
        # Check if line_number is valid
        if line_number < 1:
            return {
                "success": False,
                "error": "Invalid line number",
                "message": f"Line number must be at least 1, got {line_number}."
            }
            
        # Check if file exists
        file_exists = os.path.isfile(path)
        
        if not file_exists:
            # Create new file with content
            ensure_parent_directory(path)
            return create_file(path, content)
            
        # Read existing content
        with open(path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
            
        line_count = len(lines)
        
        # Ensure content ends with newline if not empty
        if content and not content.endswith('\n'):
            content += '\n'
            
        # Handle insertion
        if line_number > line_count + 1:
            # If line number is beyond the end with a gap, add empty lines
            for _ in range(line_count + 1, line_number):
                lines.append('\n')
            lines.append(content)
        elif line_number > line_count:
            # If the line number is just past the end, simply append
            lines.append(content)
        else:
            # Insert at the specified position
            lines.insert(line_number - 1, content)
            
        # Write back to file
        with open(path, 'w', encoding='utf-8') as file:
            file.writelines(lines)
            
        return {
            "success": True,
            "path": path,
            "line_count": len(lines),
            "message": f"Content inserted at line {line_number} in {path}"
        }
    except PermissionError:
        return {
            "success": False,
            "error": "Permission denied",
            "message": f"Cannot modify file due to permission issues: {path}. Please check file permissions."
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"Error inserting content at line: {str(e)}"
        }


@mcp.tool()
def delete_line(file_path: str, line_number: int) -> Dict[str, Union[bool, str, int]]:
    """
    Deletes a specific line from a file.
    
    Parameters:
        file_path: str - Absolute or relative path to the file
        line_number: int - Line number to delete (1-indexed)
    
    Notes:
        - Line numbers are 1-indexed (first line is 1, not 0)
        - File must exist, returns error if file not found
        - Returns error if line_number exceeds file length
        - Remaining lines maintain their relative positions after deletion
        - File is rewritten with the specified line removed
    
    Returns:
        dict with keys:
        - success: bool - True if operation succeeded, False otherwise
        - path: str - Normalized absolute path to the file
        - deleted_line: str - Content of the deleted line
        - new_line_count: int - Total number of lines after deletion
        - message: str - Success/error message
        - error: str - Error type if operation failed
    
    Examples:
        "Delete line 5 from config.txt" → delete_line(file_path="config.txt", line_number=5)
        "Remove first line from data.csv" → delete_line(file_path="data.csv", line_number=1)
    """
    try:
        path = normalize_path(file_path)
        
        # Check if file exists
        if not os.path.isfile(path):
            return {
                "success": False,
                "error": "File not found",
                "message": f"File does not exist: {path}. Please check the file path."
            }
            
        # Check if line_number is valid
        if line_number < 1:
            return {
                "success": False,
                "error": "Invalid line number",
                "message": f"Line number must be at least 1, got {line_number}."
            }
            
        # Read existing content
        with open(path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
            
        line_count = len(lines)
        
        # Check if line number is within range
        if line_number > line_count:
            return {
                "success": False,
                "error": "Invalid line number",
                "message": f"Line number ({line_number}) exceeds file length ({line_count})."
            }
            
        # Delete the specified line
        deleted_line = lines.pop(line_number - 1)
        
        # Write back to file
        with open(path, 'w', encoding='utf-8') as file:
            file.writelines(lines)
            
        return {
            "success": True,
            "path": path,
            "deleted_line": deleted_line,
            "new_line_count": len(lines),
            "message": f"Line {line_number} deleted from {path}"
        }
    except PermissionError:
        return {
            "success": False,
            "error": "Permission denied",
            "message": f"Cannot modify file due to permission issues: {path}. Please check file permissions."
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"Error deleting line: {str(e)}"
        }


@mcp.tool()
def list_directory(dir_path: str) -> Dict[str, Union[bool, str, List[str]]]:
    """
    Lists files and directories in the specified directory.
    
    Parameters:
        dir_path: str - Absolute or relative path to the directory
    
    Returns:
        dict with keys:
        - success: bool - True if operation succeeded
        - path: str - Normalized absolute path to the directory
        - files: list - List of file names in the directory
        - directories: list - List of subdirectory names
        - all_items: list - List of all items (files + directories)
        - message: str - Success/error message
    
    Examples:
        "List files in output directory" → list_directory(dir_path="output")
        "Show contents of /home/user/documents" → list_directory(dir_path="/home/user/documents")
    """
    try:
        path = normalize_path(dir_path)
        
        # Check if directory exists
        if not os.path.exists(path):
            return {
                "success": False,
                "error": "Directory not found",
                "message": f"Directory does not exist: {path}. Please check the directory path."
            }
        
        # Check if it's actually a directory
        if not os.path.isdir(path):
            return {
                "success": False,
                "error": "Not a directory",
                "message": f"Path exists but is not a directory: {path}. Use file operations for files."
            }
        
        # List directory contents
        all_items = os.listdir(path)
        files = []
        directories = []
        
        for item in all_items:
            item_path = os.path.join(path, item)
            if os.path.isfile(item_path):
                files.append(item)
            elif os.path.isdir(item_path):
                directories.append(item)
        
        return {
            "success": True,
            "path": path,
            "files": files,
            "directories": directories,
            "all_items": all_items,
            "message": f"Found {len(files)} files and {len(directories)} directories in {path}"
        }
    except PermissionError:
        return {
            "success": False,
            "error": "Permission denied",
            "message": f"Cannot access directory due to permission issues: {path}. Please check directory permissions."
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"Error listing directory: {str(e)}"
        }
    
if __name__ == "__main__":
    # Run the MCP server
    mcp.run(transport='stdio') 