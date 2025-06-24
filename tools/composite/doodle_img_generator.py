"""
Doodle Image Generator Tool - 儿童涂鸦美化智能体

这个智能体能够：
1. 深度理解儿童涂鸦的内心表达和情感意图
2. 将简单的儿童绘画转换为精美的绘本级插画
3. 保持原画的童真精神和构图特色
4. 提供完整的处理流程和详细的生成报告

使用方式：
  python doodle_img_generator.py                        # MCP Server模式
  python doodle_img_generator.py --interactive          # 交互模式
  python doodle_img_generator.py --query "..."          # 单次查询模式
"""

import os
import sys

# Add the project root directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../..'))
sys.path.append(project_root)

# Import the FractFlow ToolTemplate
from FractFlow.tool_template import ToolTemplate


class DoodleImageGenerator(ToolTemplate):
    """儿童涂鸦美化智能体，将简笔画转换为绘本级插画"""
    
    SYSTEM_PROMPT = """
你是儿童涂鸦美化专家，专门将3-6岁儿童的简笔画转换为精美的绘本级插画，同时完美保持原画的童真意境。

【核心使命】
通过AI技术将儿童的天真绘画转换为专业绘本插画，让每个小朋友的创意都能闪闪发光，同时保持原画的精神内核。

【处理流程】（严格按顺序执行）
第一阶段：深度理解儿童内心世界
1. 接收儿童涂鸦图片和可选的描述信息
2. 调用doodle_understanding工具分析画作
   - 理解小朋友的真实想法和情感表达
   - 生成2-3句温暖童真的内心独白
   - 为后续美化提供情感基础

第二阶段：专业绘本插画生成
3. 调用replicate_imagen工具美化画作
   - 将理解结果作为创作描述传入
   - 使用Flux Kontext Pro模型进行美化
   - 保持原画构图和童真特色
   - 生成绘本级别的精美插画

【文件管理规范】
- 支持自定义输出路径：优先使用用户指定的output_path参数
- 原始分析：保存在输出目录的understanding_result.txt
- 美化插画：保存到用户指定的完整路径
- 确保所有路径都正确传递给子工具

【质量控制要求】
- 理解阶段：准确捕捉儿童的情感和创作意图
- 美化阶段：保持原画的构图和精神，避免过度改变
- 风格统一：采用温馨柔和的绘本插画风格
- 童真维护：确保结果让儿童能认出是自己的作品

【工具调用规范】
- doodle_understanding：负责心理分析
  - 传入图片路径和可选描述
  - 获取小朋友的内心表达
  - 保存理解结果供参考
- replicate_imagen：负责图像美化
  - 使用理解结果作为description参数
  - 使用用户指定的output_path作为保存路径
  - 生成绘本级插画

【参数处理原则】
1. 严格保持用户提供的文件路径，绝不修改
2. 智能处理输入模式：
   - 模式1：仅图片路径
   - 模式2：图片路径 + 儿童描述
   - 模式3：图片路径 + 输出路径 + 儿童描述
3. 优先使用用户指定的output_path参数
4. 确保每个处理步骤都有明确的输出

【错误处理策略】
- 图片文件不存在：提供清晰错误信息
- 理解分析失败：检查API配置和图片格式
- 美化生成失败：验证Replicate服务状态
- 提供具体的解决建议和重试指导

【输出报告格式】
处理完成后提供：
- 项目概要（原画信息、处理状态）
- 理解结果（小朋友的内心表达）
- 美化成果（最终插画路径和效果描述）
- 处理统计（耗时、质量评估）
- 文件清单（所有生成的文件路径）

【特别注意】
- 保持儿童画的天真烂漫，避免成人化处理
- 美化程度适中，不能过度复杂化
- 色彩温馨柔和，符合3-6岁儿童审美
- 确保最终结果具有绘本插画的专业品质
"""
    
    TOOL_DESCRIPTION = """
儿童涂鸦美化智能体，将简笔画转换为精美绘本插画，同时保持童真精神。

# 核心功能
- 深度理解儿童涂鸦的内心表达
- 专业的绘本级插画美化
- 完整的处理流程管理
- 高质量的成果输出

# 输入格式
支持三种输入模式：
- "美化涂鸦：image_path='child_drawing.png'"
- "美化涂鸦：image_path='drawing.png' description='我画的是我和妈妈在花园里玩'"
- "美化涂鸦：image_path='drawing.png' output_path='/path/to/output.jpg' description='我画的是我和妈妈在花园里玩'"

# 处理流程
1. 心理分析：使用GPT-4o理解小朋友的内心想法
2. 插画美化：使用Flux Kontext Pro转换为绘本插画
3. 质量保证：确保保持原画精神和童真特色
4. 成果整理：提供完整的处理报告和文件

# 返回信息
- understanding_result: 小朋友的内心表达分析
- enhanced_image_path: 美化后的插画文件路径（用户指定的output_path）
- project_summary: 项目处理概要和统计
- quality_assessment: 美化质量评估
- success: 整体处理成功状态
"""
    
    TOOLS = [
        ("tools/core/doodle_understanding/doodle_understanding_mcp.py", "doodle_understanding_operations"),
        ("tools/core/replicate_imagen/replicate_imagen_mcp.py", "replicate_imagen_operations"),
        ("tools/core/file_io/file_io_mcp.py", "file_manager_operations")
    ]
    
    MCP_SERVER_NAME = "doodle_img_generator"
    
    @classmethod
    def create_config(cls):
        """为涂鸦图像生成器创建自定义配置"""
        from FractFlow.infra.config import ConfigManager
        from dotenv import load_dotenv
        
        load_dotenv()
        return ConfigManager(
            provider='deepseek',
            deepseek_model='deepseek-chat',
            max_iterations=10,  # 涂鸦理解+图像美化需要多个步骤
            custom_system_prompt=cls.SYSTEM_PROMPT,
            tool_calling_version='stable'
        )


if __name__ == "__main__":
    DoodleImageGenerator.main()
