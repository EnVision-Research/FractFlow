"""
PPT to PNG conversion tool provider.

Provides tools for converting PowerPoint presentations to PNG image sequences.
Uses a two-step process: PPT → PDF → PNG to ensure all slides are converted.
"""

import subprocess
import os
import glob
import time
from typing import Dict, List, Union, Optional
from mcp.server.fastmcp import FastMCP

# Try to import pdf2image for PDF to PNG conversion
try:
    from pdf2image import convert_from_path
    PDF2IMAGE_AVAILABLE = True
except ImportError:
    PDF2IMAGE_AVAILABLE = False

# Initialize FastMCP server
mcp = FastMCP("ppt2png")

def normalize_path(path: str) -> str:
    """
    Normalize a file path to prevent path traversal attacks and handle relative paths.
    
    Args:
        path: The file path to normalize
        
    Returns:
        Normalized absolute file path
    """
    # Expand ~ to user's home directory
    expanded_path = os.path.expanduser(path)
    
    # Convert to absolute path if relative
    if not os.path.isabs(expanded_path):
        expanded_path = os.path.abspath(expanded_path)
        
    return expanded_path

def ensure_directory_exists(directory: str) -> None:
    """
    Ensure that a directory exists, create it if it doesn't.
    
    Args:
        directory: The directory path to ensure exists
    """
    if directory and not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)

def check_libreoffice_available() -> bool:
    """
    Check if LibreOffice is available in the system.
    
    Returns:
        True if LibreOffice is available, False otherwise
    """
    try:
        result = subprocess.run(
            ["soffice", "--version"], 
            capture_output=True, 
            text=True, 
            timeout=10
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False

def check_dependencies() -> tuple[bool, str]:
    """
    Check if all required dependencies are available.
    
    Returns:
        tuple: (dependencies_available, error_message)
    """
    # Check LibreOffice
    if not check_libreoffice_available():
        return False, "LibreOffice未安装。请安装LibreOffice: brew install --cask libreoffice (macOS) 或 sudo apt-get install libreoffice (Ubuntu)"
    
    # Check pdf2image
    if not PDF2IMAGE_AVAILABLE:
        return False, "pdf2image库未安装。请安装: pip install pdf2image。注意：还需要安装poppler: brew install poppler (macOS) 或 sudo apt-get install poppler-utils (Ubuntu)"
    
    return True, ""

@mcp.tool()
def convert_ppt_to_images(
    input_path: str, 
    output_dir: str = "", 
    output_format: str = "png",
    dpi: int = 200,
    save_path: str = ""
) -> str:
    """
    将PPT的所有页面转换为图片文件。
    
    使用两步转换过程：PPT → PDF → PNG，确保转换所有幻灯片页面。
    
    Args:
        input_path (str): PPT文件的路径（支持相对路径和绝对路径）
        output_dir (str): 图片输出目录路径（可选，默认在输入文件同目录下创建）
        output_format (str): 输出图片格式（目前支持png和jpg，默认png）
        dpi (int): 输出图片的DPI分辨率（默认200，范围100-300）
        save_path (str): 自定义保存路径（可选，会覆盖output_dir设置）
    
    Returns:
        str: 转换结果详情，包含生成的文件列表和状态信息
        
    Examples:
        "转换presentation.pptx为图片" → convert_ppt_to_images(input_path="presentation.pptx")
        "转换PPT到指定目录" → convert_ppt_to_images(input_path="test.pptx", save_path="/path/to/images/")
    """
    try:
        # 检查所有依赖
        deps_ok, error_msg = check_dependencies()
        if not deps_ok:
            return f"错误：依赖检查失败。{error_msg}"
        
        # 规范化输入路径
        input_path = normalize_path(input_path)
        
        # 检查输入文件是否存在
        if not os.path.isfile(input_path):
            return f"错误：输入文件不存在: {input_path}"
        
        # 检查文件扩展名
        file_ext = os.path.splitext(input_path)[1].lower()
        if file_ext not in ['.ppt', '.pptx', '.odp']:
            return f"错误：不支持的文件格式: {file_ext}。支持的格式: .ppt, .pptx, .odp"
        
        # 确定输出目录（优先使用save_path）
        if save_path.strip():
            output_dir = normalize_path(save_path)
        elif output_dir.strip():
            output_dir = normalize_path(output_dir)
        else:
            input_dir = os.path.dirname(input_path)
            input_name = os.path.splitext(os.path.basename(input_path))[0]
            output_dir = os.path.join(input_dir, f"{input_name}_images")
        
        # 确保输出目录存在
        ensure_directory_exists(output_dir)
        
        # 获取输入文件的基础名称（不含扩展名）
        input_name = os.path.splitext(os.path.basename(input_path))[0]
        
        # 第一步：PPT转PDF
        temp_dir = os.path.join(output_dir, "temp_pdf")
        ensure_directory_exists(temp_dir)
        
        pdf_cmd = [
            "soffice",
            "--headless",
            "--nologo",
            "--convert-to", "pdf",
            "--outdir", temp_dir,
            input_path
        ]
        
        # 执行PPT转PDF命令
        result = subprocess.run(pdf_cmd, capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            error_msg = result.stderr.strip() if result.stderr.strip() else "未知转换错误"
            return f"PPT转PDF失败: {error_msg}"
        
        # 等待PDF文件生成
        time.sleep(1.0)
        
        # 查找生成的PDF文件
        pdf_pattern = os.path.join(temp_dir, f"{input_name}.pdf")
        if not os.path.exists(pdf_pattern):
            # 尝试查找任何PDF文件
            pdf_files = glob.glob(os.path.join(temp_dir, "*.pdf"))
            if not pdf_files:
                return "错误：PDF文件生成失败"
            pdf_path = pdf_files[0]
        else:
            pdf_path = pdf_pattern
        
        # 第二步：PDF转PNG
        try:
            # 验证DPI范围
            dpi = max(100, min(300, dpi))
            
            # 使用pdf2image转换PDF为图片
            images = convert_from_path(pdf_path, dpi=dpi, fmt=output_format.upper())
            
            if not images:
                return "错误：PDF转图片失败，未生成任何图片"
            
            # 保存每一页为单独的图片文件
            final_files = []
            for i, image in enumerate(images, 1):
                filename = f"slide_{i}.{output_format}"
                filepath = os.path.join(output_dir, filename)
                
                # 保存图片
                if output_format.lower() == 'png':
                    image.save(filepath, 'PNG')
                elif output_format.lower() in ['jpg', 'jpeg']:
                    # 对于JPEG格式，转换为RGB模式
                    rgb_image = image.convert('RGB')
                    rgb_image.save(filepath, 'JPEG', quality=95)
                else:
                    image.save(filepath)
                
                final_files.append(filepath)
            
            # 清理临时PDF文件和目录
            try:
                os.remove(pdf_path)
                os.rmdir(temp_dir)
            except:
                pass  # 忽略清理错误
            
            # 生成详细的结果报告
            result_summary = f"""PPT转换成功完成！

转换方式: PPT → PDF → {output_format.upper()}
输入文件: {input_path}
输出目录: {output_dir}
图片格式: {output_format.upper()}
图片分辨率: {dpi} DPI
生成文件数: {len(final_files)}

生成的图片文件:"""
            
            for i, file_path in enumerate(final_files, 1):
                file_size = os.path.getsize(file_path)
                size_kb = file_size / 1024
                result_summary += f"\n  {i}. {os.path.basename(file_path)} ({size_kb:.1f} KB)"
            
            result_summary += f"\n\n所有文件已保存到: {output_dir}"
            
            return result_summary
            
        except Exception as e:
            return f"PDF转图片失败: {str(e)}"
        
    except subprocess.TimeoutExpired:
        return "错误：PPT转换超时。文件可能过大或包含复杂内容，请尝试较小的文件。"
    except PermissionError:
        return f"错误：权限不足。无法访问文件或创建输出目录: {output_dir}"
    except Exception as e:
        return f"转换过程中发生错误: {str(e)}"

@mcp.tool()
def get_ppt_info(input_path: str) -> str:
    """
    获取PPT文件的基本信息和系统依赖状态，不进行转换。
    
    Args:
        input_path (str): PPT文件的路径
    
    Returns:
        str: PPT文件的基本信息和系统状态
    """
    try:
        # 规范化输入路径
        input_path = normalize_path(input_path)
        
        # 检查文件是否存在
        if not os.path.isfile(input_path):
            return f"错误：文件不存在: {input_path}"
        
        # 获取文件信息
        file_size = os.path.getsize(input_path)
        size_mb = file_size / (1024 * 1024)
        file_ext = os.path.splitext(input_path)[1].lower()
        
        # 检查是否为支持的格式
        supported_formats = ['.ppt', '.pptx', '.odp']
        is_supported = file_ext in supported_formats
        
        # 检查系统依赖
        deps_ok, deps_msg = check_dependencies()
        libreoffice_status = "✓ 可用" if check_libreoffice_available() else "✗ 未安装"
        pdf2image_status = "✓ 可用" if PDF2IMAGE_AVAILABLE else "✗ 未安装"
        
        info = f"""PPT文件信息:

文件路径: {input_path}
文件名: {os.path.basename(input_path)}
文件大小: {size_mb:.2f} MB ({file_size:,} 字节)
文件格式: {file_ext}
格式支持: {'✓ 支持' if is_supported else '✗ 不支持'}

系统依赖状态:
├─ LibreOffice: {libreoffice_status}
├─ pdf2image: {pdf2image_status}
└─ 整体状态: {'✓ 就绪' if deps_ok else '✗ 依赖缺失'}

支持的格式: {', '.join(supported_formats)}
转换流程: PPT → PDF → PNG (两步转换，确保所有页面)"""

        if is_supported and deps_ok:
            info += "\n\n✅ 该文件可以正常转换为图片。"
        elif not is_supported:
            info += f"\n\n⚠️  警告：{file_ext} 格式不受支持，无法转换。"
        elif not deps_ok:
            info += f"\n\n⚠️  警告：{deps_msg}"
            
        return info
        
    except Exception as e:
        return f"获取文件信息时发生错误: {str(e)}"

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')
