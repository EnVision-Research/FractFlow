"""
ComfyUI Workflow Agent - 智能工作流选择和执行系统

这个代理能够：
1. 理解用户的图像生成需求
2. 自动选择最合适的ComfyUI工作流
3. 智能填充参数并执行工作流
4. 提供详细的执行结果和文件路径

使用方式：
  python comfyui_agent.py                           # MCP Server模式
  python comfyui_agent.py --interactive             # 交互模式  
  python comfyui_agent.py --query "生成一张猫的图片"    # 单次查询模式
"""

import os
import sys

# Add the project root directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../../..'))
sys.path.append(project_root)

# Import the FractFlow ToolTemplate
from FractFlow.tool_template import ToolTemplate


class ComfyUIWorkflowAgent(ToolTemplate):
    """ComfyUI工作流智能代理，基于ToolTemplate的自动化工作流执行系统"""
    
    SYSTEM_PROMPT = """
你是ComfyUI工作流执行专家，专门帮助用户通过最合适的工作流生成图像、视频和其他创意内容。

# 工作流程
1. **需求分析**: 当用户描述他们的需求时，首先理解他们想要什么类型的内容
2. **工作流发现**: 调用list_comfyui_workflows()查看所有可用的工作流选项
3. **智能选择**: 根据用户需求和工作流文档，选择最合适的工作流
4. **参数准备**: 根据工作流要求，收集和准备所需参数
5. **执行工作流**: 调用execute_comfyui_workflow()执行生成任务
6. **结果报告**: 提供详细的执行结果，包括生成的文件路径

# 关键原则
- **始终先查询**: 每次处理用户需求前，先调用list_comfyui_workflows()了解可用选项
- **智能匹配**: 根据工作流的"use_when"字段和描述，选择最符合用户需求的工作流
- **参数优化**: 为用户提供合理的默认参数，同时允许自定义
- **错误处理**: 如果工作流执行失败，提供清晰的错误说明和建议

# 常见场景判断
- 用户只提供文字描述 → 选择text_to_image类工作流
- 用户提供参考图片 → 选择image_to_image类工作流  
- 用户需要特定风格控制 → 选择controlnet类工作流
- 用户需要视频内容 → 选择video_generation类工作流

# 参数处理策略
- **必需参数**: 如果用户未提供，主动询问
- **可选参数**: 使用工作流定义的默认值
- **路径参数**: 自动规范化和验证路径
- **质量参数**: 根据用户需求推荐合适的质量设置

# 输出格式
- 清楚说明选择了哪个工作流及原因
- 列出使用的主要参数
- 提供生成文件的完整路径
- 给出后续使用建议

# 错误恢复
- 如果工作流不存在，列出可用选项
- 如果参数错误，解释正确的参数格式
- 如果执行失败，提供故障排除建议
"""
    
    TOOL_DESCRIPTION = """
ComfyUI智能工作流执行系统，能够自动选择和执行最合适的图像生成工作流。

# 核心功能
- 自动工作流发现和选择
- 智能参数填充和验证
- 多种输出类型支持（图像、视频、音频等）
- 详细的执行报告和文件管理

# 输入格式
用自然语言生成需求和保存路径。
- 生成一只猪，保存在 "output/comfyui/text_to_image/20250617_100000.png"
"""
    
    TOOLS = [
        ("tools/core/comfyui/comfyui_mcp.py", "comfyui_workflows")
    ]
    
    MCP_SERVER_NAME = "comfyui_workflow_agent"
    
    @classmethod
    def create_config(cls):
        """为ComfyUI代理创建自定义配置"""
        from FractFlow.infra.config import ConfigManager
        from dotenv import load_dotenv
        
        load_dotenv()
        return ConfigManager(
            provider='deepseek',
            deepseek_model='deepseek-chat',
            max_iterations=10,  # 足够处理工作流选择和执行
            custom_system_prompt=cls.SYSTEM_PROMPT,
            tool_calling_version='stable'
        )


if __name__ == "__main__":
    ComfyUIWorkflowAgent.main() 