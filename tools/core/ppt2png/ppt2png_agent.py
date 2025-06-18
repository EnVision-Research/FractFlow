import os
import sys

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../../..'))
sys.path.append(project_root)

from FractFlow.tool_template import ToolTemplate

class PPT2PNGAgent(ToolTemplate):
    """PPT转PNG转换工具"""
    
    SYSTEM_PROMPT = """
你是一个专业的PPT转换助手，使用LibreOffice将PowerPoint演示文稿转换为PNG图片序列。

# 核心能力
- 将PPT、PPTX、ODP文件转换为高质量PNG图片
- 自动检测并安装必要的系统依赖（LibreOffice）
- 智能文件命名和目录管理
- 支持批量转换和自定义输出格式
- 提供详细的转换状态和错误诊断

# 工作流程
1. 验证输入文件存在且格式受支持
2. 检查LibreOffice可用性状态
3. 创建输出目录并执行转换
4. 重命名文件为统一格式（slide_1.png, slide_2.png等）
5. 返回详细的转换报告

# 参数说明
- input_path: PPT文件路径（必需）
- output_dir: 输出目录（可选，默认自动创建）
- output_format: 输出格式（默认png，也支持jpg等）
- keep_original_names: 是否保留原始文件名（默认false）

# 错误处理
- 自动检测LibreOffice安装状态
- 提供清晰的错误信息和解决建议
- 支持权限和路径问题诊断

始终提供详细的转换状态反馈，包括生成的文件列表和大小信息。
"""
    
    TOOLS = [
        ("tools/core/ppt2png/ppt2png_mcp.py", "ppt_converter")
    ]
    
    MCP_SERVER_NAME = "ppt2png_agent"
    
    TOOL_DESCRIPTION = """
将PowerPoint演示文稿转换为PNG图片序列的专业工具。

# 输入格式
直接描述你的转换需求，例如：
- "转换presentation.pptx为图片"
- "把这个PPT文件转为PNG：/path/to/file.pptx"
- "转换PPT到指定目录：input=/path/to/slides.pptx output=/path/to/images/"

# 返回信息
- 转换状态和成功/失败信息
- 生成的图片文件完整路径列表
- 每个文件的大小和质量信息
- 转换过程中的详细日志

# 支持格式
输入：.ppt, .pptx, .odp
输出：png, jpg等图片格式

# 系统要求
需要安装LibreOffice，工具会自动检测并提供安装指导。
"""
    
    @classmethod
    def create_config(cls):
        """自定义配置"""
        from FractFlow.infra.config import ConfigManager
        from dotenv import load_dotenv
        
        load_dotenv()
        return ConfigManager(
            provider='siliconflow',
            siliconflow_model='Qwen/Qwen3-30B-A3B',
            max_iterations=5,
            custom_system_prompt=cls.SYSTEM_PROMPT,
            tool_calling_version='stable'
            # provider='deepseek',
            # deepseek_model='deepseek-chat',
            # max_iterations=5,
            # custom_system_prompt=cls.SYSTEM_PROMPT,
            # tool_calling_version='stable'
        )

if __name__ == "__main__":
    PPT2PNGAgent.main()