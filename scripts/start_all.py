#!/usr/bin/env python3
"""
FractFlow 统一启动脚本
自动启动前端、后端和Agent Launcher服务
"""

import subprocess
import signal
import os
import time
import sys
import socket
from pathlib import Path

# 获取项目根目录
PROJECT_ROOT = Path(__file__).parent.parent


def get_local_ip() -> str:
    """获取本机IP地址（连接到外部网络时使用的IP）"""
    try:
        # 创建一个socket连接到外部地址来获取本机IP
        # 使用Google DNS服务器地址，不会实际发送数据
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            return local_ip
    except Exception:
        # 如果获取失败，返回localhost
        return "127.0.0.1"

class ServiceManager:
    def __init__(self):
        self.processes = []
        self.services = [
            {
                'name': 'Frontend (React + Vite)',
                'command': ['npm', 'run', 'dev'],
                'cwd': PROJECT_ROOT / 'web_ui' / 'frontend',
                'url': 'http://localhost:50003'
            },
            {
                'name': 'Backend (FastAPI)',
                'command': ['python', 'run.py'],
                'cwd': PROJECT_ROOT / 'web_ui' / 'backend',
                'url': 'http://localhost:50008'
            },
            {
                'name': 'Agent Launcher',
                'command': ['python', str(PROJECT_ROOT / 'tools' / 'agent_launcher.py'), '--port', '50018'],
                'cwd': PROJECT_ROOT,
                'url': 'http://localhost:50018'
            }
        ]
    
    def start_service(self, service):
        """启动单个服务"""
        try:
            print(f"🚀 Starting {service['name']}...")
            
            # 启动进程
            process = subprocess.Popen(
                service['command'],
                cwd=service['cwd'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            self.processes.append({
                'process': process,
                'service': service
            })
            
            # 显示本机和局域网地址
            local_ip = get_local_ip()
            lan_url = service['url'].replace('localhost', local_ip)
            
            print(f"✓ {service['name']} started (PID: {process.pid})")
            print(f"  📍 本机: {service['url']}")
            print(f"  🌐 局域网: {lan_url}")
            
            return True
            
        except Exception as e:
            print(f"✗ Failed to start {service['name']}: {e}")
            return False
    
    def start_all(self):
        """启动所有服务"""
        print("=" * 60)
        print("🌟 FractFlow 统一服务启动器")
        print("=" * 60)
        
        success_count = 0
        for service in self.services:
            if self.start_service(service):
                success_count += 1
            time.sleep(1)  # 短暂延迟避免端口冲突
        
        if success_count == len(self.services):
            # 获取本机局域网IP
            local_ip = get_local_ip()
            
            print("\n" + "=" * 60)
            print("🎉 所有服务启动成功!")
            print("📋 服务地址:")
            print(f"   🎨 前端界面: http://{local_ip}:50003")
            print(f"   🔧 后端API: http://{local_ip}:50008")
            print(f"   🤖 Agent服务: http://{local_ip}:50018")
            print(f"   📖 完整API文档: http://{local_ip}:50018/docs")
            
            # 显示远程tool使用教程
            self._show_remote_tool_tutorial()
            
            print("\n💡 按 Ctrl+C 停止所有服务")
            print("=" * 60)
            return True
        else:
            print(f"\n⚠️  只有 {success_count}/{len(self.services)} 个服务启动成功")
            return False
    
    def stop_all(self):
        """停止所有服务"""
        print("\n🔄 正在停止所有服务...")
        
        for proc_info in self.processes:
            try:
                process = proc_info['process']
                service = proc_info['service']
                
                if process.poll() is None:  # 进程仍在运行
                    print(f"🛑 Stopping {service['name']} (PID: {process.pid})")
                    process.terminate()
                    
                    # 等待进程优雅关闭
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        print(f"⚡ Force killing {service['name']}")
                        process.kill()
            except Exception as e:
                print(f"⚠️  Error stopping service: {e}")
        
        print("✓ 所有服务已停止")
    
    def _show_remote_tool_tutorial(self):
        """显示完整使用教程"""
        # 获取本机局域网IP
        local_ip = get_local_ip()
        
        print("\n" + "=" * 60)
        print("📖 FractFlow 使用教程")
        print("=" * 60)
        
        # 前端使用教程
        print("🎨 前端Web界面:")
        print(f"   • 本机访问: http://localhost:50003")
        print(f"   • 局域网访问: http://{local_ip}:50003")
        print("   • 功能: 可视化Agent管理和交互终端")
        print()
        
        # 后端API教程
        print("🔧 后端API服务:")
        print(f"   • API地址: http://{local_ip}:50008")
        print(f"   • 文档地址: http://{local_ip}:50008/docs")
        print("   • Agent扫描: GET /api/agents")
        print()
        
        # Agent API教程
        print("🤖 Agent API服务:")
        print(f"   • 完整API文档: http://{local_ip}:50018/docs")
        print(f"   • Agent查询: POST /api/agents/{{agent_name}}")
        print("   • 示例: POST /api/agents/weatheragent")
        print("   • 请求体: {\"query\": \"Weather in New York\"}")
        print()
        
        # Tool使用教程
        print("🤖 Agent Tool远程调用:")
        print("💡 方法1: 使用REST API (推荐)")
        print("```python")
        print("import requests")
        print()
        print("# 直接调用agent")
        print("response = requests.post(")
        print(f"    'http://{local_ip}:50018/api/agents/weatheragent',")
        print("    json={'query': 'Weather in New York'}")
        print(")")
        print("result = response.json()")
        print("```")
        print()
        print("💡 方法2: 使用MCP HTTP Client")
        print("```python")
        print("from FractFlow.mcpcore.client_pool import MCPClientPool")
        print()
        print("# 配置远程tools")
        print("TOOLS = [")
        print(f"    (\"http://{local_ip}:50018/{{agent_name}}/mcp\", \"tool_alias\"),")
        print("    # 示例:")
        print(f"    (\"http://{local_ip}:50018/weatheragent/mcp\", \"weather\"),")
        print(f"    (\"http://{local_ip}:50018/fileioagent/mcp\", \"fileio\"),")
        print("]")
        print()
        print("# 创建客户端池并使用")
        print("client_pool = MCPClientPool()")
        print("await client_pool.setup(TOOLS)")
        print("result = await client_pool.call_tool('weather', 'get_weather', {'city': 'Beijing'})")
        print("```")
        print()
        print("🌐 方法3: 其他机器访问 (跨网段)")
        print("```python")
        print("# REST API跨网段访问")
        print("import requests")
        print("response = requests.post(")
        print("    'http://192.168.1.100:50018/api/agents/weatheragent',")
        print("    json={'query': 'Weather in New York'}")
        print(")")
        print()
        print("# 或使用MCP客户端")
        print("TOOLS = [")
        print("    (\"http://192.168.1.100:50018/weatheragent/mcp\", \"weather\"),")
        print("    (\"http://10.0.0.50:50018/fileioagent/mcp\", \"fileio\"),")
        print("]")
        print("```")
        print()
        print("📋 服务端点总览:")
        print(f"   🎨 前端界面: http://{local_ip}:50003")
        print(f"   🔧 后端API: http://{local_ip}:50008")
        print(f"   🤖 Agent服务: http://{local_ip}:50018")
        print(f"   📖 后端API文档: http://{local_ip}:50008/docs")
        print(f"   📖 Agent API文档: http://{local_ip}:50018/docs")
        print(f"   🏥 健康检查: http://{local_ip}:50018/health")
        print(f"   📂 Agent列表: http://{local_ip}:50018/")
        print("=" * 60)

    def wait_for_interrupt(self):
        """等待用户中断"""
        try:
            while True:
                # 检查所有进程是否还在运行
                running_count = 0
                for proc_info in self.processes:
                    if proc_info['process'].poll() is None:
                        running_count += 1
                
                if running_count == 0:
                    print("\n⚠️  所有服务都已停止")
                    break
                
                time.sleep(1)
                
        except KeyboardInterrupt:
            pass

def signal_handler(signum, frame):
    """信号处理器"""
    print("\n📥 收到停止信号...")
    sys.exit(0)

def main():
    """主函数"""
    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    
    # 创建服务管理器
    manager = ServiceManager()
    
    try:
        # 启动所有服务
        if manager.start_all():
            # 等待中断
            manager.wait_for_interrupt()
    finally:
        # 确保清理所有进程
        manager.stop_all()

if __name__ == "__main__":
    main() 