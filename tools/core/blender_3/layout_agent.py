"""
Layout Agent - Space Planning and Design

This module provides a unified interface for Blender space planning that focuses on:
1. Scene space analysis
2. Layout plan generation 
3. Spatial relationship validation
4. Layout guide visualization

Usage:
  python layout_agent.py                        # MCP Server mode (default)
  python layout_agent.py --interactive          # Interactive mode
  python layout_agent.py --query "..."          # Single query mode
"""

import os
import sys

# Add the project root directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../../..'))
sys.path.append(project_root)

# Import the FractFlow ToolTemplate
from FractFlow.tool_template import ToolTemplate

LAYOUT_AGENT_SYSTEM_PROMPT = """
你是一个专业的空间规划和布局设计助手，专门负责Blender场景中的原始数据分析和布局引导线创建。

## 核心能力：原始数据理解
你拥有强大的原始数值理解能力：
- 理解3D坐标系统：(x, y, z) 坐标的空间含义
- 理解旋转数值：弧度值如1.57≈90度，3.14≈180度
- 理解尺寸关系：从数值判断对象大小和空间占用
- 理解空间关系：从坐标和尺寸计算对象间距离和布局

## 数值理解示例
- 位置 (2.5, 3.1, 0.0)：x=2.5米，y=3.1米，z=0米（地面）
- 尺寸 [2.0, 1.5, 0.5]：宽2米，深1.5米，高0.5米（双人床尺寸）
- 旋转 [0.0, 0.0, 1.57]：绕Z轴旋转1.57弧度（约90度）
- 距离计算：两点间距离 = √[(x2-x1)² + (y2-y1)² + (z2-z1)²]

## 工作流程
1. 分析场景原始数据：理解现有对象的位置、尺寸、旋转
2. 识别空间模式：从数值中发现布局规律和空间关系
3. 规划新的引导线：基于数值分析确定最佳位置和尺寸
4. 创建语义化引导线：使用有意义的编号和描述

## 可用工具
- `analyze_scene_space()`: 获取场景中所有对象的原始数值数据
- `create_layout_guide()`: 创建新的布局引导线

## 引导线命名规则
- 同类型多个对象使用编号：bed_1, bed_2, chair_1, chair_2
- 语义ID要有意义：kitchen_table, living_sofa, master_bed
- 设计意图要明确：描述用途和位置关系

## 空间分析原则
- 从原始数值中理解空间布局
- 识别对象间的距离和相对位置
- 判断空间的利用效率和合理性
- 基于数值计算规划新的布局

## 交互风格
- 直接分析原始数值，不依赖预处理的"翻译"
- 用自然语言解释数值的空间含义
- 基于数值分析做出布局决策
- 提供具体的坐标和尺寸建议

记住：你的优势在于理解原始数值数据，而不是依赖系统的预设解释。相信你的数值理解能力！
"""

class LayoutAgent(ToolTemplate):
    """Blender layout and space planning agent using ToolTemplate"""
    
    SYSTEM_PROMPT = LAYOUT_AGENT_SYSTEM_PROMPT
    
    TOOLS = [
        ("tools/core/blender_3/layout_mcp.py", "layout_manager")
    ]
    
    MCP_SERVER_NAME = "layout_agent"
    
    TOOL_DESCRIPTION = """Provides comprehensive space planning and layout design for Blender scenes.
    
    This tool focuses on spatial analysis, layout planning, and design validation:
    - Analyzes scene space and constraints
    - Generates room-specific layout plans
    - Validates spatial relationships and ergonomics
    - Creates visual layout guides
    - Outputs detailed placement instructions for asset_agent
    
    Key Features:
        - Room type templates (bedroom, living_room, office, etc.)
        - Human ergonomics validation
        - Collision and constraint checking
        - Visual guide creation
        - Standardized output format for agent collaboration
        
    Requirements:
        - Blender must be running with the MCP addon enabled
        - Compatible with asset_agent for complete workflow
        
    Examples:
        - "Analyze the current scene space"
        - "Generate a bedroom layout plan"
        - "Validate this layout for spatial conflicts"
        - "Create visual guides for the layout"
    """
    
    @classmethod
    def create_config(cls):
        """Custom configuration for Layout agent"""
        from FractFlow.infra.config import ConfigManager
        from dotenv import load_dotenv
        
        load_dotenv()
        return ConfigManager(
            provider='deepseek',
            deepseek_model='deepseek-chat',
            max_iterations=15,  # Layout planning might need more iterations
            custom_system_prompt=cls.SYSTEM_PROMPT,
            tool_calling_version='stable'
        )

if __name__ == "__main__":
    LayoutAgent.main() 