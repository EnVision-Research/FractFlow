#!/usr/bin/env python3
"""
启动儿童涂鸦美化Web应用
前后端分离版本 - FastAPI + HTML
"""

import subprocess
import sys
import os
from pathlib import Path

def main():
    """启动FastAPI web应用"""
    print("🎨 启动儿童涂鸦美化Web应用 (FastAPI版)")
    print("🌐 前端界面: http://localhost:8000")
    print("📚 API文档: http://localhost:8000/docs")
    print("⏹️  按 Ctrl+C 停止应用")
    print("=" * 50)
    
    # 确保在frontend目录下运行
    frontend_dir = Path(__file__).parent
    os.chdir(frontend_dir)
    
    try:
        # 运行FastAPI应用
        subprocess.run([
            sys.executable, "app.py"
        ])
    except KeyboardInterrupt:
        print("\n👋 应用已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        print("\n💡 故障排除:")
        print("1. 确保已安装依赖: pip install -r requirements.txt")
        print("2. 检查DoodleImageGenerator导入是否正常")
        print("3. 确保API密钥配置正确")

if __name__ == "__main__":
    main() 