"""
Agent Launcher - 统一Agent HTTP服务器
支持将多个agent聚合到同一个HTTP端口上运行

Usage:
python agent_launcher.py --port 8000  # 运行所有agent在端口8000
python agent_launcher.py --port 8000 --agents weather,visual_article  # 只运行指定agent
"""

import os
import sys
import asyncio
import argparse
import importlib.util
import traceback
import socket
from pathlib import Path
from typing import List, Dict, Type
from fastapi import FastAPI, Body
from contextlib import asynccontextmanager
import uvicorn
import contextlib

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from FractFlow.tool_template import ToolTemplate


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


def get_display_ip(bind_host: str) -> str:
    """根据绑定的host获取用于显示的IP地址"""
    if bind_host == "0.0.0.0":
        return get_local_ip()
    return bind_host


class AgentLauncher:
    """Agent聚合启动器 - 符合MCP官方规范"""
    
    def __init__(self):
        self.agents: Dict[str, Type[ToolTemplate]] = {}
        self.mcp_servers: Dict[str, any] = {}  # 存储已创建的MCP服务器
        self.tools_dirs = [
            project_root / "tools" / "core",
            project_root / "tools" / "composite"
        ]
    
    def scan_agents(self) -> List[str]:
        """扫描并发现所有agent文件"""
        agent_files = []
        
        for tools_dir in self.tools_dirs:
            if tools_dir.exists():
                # 递归查找所有*_agent.py文件
                for agent_file in tools_dir.rglob("*_agent.py"):
                    agent_files.append(str(agent_file))
        
        return agent_files
    
    def load_agent(self, agent_file: str) -> Type[ToolTemplate]:
        """动态加载agent类"""
        agent_path = Path(agent_file)
        module_name = agent_path.stem
        
        try:
            # 动态导入模块
            spec = importlib.util.spec_from_file_location(module_name, agent_file)
            if spec is None:
                raise ImportError(f"Could not create spec for {agent_file}")
            
            module = importlib.util.module_from_spec(spec)
            if spec.loader is None:
                raise ImportError(f"Could not get loader for {agent_file}")
            
            # 执行模块并注册到sys.modules
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            
            # 查找ToolTemplate的子类
            found_classes = []
            for attr_name in dir(module):
                try:
                    attr = getattr(module, attr_name)
                    if (isinstance(attr, type) and 
                        hasattr(attr, '__bases__') and
                        any(base.__name__ == 'ToolTemplate' for base in attr.__mro__) and
                        attr.__name__ != 'ToolTemplate'):
                        found_classes.append((attr_name, attr))
                except Exception as e:
                    # 跳过获取属性时的错误
                    continue
            
            if found_classes:
                # 返回第一个找到的ToolTemplate子类
                class_name, agent_class = found_classes[0]
                return agent_class
            
            # 如果没有找到，列出模块中的所有类
            all_classes = []
            for attr_name in dir(module):
                try:
                    attr = getattr(module, attr_name)
                    if isinstance(attr, type):
                        all_classes.append(attr_name)
                except:
                    continue
            
            raise ValueError(f"No ToolTemplate subclass found in {agent_file}. "
                           f"Available classes: {all_classes}")
            
        except Exception as e:
            raise Exception(f"Failed to load {agent_file}: {str(e)}")
    
    def register_agents(self, agent_filter: List[str] = None):
        """注册所有或指定的agent"""
        agent_files = self.scan_agents()
        
        for agent_file in agent_files:
            try:
                # 确保项目根目录在Python路径中
                if str(project_root) not in sys.path:
                    sys.path.insert(0, str(project_root))
                
                agent_class = self.load_agent(agent_file)
                agent_name = agent_class.__name__.lower()
                
                # 过滤指定的agent（支持部分匹配）
                if agent_filter:
                    # 检查是否有任何过滤器项匹配当前agent
                    matches = any(filter_item.lower() in agent_name or 
                                agent_name in filter_item.lower() or
                                filter_item.lower() in agent_class.__name__.lower()
                                for filter_item in agent_filter)
                    if not matches:
                        continue
                
                # 验证agent配置
                agent_class._validate_configuration()
                self.agents[agent_name] = agent_class
                
                # 创建MCP服务器并存储（但不获取session_manager，那会在lifespan中处理）
                mcp_server = agent_class._create_fastmcp_server()
                self.mcp_servers[agent_name] = mcp_server
                
                print(f"✓ Registered agent: {agent_name}")
                
            except Exception as e:
                print(f"✗ Failed to load {agent_file}: {e}")
                # 添加更详细的调试信息
                print(f"   Full traceback: {traceback.format_exc()}")
    
    @asynccontextmanager
    async def lifespan(self, app: FastAPI):
        """管理FastAPI应用生命周期 - 符合MCP官方规范"""
        print(f"Starting {len(self.agents)} agents with session managers...")
        
        # 启动所有agent的session managers
        async with contextlib.AsyncExitStack() as stack:
            for agent_name, mcp_server in self.mcp_servers.items():
                try:
                    # 进入session manager上下文
                    await stack.enter_async_context(mcp_server.session_manager.run())
                    print(f"✓ Started session manager for {agent_name}")
                except Exception as e:
                    print(f"✗ Failed to start session manager for {agent_name}: {e}")
            
            # 应用启动完成
            print("🚀 All agent session managers started successfully")
            yield
            
            # 退出时AsyncExitStack会自动清理所有session managers
            print("🔄 Shutting down all agent session managers...")
    
    def create_app(self) -> FastAPI:
        """创建聚合的FastAPI应用 - 符合MCP官方规范"""
        app = FastAPI(
            title="FractFlow Multi-Agent Server",
            description=f"Aggregated server hosting {len(self.agents)} agents",
            version="1.0.0",
            lifespan=self.lifespan
        )
        
        # 挂载每个agent的MCP服务器到对应路径
        for agent_name, mcp_server in self.mcp_servers.items():
            mount_path = f"/{agent_name}"
            app.mount(mount_path, mcp_server.streamable_http_app())
            print(f"✓ Mounted {agent_name} at {mount_path}/mcp")
        
        # 为每个agent创建对应的FastAPI路由，以便在主应用的OpenAPI文档中显示
        for agent_name, agent_class in self.agents.items():
            self._create_agent_route(app, agent_name, agent_class)
        
        # 添加根路径端点
        @app.get("/")
        async def root():
            return {
                "message": "FractFlow Multi-Agent Server",
                "agents": list(self.agents.keys()),
                "endpoints": [f"/{name}/mcp" for name in self.agents.keys()],
                "api_docs": f"Visit /docs for complete API documentation including all {len(self.agents)} agents"
            }
        
        # 添加健康检查端点
        @app.get("/health")
        async def health():
            return {
                "status": "healthy",
                "agents_count": len(self.agents),
                "agents": list(self.agents.keys())
            }
        
        return app
    
    def _create_agent_route(self, app: FastAPI, agent_name: str, agent_class: Type[ToolTemplate]):
        """为agent创建FastAPI路由以在主应用文档中显示"""
        
        # 获取agent的工具描述
        tool_description = agent_class._get_tool_description()
        
        # 创建路由函数
        async def agent_query(query: str = Body(..., description="Query for the agent")):
            """Execute query using the agent"""
            try:
                # 调用agent的MCP工具函数
                result = await agent_class._mcp_tool_function(query)
                return {
                    "agent": agent_name,
                    "query": query,
                    "result": result,
                    "status": "success"
                }
            except Exception as e:
                return {
                    "agent": agent_name,
                    "query": query,
                    "error": str(e),
                    "status": "error"
                }
        
        # 设置路由函数的文档字符串
        agent_query.__doc__ = f"{agent_class.__name__} - {tool_description}"
        
        # 添加路由到应用
        app.add_api_route(
            f"/api/agents/{agent_name}",
            agent_query,
            methods=["POST"],
            summary=f"{agent_class.__name__} Query",
            description=tool_description,
            tags=[f"{agent_class.__name__}"]
        )


def main():
    """主程序入口"""
    parser = argparse.ArgumentParser(description="FractFlow Multi-Agent HTTP Server")
    parser.add_argument("--port", type=int, default=8008, help="HTTP server port (default: 8000)")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind to (default: 0.0.0.0)")
    parser.add_argument("--agents", type=str, help="Comma-separated list of agent names to load (default: all)")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload for development")
    
    args = parser.parse_args()
    
    # 解析agent过滤器
    agent_filter = None
    if args.agents:
        agent_filter = [name.strip() for name in args.agents.split(",")]
    
    # 创建启动器并注册agents
    launcher = AgentLauncher()
    launcher.register_agents(agent_filter)
    
    if not launcher.agents:
        print("❌ No agents found or loaded. Please check your agent files.")
        return
    
    # 创建FastAPI应用
    app = launcher.create_app()
    
    # 显示启动信息
    display_ip = get_display_ip(args.host)
    print(f"\n🚀 Starting FractFlow Multi-Agent Server")
    print(f"📍 Server URL: http://{display_ip}:{args.port}")
    print(f"📖 API Documentation: http://{display_ip}:{args.port}/docs")
    print(f"🔍 Health Check: http://{display_ip}:{args.port}/health")
    print(f"\n📋 Agent Endpoints:")
    for agent_name in launcher.agents.keys():
        print(f"   • {agent_name}: http://{display_ip}:{args.port}/{agent_name}/mcp")
    print()
    
    # 启动服务器
    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="info"
    )


if __name__ == "__main__":
    main()