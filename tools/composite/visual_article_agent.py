"""
Visual Article Generator Tool - Unified Interface

This module provides a unified interface for visual article generation that can run in multiple modes:
1. MCP Server mode (default): Provides AI-enhanced visual article generation as MCP tools
2. Interactive mode: Runs as an interactive agent with visual article capabilities
3. Single query mode: Processes a single query and exits

Usage:
  python visual_article_tool.py                        # MCP Server mode (default)
  python visual_article_tool.py --interactive          # Interactive mode
  python visual_article_tool.py --query "..."          # Single query mode
"""

import os
import sys

# Add the project root directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../..'))
sys.path.append(project_root)

# Import the FractFlow ToolTemplate
from FractFlow.tool_template import ToolTemplate

class VisualArticleTool(ToolTemplate):
    """Visual article generator tool using ToolTemplate with fractal intelligence"""
    
    SYSTEM_PROMPT = """
你是一个图文并茂的文章生成智能体。

【严格约束】
❌ 绝对禁止：在对话中直接输出或显示任何文章内容
❌ 绝对禁止：使用代码块显示文章文本
❌ 绝对禁止：使用任何占位符，包括但不限于：
   - "（后续内容...）"
   - "此处省略"
   - "...等详细描写"
   - "约XXX字"
   - 任何形式的省略或概述
✅ 必须执行：所有内容必须通过工具调用完成
✅ 必须执行：写出完整的故事内容，包含具体对话、情节、描写

【文章长度要求】
- 如果用户指定了字数要求，必须严格达到该字数要求
- 文章总字数 = 用户要求字数，需要合理分配到各个章节
- 每个章节必须完整写出，绝对禁止使用任何占位符、省略号或"此处省略"等表述
- 内容必须丰富、有情节发展、有细节描写
- 必须写出完整的对话、心理描写、环境描述等具体内容

【强制工具调用流程】
1. 规划文章结构（内部完成，不输出内容）
   - 根据字数要求确定章节数量和每章节字数分配
   - 确保总字数达到用户要求
2. 按顺序处理每个章节：
   a) 调用 file_manager_agent 写入完整章节内容到 article.md
      - 章节内容必须详细完整，达到分配的字数
      - 包含图片引用：![说明](images/sectionX-figY.png)
      - 内容要有具体情节、对话、心理描述、环境描写等
      - 先预留图片位置，内容写在图片引用之后
      - 严禁使用"（后续内容...）"、"此处省略"等任何占位符
      - 必须写出真实完整的故事内容，而不是描述性说明
   b) 调用 image_creator_agent 生成对应插图
      - 必须指定图片保存路径：output/visual_article_generator/[项目名]/images/sectionX-figY.png
      - 确保路径参数准确传递给图片生成器
   c) 确认操作成功后继续下一章节

【内容创作标准】
- 必须创作真实完整的故事内容，而非摘要或概述
- 每个章节要包含完整的场景、对话、动作描写
- 人物心理活动要详细具体，环境描写要生动
- 绝对禁止任何形式的占位符或省略表述
- 情节发展要自然流畅，有起承转合
- 对话要符合人物性格，推动剧情发展

【工具使用规范】
- file_manager_agent：专门用于文件写入操作
- image_creator_agent：专门用于图片生成操作
  - 必须传递图片保存路径参数
  - 路径格式：output/visual_article_generator/[项目名]/images/sectionX-figY.png
  - 确保图片保存到指定位置

【文件路径规范】
- 文章路径：output/visual_article_generator/[项目名]/article.md
- 图片路径：output/visual_article_generator/[项目名]/images/sectionX-figY.png
- 图片引用：![说明](images/sectionX-figY.png)

【操作验证】
每次工具调用后必须确认：
- file_manager_agent：文件是否成功创建/写入，并检查字数是否达到要求
- image_creator_agent：图片是否成功生成

【错误处理】
如果工具调用失败：
1. 报告具体的工具和错误信息
2. 尝试修正参数
3. 重新调用相应工具

"""
    
    # 分形智能体：调用其他智能体
    TOOLS = [
        ("tools/core/file_io/file_io_mcp.py", "file_manager_agent"),
        ("tools/core/gpt_imagen/gpt_imagen_mcp.py", "image_creator_agent")
        # ("tools/core/comfyui/comfyui_agent.py", "image_creator_agent")
    ]
    
    MCP_SERVER_NAME = "visual_article_tool"
    
    TOOL_DESCRIPTION = """
    Generates comprehensive visual articles with integrated text and images in Markdown format.

This tool creates complete articles by coordinating file operations and image generation. It writes structured Markdown content and automatically generates relevant images for each section, creating a cohesive visual narrative.

Input format:
- Natural language description of the article topic and requirements
- Can specify writing style, target audience, or content focus
- May include specific image requirements or visual themes
- Can request specific article structure or section organization


    """
    
    @classmethod
    def create_config(cls):
        """Custom configuration for Visual Article tool"""
        from FractFlow.infra.config import ConfigManager
        from dotenv import load_dotenv
        
        load_dotenv()
        return ConfigManager(
            provider='deepseek',
            deepseek_model='deepseek-chat',
            max_iterations=50,  # Visual article generation requires many steps
            custom_system_prompt=cls.SYSTEM_PROMPT,
            tool_calling_version='stable'
        )

if __name__ == "__main__":
    VisualArticleTool.main() 