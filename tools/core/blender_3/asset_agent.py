"""
Asset Agent - Asset Management and Validation

This module provides a unified interface for Blender asset management that focuses on:
1. Asset source management and status checking
2. Intelligent asset search across multiple sources
3. Asset acquisition from PolyHaven, Sketchfab, and Hyper3D
4. Precise asset placement and comprehensive validation

Usage:
  python asset_agent.py                        # MCP Server mode (default)
  python asset_agent.py --interactive          # Interactive mode
  python asset_agent.py --query "..."          # Single query mode
"""

import os
import sys

# Add the project root directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../../..'))
sys.path.append(project_root)

# Import the FractFlow ToolTemplate
from FractFlow.tool_template import ToolTemplate

ASSET_AGENT_SYSTEM_PROMPT = """
你是一个专业的3D资产管理Agent，专门负责在Blender场景中搜索、下载和放置3D资产。

## 核心能力

### 资产搜索与下载
- `search_asset()`: 在多个资产源中搜索指定类型的资产
- `download_asset()`: 从指定源下载资产，自动合并、重命名和缩放到目标尺寸
- **重要**：不需要严格匹配引导线尺寸！任何合适的资产都可以通过缩放调整到完美尺寸

### 精确变换控制
- `scale_object()`: 缩放对象到绝对尺寸（米）
- `move_object()`: 移动对象到精确位置
- `rotate_object()`: 旋转对象到指定角度
- **策略**：先下载合适的资产，然后通过这些工具进行精确调整

### 引导线系统
- `get_guide_info()`: 获取引导线的位置、尺寸和旋转信息
- `find_empty_guide_positions()`: 查找空闲的引导线位置
- 引导线提供目标位置和建议尺寸，但不是严格限制

### 资产管理
- `place_asset()`: 将已存在的资产放置到引导线位置
- `get_asset_info()`: 获取资产的详细信息
- `fix_asset_ground()`: 修复资产的地面接触问题

### 状态检查工具
- `check_asset_sources_status()`: 检查资产源状态
- `search_polyhaven_assets()`: 搜索PolyHaven高质量资产
- `search_sketchfab_models()`: 搜索Sketchfab模型库
- `get_polyhaven_status()`, `get_sketchfab_status()`, `get_hyper3d_status()`: 检查各个资产源状态
- `debug_scene_objects()`: **调试工具** - 检查当前场景中的所有对象，用于排查问题

## 工作流程建议

### 标准下载流程
1. **搜索资产**：使用`search_asset()`找到合适的资产（不必完美匹配尺寸）
2. **获取引导线信息**：使用`get_guide_info()`了解目标位置和尺寸
3. **下载并自动处理**：使用`download_asset()`，系统会自动：
   - 下载资产
   - 合并多个部件（如果有）
   - 重命名为目标名称
   - 缩放到引导线建议尺寸
4. **精确调整**：使用`move_object()`移动到精确位置
5. **可选微调**：如需要，使用`scale_object()`或`rotate_object()`进行微调

### 灵活的尺寸策略
- **不要被引导线尺寸限制**：任何风格合适的资产都可以考虑
- **优先考虑风格和质量**：现代、简约、高质量的资产更重要
- **相信缩放能力**：系统可以将任何尺寸的资产调整到完美大小
- **例如**：
  - 引导线要求1.2×0.6×0.75的桌子
  - 可以下载2.0×1.0×0.8的桌子，然后缩放到目标尺寸
  - 可以下载0.8×0.4×0.6的桌子，然后放大到目标尺寸

## 资产源说明

### PolyHaven (推荐)
- 高质量、免费的3D资产
- 主要包含：家具、装饰品、建筑元素
- 优点：质量高、纹理精美、优化良好
- 当前状态：已启用

### Sketchfab
- 大型3D模型社区
- 包含各种风格的资产
- 需要API密钥才能使用
- 当前状态：需要配置

### Hyper3D AI生成
- 基于文本提示生成3D模型
- 适合找不到合适资产时使用
- 生成质量较高但需要时间

## 重要提示

1. **优先使用PolyHaven**：质量最可靠
2. **不要过度担心尺寸**：缩放工具非常强大
3. **注重风格匹配**：选择符合场景风格的资产
4. **合理使用调试工具**：遇到问题时使用`debug_scene_objects()`
5. **耐心处理下载**：3D资产下载需要时间，请等待完成

记住：你的目标是帮助用户获得完美的3D场景，不要被技术细节限制创意！
"""

class AssetAgent(ToolTemplate):
    """Blender asset management agent using ToolTemplate"""
    
    SYSTEM_PROMPT = ASSET_AGENT_SYSTEM_PROMPT
    
    TOOLS = [
        ("tools/core/blender_3/asset_mcp.py", "asset_manager")
    ]
    
    MCP_SERVER_NAME = "asset_agent"
    
    TOOL_DESCRIPTION = """Provides comprehensive asset management for Blender scenes with multi-source asset acquisition.
    
    Core Functionality:
    - Multi-source asset search (PolyHaven, Sketchfab, Hyper3D)
    - Intelligent asset download and import
    - Guide-based asset placement using semantic IDs
    - Complete asset lifecycle management
    
    Asset Sources:
        - PolyHaven: High-quality textures, HDRIs, and models
        - Sketchfab: Extensive realistic model library
        - Hyper3D: AI-generated 3D models from text descriptions
        
    Key Features:
        - Smart asset search across multiple platforms
        - Automatic asset download and import
        - Guide-based placement with precise positioning
        - Raw data analysis of 3D positions and dimensions
        - AI-powered asset generation when needed
        
    Requirements:
        - Blender must be running with the MCP addon enabled
        - Layout guides must be present in the scene for placement
        - Internet connection for asset downloads
        
    Examples:
        - "搜索并下载一个双人床模型" (Search and download a double bed model)
        - "从Sketchfab下载椅子模型" (Download chair model from Sketchfab)
        - "生成一个现代沙发" (Generate a modern sofa)
        - "基于引导线放入下载的床" (Place downloaded bed based on guides)
    """
    
    @classmethod
    def create_config(cls):
        """Custom configuration for Asset agent"""
        from FractFlow.infra.config import ConfigManager
        from dotenv import load_dotenv
        
        load_dotenv()
        return ConfigManager(
            provider='deepseek',
            deepseek_model='deepseek-chat',
            max_iterations=20,  # Asset operations might need more iterations
            custom_system_prompt=cls.SYSTEM_PROMPT,
            tool_calling_version='stable'
        )

if __name__ == "__main__":
    AssetAgent.main() 