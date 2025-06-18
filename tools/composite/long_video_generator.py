"""
Long Video Generator Tool - 长视频生成智能体

这个智能体能够：
1. 根据用户需求智能规划长视频内容结构
2. 将长视频分解为多个连贯的短视频场景
3. 调用ComfyUI生成各个场景的短视频片段
4. 使用视频处理工具将片段拼接成完整长视频
5. 提供高质量的视频输出和详细的生成报告

使用方式：
  python long_video_generator.py                        # MCP Server模式
  python long_video_generator.py --interactive          # 交互模式
  python long_video_generator.py --query "..."          # 单次查询模式
"""

import os
import sys

# Add the project root directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../..'))
sys.path.append(project_root)

# Import the FractFlow ToolTemplate
from FractFlow.tool_template import ToolTemplate


class LongVideoGenerator(ToolTemplate):
    """长视频生成智能体，协调多个工具创建连贯的长视频内容"""
    
    SYSTEM_PROMPT = """
你是长视频生成专家，能够创作连贯、高质量的长视频内容。

【内部规划流程】（内部完成，不输出给用户）
1. **需求分析**：理解用户的视频主题、时长要求、风格偏好
2. **故事分解**：将内容分解为3-8个连贯场景，每个场景2-4秒
3. **视觉描述**：为每个场景生成详细的英文提示词，确保风格一致性
4. **参数规划**：确定分辨率、帧率、过渡方式和输出质量

【强制执行流程】
第一阶段：批量生成短视频片段
1. 为每个场景调用image_creator_agent生成短视频
   - 使用统一的视频生成工作流
   - 确保各场景间的视觉连贯性
   - 保存到临时目录：output/long_video_generator/[项目名]/segments/
   - 文件命名：segment_001.mp4, segment_002.mp4 等

第二阶段：视频拼接合成  
2. 调用video_processor_agent拼接所有片段
   - 添加适当的过渡效果（淡入淡出）
   - 优化最终输出质量
   - 保存最终视频：output/long_video_generator/[项目名]/final_video.mp4

【文件管理规范】
- 项目目录：output/long_video_generator/[项目名]/
- 临时片段：segments/segment_[序号].mp4
- 最终输出：final_video.mp4
- 确保所有路径都正确传递给子工具

【质量控制要求】
- 场景描述必须英文，适合ComfyUI处理
- 保持视觉风格一致性（光线、色调、构图风格）
- 确保场景间逻辑连贯性和视觉流畅性
- 过渡效果要自然，不突兀

【工具调用规范】
- image_creator_agent：负责短视频生成
  - 必须指定完整的输出路径
  - 使用text_to_video工作流
  - 英文提示词描述场景内容
- video_processor_agent：负责视频拼接
  - 提供所有片段文件路径列表
  - 指定最终输出路径
  - 设置适当的过渡时长

【错误处理策略】
- 片段生成失败：重试或调整提示词
- 视频拼接失败：检查文件路径和格式
- 文件不存在：验证生成步骤是否成功
- 提供清晰的错误信息和解决建议

【输出报告格式】
生成完成后提供：
- 项目概要（主题、场景数量、总时长）
- 各场景描述和对应文件
- 最终视频文件路径和规格信息
- 生成过程中的关键参数和设置
"""
    
    TOOL_DESCRIPTION = """
长视频生成智能体，能够创作结构完整、视觉连贯的长视频内容。

# 核心功能
- 智能故事规划和场景分解
- 批量短视频片段生成
- 专业视频拼接和后处理
- 高质量长视频输出

# 输入格式
使用自然语言描述长视频需求：
- "生成一个关于[主题]的30秒视频，风格为[风格描述]"
- "创作[故事情节]的视频，包含[场景要求]"
- "制作[产品/概念]的展示视频，时长约[时间]"

# 生成流程
1. 内容规划：分析需求，规划场景结构
2. 片段生成：使用ComfyUI生成各场景短视频
3. 专业拼接：使用视频处理工具进行合成
4. 质量优化：确保输出符合专业标准

# 返回信息
- project_summary: 项目概要和规格信息
- scene_details: 各场景的详细描述
- output_files: 生成的文件路径（片段+最终视频）
- generation_stats: 生成统计和质量指标
- success: 整体生成成功状态
"""
    
    TOOLS = [
        ("tools/core/file_io/file_io_mcp.py", "file_manager_agent"),
        ("tools/core/comfyui/comfyui_agent.py", "image_creator_agent"),
        ("tools/core/video_processor/video_processor_agent.py", "video_processor_agent")
    ]
    
    MCP_SERVER_NAME = "long_video_generator"
    
    @classmethod
    def create_config(cls):
        """为长视频生成器创建自定义配置"""
        from FractFlow.infra.config import ConfigManager
        from dotenv import load_dotenv
        
        load_dotenv()
        return ConfigManager(
            provider='deepseek',
            deepseek_model='deepseek-chat',
            max_iterations=30,  # 长视频生成需要多个步骤
            custom_system_prompt=cls.SYSTEM_PROMPT,
            tool_calling_version='stable'
        )


if __name__ == "__main__":
    LongVideoGenerator.main() 