"""
Video Processor Agent - 智能视频处理工具

这个代理能够：
1. 理解用户的视频处理需求
2. 执行视频拼接、格式转换、质量优化等操作
3. 提供详细的处理结果和文件路径
4. 处理各种视频格式和质量要求

使用方式：
  python video_processor_agent.py                    # MCP Server模式
  python video_processor_agent.py --interactive      # 交互模式
  python video_processor_agent.py --query "..."      # 单次查询模式
"""

import os
import sys

# Add the project root directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../../..'))
sys.path.append(project_root)

# Import the FractFlow ToolTemplate
from FractFlow.tool_template import ToolTemplate


class VideoProcessorAgent(ToolTemplate):
    """视频处理智能代理，基于ToolTemplate的专业视频处理系统"""
    
    SYSTEM_PROMPT = """
你是专业的视频处理专家，专门帮助用户进行各种视频处理操作。

# 核心功能
1. **视频拼接**: 将多个视频文件合并为一个连续的视频
2. **过渡效果**: 为视频添加淡入淡出等过渡效果
3. **格式转换**: 转换视频格式（MP4、AVI、MOV、WebM等）
4. **质量优化**: 压缩视频大小或提升质量

# 工作流程
1. **需求分析**: 理解用户的视频处理需求
2. **参数准备**: 确定输入文件、输出路径和处理参数
3. **执行处理**: 调用相应的视频处理工具
4. **结果报告**: 提供详细的处理结果和文件信息

# 处理原则
- **文件验证**: 确保所有输入文件存在且可访问
- **路径规范**: 自动创建输出目录，规范化文件路径
- **质量保证**: 使用合适的编码参数确保输出质量
- **错误处理**: 提供清晰的错误信息和解决建议

# 常见操作指南

## 视频拼接
- 支持多个视频文件的顺序拼接
- 可添加过渡效果（淡入淡出）
- 自动处理分辨率和帧率差异

## 格式转换
- 支持主流视频格式间的转换
- 提供高中低三种质量档位
- 保持音频和字幕信息

## 质量优化
- 根据目标大小自动调整比特率
- 智能压缩算法减少文件大小
- 保持视觉质量和播放流畅度

# 输出格式
处理完成后，提供：
- 操作结果摘要
- 输出文件路径
- 文件大小和质量信息
- 处理时间和压缩比例（如适用）

# 错误处理
- 文件不存在：提供具体的缺失文件信息
- 格式不支持：建议支持的格式列表
- 处理失败：提供故障排除建议和替代方案
"""
    
    TOOL_DESCRIPTION = """
智能视频处理工具，提供专业的视频编辑和格式转换服务。

# 主要功能
- 视频拼接与合并
- 过渡效果处理
- 格式转换与优化
- 质量控制与压缩

# 输入格式
使用自然语言描述视频处理需求，支持：
- "将这些视频拼接成一个文件：[文件路径列表]，输出到：[目标路径]"
- "转换视频格式：从[输入路径]转换为MP4格式，保存到[输出路径]"
- "优化视频质量：压缩[输入路径]到50MB以下，输出[目标路径]"
- "添加过渡效果：为[视频列表]添加淡入淡出效果"

# 返回格式
- operation_result: 处理操作的详细描述
- output_files: 生成的文件路径列表
- file_info: 文件大小、格式、质量等信息
- processing_time: 处理耗时
- success: 操作成功状态
"""
    
    TOOLS = [
        ("tools/core/file_io/file_io_agent.py", "file_manager_agent"),
        ("tools/core/video_processor/video_processor_mcp.py", "video_processor")
    ]
    
    MCP_SERVER_NAME = "video_processor_agent"
    
    @classmethod
    def create_config(cls):
        """为视频处理代理创建自定义配置"""
        from FractFlow.infra.config import ConfigManager
        from dotenv import load_dotenv
        
        load_dotenv()
        return ConfigManager(
            provider='deepseek',
            deepseek_model='deepseek-chat',
            max_iterations=8,  # 视频处理可能需要多步操作
            custom_system_prompt=cls.SYSTEM_PROMPT,
            tool_calling_version='stable'
        )


if __name__ == "__main__":
    VideoProcessorAgent.main() 